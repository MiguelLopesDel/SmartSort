import os
import re
import shutil
import time

import joblib
import pypdf
import pytesseract
from PIL import Image
from transformers import AutoTokenizer, pipeline

from smartsort.utils.logger import logger
from smartsort.utils.power import PowerManager
from smartsort.utils.recommender import HardwareRecommender


class FileProcessor:
    def __init__(self, config):
        self.config = config
        self.ai_config = config.get("ai_classification", {})
        self.power_manager = PowerManager(config)
        self.recommender = HardwareRecommender(config)
        self.destination_base = config.get("destination_base_folder", "data/sorted")
        self.fallback_rules = config.get("fallback_rules", {})

        # Configura cache persistente para evitar redownloads
        os.environ["HF_HOME"] = os.path.abspath("models/hf_cache")
        os.makedirs("models/hf_cache", exist_ok=True)

        self.ml_model = None
        self.zero_shot_classifier = None
        self._current_model_name = None
        self._current_mode = None

        self._load_models()

    def update_config(self, new_config):
        """Atualiza a configuração e recarrega modelos apenas se necessário."""
        old_ai = self.config.get("ai_classification", {})
        new_ai = new_config.get("ai_classification", {})

        old_accel = self.config.get("acceleration", {})
        new_accel = new_config.get("acceleration", {})

        self.config = new_config
        self.ai_config = new_ai
        self.power_manager.config = new_config
        self.destination_base = new_config.get("destination_base_folder", "data/sorted")
        self.fallback_rules = new_config.get("fallback_rules", {})
        # Verifica se algo pesado mudou
        if (old_ai.get("mode") != new_ai.get("mode") or 
            old_ai.get("zero_shot_model") != new_ai.get("zero_shot_model") or
            old_accel != new_accel):
            logger.info("Alteração detectada em configurações de IA/Aceleração. Recarregando modelos...")
            self._load_models()
        else:
            logger.debug("Configuração atualizada (sem necessidade de recarregar modelos de IA).")

    def _load_models(self):
        """Lógica interna de carregamento de modelos com cache local."""
        ai_config = self.config.get("ai_classification", {})
        accel_config = self.config.get("acceleration", {"enabled": False})

        if not ai_config.get("enabled", False):
            self.ml_model = None
            self.zero_shot_classifier = None
            return

        mode = ai_config.get("mode")

        # Resolução Dinâmica de Hardware
        provider = accel_config.get("provider", "auto")
        device = accel_config.get("device", "auto")

        if accel_config.get("enabled") and provider == "auto":
            on_battery = self.power_manager.is_on_battery()
            provider, device = self.recommender.get_best_acceleration(on_battery)
            logger.info(f"[AUTO] Hardware: {provider.upper()} em {device.upper()} (Bateria: {on_battery})")

        if mode == "local_ml":
            model_path = ai_config.get("local_ml_model_path", "models/modelo_classificador.joblib")
            try:
                self.ml_model = joblib.load(model_path)
                logger.info(f"Modelo de IA Local ({model_path}) carregado.")
            except Exception as e:
                logger.warning(f"Não foi possível carregar o modelo de ML: {e}")

        elif mode == "zero_shot":
            model_name = ai_config.get("zero_shot_model", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")

            # Evita recarregar o mesmo modelo se já estiver na memória
            if model_name == self._current_model_name and provider == self._current_mode:
                return

            try:
                if accel_config.get("enabled") and provider == "cuda":
                    logger.info(f"Carregando Zero-Shot para CUDA... ({model_name})")
                    self.zero_shot_classifier = pipeline("zero-shot-classification", model=model_name, device=0)

                elif accel_config.get("enabled") and provider == "openvino":
                    ov_cache_dir = os.path.join("models", "ov_cache", model_name.replace("/", "_"))
                    from optimum.intel.openvino import OVModelForSequenceClassification

                    if os.path.exists(ov_cache_dir):
                        logger.debug(f"Usando Cache OpenVINO: {ov_cache_dir}")
                        model = OVModelForSequenceClassification.from_pretrained(ov_cache_dir, device=device.upper())
                    else:
                        logger.info(f"Exportando {model_name} para OpenVINO (Cache Local)...")
                        os.makedirs(ov_cache_dir, exist_ok=True)
                        model = OVModelForSequenceClassification.from_pretrained(
                            model_name, export=True, device=device.upper(),
                            load_in_8bit=(accel_config.get("quantization") == "int8")
                        )
                        model.save_pretrained(ov_cache_dir)

                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.zero_shot_classifier = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer)
                else:
                    logger.info(f"Carregando Zero-Shot padrão (CPU)... ({model_name})")
                    self.zero_shot_classifier = pipeline("zero-shot-classification", model=model_name)

                self._current_model_name = model_name
                self._current_mode = provider
            except Exception as e:
                logger.exception(f"Falha ao carregar modelo de IA: {e}")

    def sanitize_category(self, category_name):
        if not category_name:
            return "Desconhecido"

        safe_name = re.sub(r"[^\w\s\-_]", "", str(category_name))
        safe_name = safe_name.strip()
        return safe_name if safe_name else "Desconhecido"

    def process_existing_files(self):
        """Varre os diretórios configurados e processa ficheiros já existentes."""
        directories = self.config.get("directories_to_watch", [])
        logger.info(f"A verificar ficheiros existentes em: {directories}")

        for directory in directories:
            if not os.path.exists(directory):
                logger.warning(f"Diretório não encontrado: {directory}")
                continue

            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)

                if os.path.isdir(file_path) or filename.startswith("."):
                    continue

                logger.debug(f"Ficheiro existente encontrado: {filename}")
                self.process_file(file_path)

    def log_history(self, filename, category, dest_path, confidence=None):
        """Regista a ação num ficheiro de histórico para consulta do utilizador."""
        history_file = os.path.join(os.path.dirname(self.destination_base), "history.log")
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        conf_info = f" [Confiança: {confidence:.2f}]" if confidence is not None else ""

        log_entry = f"[{timestamp}] {filename} -> {category}{conf_info} | Local: {dest_path}\n"

        try:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Erro ao gravar no histórico: {e}")

    def process_file(self, file_path):
        if not os.path.exists(file_path):
            return


        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if os.path.abspath(file_path).startswith(project_root):
            return

        filename = os.path.basename(file_path)

        ignored_extensions = (
            ".part",
            ".crdownload",
            ".tmp",
            ".kate-swp",
            ".swp",
            ".swx",
        )
        if filename.startswith(".") or filename.endswith(ignored_extensions) or filename.endswith("~"):
            return


        time.sleep(2)
        if not os.path.exists(file_path):
            return

        logger.info(f"A processar: [bold]{filename}[/bold] " f"({'Pasta' if os.path.isdir(file_path) else 'Ficheiro'})")

        try:
            category_raw, confidence = self.classify_file(file_path, filename)
            category = self.sanitize_category(category_raw)

            target_dir = os.path.join(self.destination_base, category)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            destination_path = os.path.join(target_dir, filename)

            if os.path.exists(destination_path):
                base, ext = os.path.splitext(filename)
                destination_path = os.path.join(target_dir, f"{base}_{int(time.time())}{ext}")

            shutil.move(file_path, destination_path)
            logger.info(f"Sucesso: Movido para [green]{destination_path}[/green]")
            self.log_history(filename, category, destination_path, confidence)
        except Exception as e:
            logger.exception(f"Erro crítico ao processar {filename}: {e}")

    def extract_text_from_pdf(self, file_path):
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Erro ao extrair texto do PDF: {e}")
            return ""

    def extract_text_from_image(self, file_path):
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang="por")
            return text.strip()
        except Exception as e:
            if "por" in str(e) or "traineddata" in str(e):
                logger.warning(
                    "Aviso: Tesseract não encontrou o idioma 'por'. "
                    "Por favor, instale 'tesseract-ocr-por' ou 'tesseract-data-por'."
                )
            else:
                logger.error(f"Erro ao extrair texto da imagem: {e}")
            return ""

    def classify_file(self, file_path, filename):
        ext = filename.split(".")[-1].lower() if "." in filename else ""


        if self.power_manager.should_use_fallback():
            logger.info(f"Modo Economia: Saltando IA pesada para [yellow]{filename}[/yellow].")
            return self.fallback_rules.get(ext, "Outros"), None

        extracted_text = ""

        clean_filename = re.sub(r"[._-]", " ", filename.rsplit(".", 1)[0])

        if ext == "pdf":
            logger.debug(f"A extrair texto do PDF {filename}...")
            extracted_text = self.extract_text_from_pdf(file_path)
        elif ext in ["jpg", "jpeg", "png"]:
            logger.debug(f"A extrair texto da imagem {filename} via OCR...")
            extracted_text = self.extract_text_from_image(file_path)
        elif ext in ["txt", "md", "csv"]:
            logger.debug(f"A extrair texto do ficheiro de texto {filename}...")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    extracted_text = f.read()
            except Exception as e:
                logger.error(f"Erro ao ler texto: {e}")


        full_context = f"Ficheiro: {clean_filename}. Conteúdo: {extracted_text[:500]}"

        if self.ai_config.get("enabled", False):
            mode = self.ai_config.get("mode", "api")
            logger.debug(f"Modo IA ativado: Usando ({mode}) para classificar...")

            try:
                if mode == "local":
                    model = self.ai_config.get("local_model", "llama3")
                    logger.debug(f"Simulando inferência com IA Local (Modelo: {model})...")
                    ai_category = self.simulate_ai_classification(filename, extracted_text)
                    return ai_category, None
                elif mode == "local_ml" and self.ml_model:
                    logger.debug("A usar Modelo de ML Local (scikit-learn)...")
                    previsao = self.ml_model.predict([full_context])
                    return previsao[0], None
                elif mode == "zero_shot" and self.zero_shot_classifier:
                    logger.debug("A usar Modelo Zero-Shot HuggingFace...")
                    categorias = self.ai_config.get(
                        "categorias_disponiveis",
                        ["Financas", "Trabalho", "Pessoal", "Saude", "Outros"],
                    )

                    resultado = self.zero_shot_classifier(full_context, categorias)
                    cat = resultado["labels"][0]
                    conf = resultado["scores"][0]
                    logger.info(f"IA classificou como: [magenta]{cat}[/magenta] (Confiança: {conf:.2f})")
                    return cat, conf
                elif mode == "api":
                    provider = self.ai_config.get("api_provider", "gemini")
                    logger.debug(f"Simulando chamada de API Remota (Provider: {provider})...")
                    ai_category = self.simulate_ai_classification(filename, extracted_text)
                    return ai_category, None
                else:
                    logger.warning(f"Modo de IA desconhecido: {mode}. Usando fallback...")
                    ai_category = None
            except Exception as e:
                logger.exception(f"Falha na IA: {e}. A recorrer ao fallback (regras)...")

        return self.fallback_rules.get(ext, "Outros"), None

    def simulate_ai_classification(self, filename, text=""):
        name_lower = filename.lower()
        text_lower = text.lower()

        if "fatura" in name_lower or "recibo" in name_lower or "fatura" in text_lower or "recibo" in text_lower:
            return "Financas"
        elif "relatorio" in name_lower or "cv" in name_lower or "relatório" in text_lower:
            return "Trabalho"
        return "Outros"

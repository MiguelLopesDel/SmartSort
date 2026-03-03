import os
import re
import shutil
import time

import joblib
import pypdf
import pytesseract
from PIL import Image
from transformers import pipeline
from smartsort.utils.power import PowerManager


class FileProcessor:
    def __init__(self, config):
        self.config = config
        self.power_manager = PowerManager(config)
        self.destination_base = config.get("destination_base_folder", "data/sorted")
        self.ai_config = config.get("ai_classification", {})
        self.fallback_rules = config.get("fallback_rules", {})

        self.ml_model = None
        self.zero_shot_classifier = None

        mode = self.ai_config.get("mode")
        if self.ai_config.get("enabled", False):
            if mode == "local_ml":
                model_path = self.ai_config.get(
                    "local_ml_model_path", "models/modelo_classificador.joblib"
                )
                try:
                    self.ml_model = joblib.load(model_path)
                    print(f"Modelo de IA Local ({model_path}) carregado com sucesso!")
                except Exception as e:
                    print(
                        f"Aviso: Não foi possível carregar o modelo de ML ({e}). "
                        "Tens a certeza que executaste o script de treino?"
                    )
            elif mode == "zero_shot":
                model_name = self.ai_config.get(
                    "zero_shot_model", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
                )
                print(
                    f"A carregar o modelo Zero-Shot avançado ({model_name}). "
                    "Isto pode demorar um pouco na primeira vez..."
                )
                try:
                    self.zero_shot_classifier = pipeline(
                        "zero-shot-classification", model=model_name
                    )
                    print("Modelo Zero-Shot carregado com sucesso!")
                except Exception as e:
                    print(f"Aviso: Falha ao carregar modelo Zero-Shot: {e}")

    def sanitize_category(self, category_name):

        if not category_name:
            return "Desconhecido"

        safe_name = re.sub(r"[^\w\s\-_]", "", str(category_name))
        safe_name = safe_name.strip()
        return safe_name if safe_name else "Desconhecido"

    def process_existing_files(self):
        """Varre os diretórios configurados e processa ficheiros já existentes."""
        directories = self.config.get("directories_to_watch", [])
        print(f"\\nA verificar ficheiros existentes em: {directories}")

        for directory in directories:
            if not os.path.exists(directory):
                continue

            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)

                if os.path.isdir(file_path) or filename.startswith("."):
                    continue

                print(f"Ficheiro existente encontrado: {filename}")
                self.process_file(file_path)

    def log_history(self, filename, category, dest_path, confidence=None):
        """Regista a ação num ficheiro de histórico para consulta do utilizador."""
        history_file = os.path.join(
            os.path.dirname(self.destination_base), "history.log"
        )
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        conf_info = f" [Confiança: {confidence:.2f}]" if confidence is not None else ""

        log_entry = (
            f"[{timestamp}] {filename} -> {category}{conf_info} | Local: {dest_path}\n"
        )

        try:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Erro ao gravar no histórico: {e}")

    def process_file(self, file_path):
        if not os.path.exists(file_path):
            return

        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../..")
        )
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
        if (
            filename.startswith(".")
            or filename.endswith(ignored_extensions)
            or filename.endswith("~")
        ):
            return

        time.sleep(2)
        if not os.path.exists(file_path):
            return

        print(
            f"\nA processar: {filename} "
            f"({'Pasta' if os.path.isdir(file_path) else 'Ficheiro'})"
        )

        category_raw, confidence = self.classify_file(file_path, filename)
        category = self.sanitize_category(category_raw)

        target_dir = os.path.join(self.destination_base, category)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        destination_path = os.path.join(target_dir, filename)

        try:
            if os.path.exists(destination_path):
                base, ext = os.path.splitext(filename)
                destination_path = os.path.join(
                    target_dir, f"{base}_{int(time.time())}{ext}"
                )

            shutil.move(file_path, destination_path)
            print(f"Sucesso: Movido para {destination_path}")
            self.log_history(filename, category, destination_path, confidence)
        except Exception as e:
            print(f"Erro ao mover {filename}: {e}")

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
            print(f"Erro ao extrair texto do PDF: {e}")
            return ""

    def extract_text_from_image(self, file_path):
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang="por")
            return text.strip()
        except Exception as e:
            if "por" in str(e) or "traineddata" in str(e):
                print(
                    "Aviso: Tesseract não encontrou o idioma 'por'. "
                    "Por favor, instale 'tesseract-ocr-por' ou 'tesseract-data-por'."
                )
            else:
                print(f"Erro ao extrair texto da imagem: {e}")
            return ""

    def classify_file(self, file_path, filename):
        ext = filename.split(".")[-1].lower() if "." in filename else ""

        # Verificação de Economia de Energia (Bateria)
        if self.power_manager.should_use_fallback():
            print(f"Modo Economia: Saltando IA pesada para {filename}.")
            return self.fallback_rules.get(ext, "Outros")

        extracted_text = ""
        if ext == "pdf":
            print(f"A extrair texto do PDF {filename}...")
            extracted_text = self.extract_text_from_pdf(file_path)
            if extracted_text:
                print(f"Texto extraído: {extracted_text[:100]}...")
            else:
                print("Nenhum texto encontrado no PDF (talvez seja uma imagem).")
        elif ext in ["jpg", "jpeg", "png"]:
            print(f"A extrair texto da imagem {filename} via OCR...")
            extracted_text = self.extract_text_from_image(file_path)
            if extracted_text:
                print(f"Texto extraído: {extracted_text[:100]}...")
            else:
                print("Nenhum texto encontrado na imagem.")
        elif ext in ["txt", "md", "csv"]:
            print(f"A extrair texto do ficheiro de texto {filename}...")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    extracted_text = f.read()
                    print(f"Texto extraído: {extracted_text[:100]}...")
            except Exception as e:
                print(f"Erro ao ler texto: {e}")

        if self.ai_config.get("enabled", False):
            mode = self.ai_config.get("mode", "api")
            print(f"Modo IA ativado: Usando ({mode}) para classificar...")

            try:
                if mode == "local":
                    model = self.ai_config.get("local_model", "llama3")
                    print(f"-> Simulando inferência com IA Local (Modelo: {model})...")
                    ai_category = self.simulate_ai_classification(
                        filename, extracted_text
                    )
                    return ai_category, None
                elif mode == "local_ml" and self.ml_model:
                    print("-> A usar Modelo de ML Local (scikit-learn)...")
                    texto_completo = f"{filename} {extracted_text}"
                    previsao = self.ml_model.predict([texto_completo])
                    return previsao[0], None
                elif mode == "zero_shot" and self.zero_shot_classifier:
                    print("-> A usar Modelo Zero-Shot HuggingFace...")
                    texto_completo = f"Ficheiro: {filename}. Conteúdo: {extracted_text}"
                    categorias = self.ai_config.get(
                        "categorias_disponiveis",
                        ["Financas", "Trabalho", "Pessoal", "Saude", "Outros"],
                    )
                    texto_analise = texto_completo if extracted_text else filename
                    resultado = self.zero_shot_classifier(texto_analise, categorias)
                    ai_category = resultado["labels"][0]
                    confianca = resultado["scores"][0]
                    print(
                        f"IA classificou como: {ai_category} (Confiança: {confianca:.2f})"
                    )
                    return ai_category, confianca
                elif mode == "api":
                    provider = self.ai_config.get("api_provider", "gemini")
                    print(
                        f"-> Simulando chamada de API Remota (Provider: {provider})..."
                    )
                    ai_category = self.simulate_ai_classification(
                        filename, extracted_text
                    )
                    return ai_category, None
                else:
                    print("-> Modo de IA desconhecido, usando fallback...")
                    ai_category = None
            except Exception as e:
                print(f"Falha na IA: {e}. A recorrer ao fallback (regras)...")

        return self.fallback_rules.get(ext, "Outros"), None

    def simulate_ai_classification(self, filename, text=""):

        name_lower = filename.lower()
        text_lower = text.lower()

        if (
            "fatura" in name_lower
            or "recibo" in name_lower
            or "fatura" in text_lower
            or "recibo" in text_lower
        ):
            return "Financas"
        elif (
            "relatorio" in name_lower or "cv" in name_lower or "relatório" in text_lower
        ):
            return "Trabalho"
        return None

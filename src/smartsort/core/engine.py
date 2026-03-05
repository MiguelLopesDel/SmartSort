import gc
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import joblib
import pypdf
import pytesseract
from PIL import Image
from transformers import AutoTokenizer, pipeline

from smartsort.utils.logger import logger
from smartsort.utils.power import PowerManager
from smartsort.utils.recommender import HardwareRecommender


class FileProcessor:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.project_root = Path(__file__).resolve().parent.parent.parent.parent

        self.ai_config = config.get("ai_classification", {})
        self.power_manager = PowerManager(config)
        self.recommender = HardwareRecommender(config)

        dest_base = config.get("destination_base_folder", "data/sorted")
        self.destination_base = Path(dest_base)
        if not self.destination_base.is_absolute():
            self.destination_base = self.project_root / dest_base

        self.fallback_rules = config.get("fallback_rules", {})

        hf_cache = self.project_root / "models" / "hf_cache"
        os.environ["HF_HOME"] = str(hf_cache)
        hf_cache.mkdir(parents=True, exist_ok=True)

        self.ml_model: Optional[Any] = None
        self.zero_shot_classifier: Optional[Any] = None
        self.whisper_model: Optional[Any] = None
        self._current_audio_model: Optional[str] = None
        self._current_model_name: Optional[str] = None
        self._current_mode: Optional[str] = None
        self._last_battery_state: Optional[bool] = None
        self._last_provider: Optional[str] = None

        self._load_models()
        self._load_audio_model()

    def update_config(self, new_config: Dict[str, Any]) -> None:
        old_ai = self.config.get("ai_classification", {})
        new_ai = new_config.get("ai_classification", {})
        old_accel = self.config.get("acceleration", {})
        new_accel = new_config.get("acceleration", {})

        self.config = new_config
        self.ai_config = new_ai
        self.power_manager.config = new_config
        self.destination_base = Path(new_config.get("destination_base_folder", "data/sorted"))
        self.fallback_rules = new_config.get("fallback_rules", {})

        if (
            old_ai.get("mode") != new_ai.get("mode")
            or old_ai.get("zero_shot_model") != new_ai.get("zero_shot_model")
            or old_accel != new_accel
        ):
            logger.info("Alteração em IA/Aceleração. Recarregando modelos...")
            self._load_models()
            self._load_audio_model()

    def _unload_model(self, model_attr: str) -> None:
        if hasattr(self, model_attr) and getattr(self, model_attr) is not None:
            setattr(self, model_attr, None)
            gc.collect()

    def _load_audio_model(self) -> None:
        audio_cfg = self.config.get("audio_classification", {"enabled": False})
        if not audio_cfg.get("enabled"):
            self._unload_model("whisper_model")
            return

        on_battery = self.power_manager.is_on_battery()
        profile = audio_cfg.get("battery_mode" if on_battery else "ac_mode", {})

        if not profile.get("enabled"):
            self._unload_model("whisper_model")
            return

        model_name = profile.get("model", "tiny")
        device = "cuda" if profile.get("use_gpu") and self.recommender._check_nvidia_gpu() else "cpu"

        if self._current_audio_model == f"{model_name}_{device}":
            return

        try:
            import whisper

            self._unload_model("whisper_model")
            logger.info(f"Carregando Whisper ({model_name}) em {device.upper()}...")
            self.whisper_model = whisper.load_model(model_name, device=device)
            self._current_audio_model = f"{model_name}_{device}"
        except Exception as e:
            logger.error(f"Erro ao carregar Whisper: {e}")
            self.whisper_model = None

    def _load_models(self) -> None:
        ai_config = self.config.get("ai_classification", {})
        accel_config = self.config.get("acceleration", {"enabled": False})

        if not ai_config.get("enabled", False):
            self._unload_model("ml_model")
            self._unload_model("zero_shot_classifier")
            return

        mode = ai_config.get("mode")
        provider, device = self._resolve_accel_settings(accel_config)

        if mode == "local_ml":
            self._load_local_ml_model(ai_config)
        elif mode == "zero_shot":
            self._load_zero_shot_model(ai_config, accel_config, provider, device)

    def _resolve_accel_settings(self, accel_config: Dict[str, Any]) -> Tuple[str, str]:
        provider = accel_config.get("provider", "auto")
        device = accel_config.get("device", "auto")

        if accel_config.get("enabled") and provider == "auto":
            on_battery = self.power_manager.is_on_battery()
            provider, device = self.recommender.get_best_acceleration(on_battery)
            self._last_battery_state = on_battery
            self._last_provider = provider
        return provider, device

    def _load_local_ml_model(self, ai_config: Dict[str, Any]) -> None:
        self._unload_model("zero_shot_classifier")
        path_rel = ai_config.get("local_ml_model_path", "models/modelo_classificador.joblib")
        model_path = self.project_root / path_rel
        try:
            self.ml_model = joblib.load(str(model_path))
            logger.info(f"Modelo Local ({model_path.name}) carregado.")
        except Exception as e:
            logger.warning(f"Erro ao carregar ML: {e}")

    def _load_zero_shot_model(self, ai_config: Dict[str, Any], accel_config: Dict[str, Any], p: str, d: str) -> None:
        self._unload_model("ml_model")
        name = ai_config.get("zero_shot_model", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        if name == self._current_model_name and p == self._current_mode:
            return

        try:
            self._unload_model("zero_shot_classifier")
            if accel_config.get("enabled") and p == "cuda":
                logger.info(f"Carregando Zero-Shot para CUDA... ({name})")
                self.zero_shot_classifier = pipeline("zero-shot-classification", model=name, device=0)
            elif accel_config.get("enabled") and p == "openvino":
                model, tokenizer = self._setup_openvino_model(name, d, accel_config)
                self.zero_shot_classifier = pipeline("zero-shot-classification", model=model, tokenizer=tokenizer)
            else:
                self.zero_shot_classifier = pipeline("zero-shot-classification", model=name)

            self._current_model_name = name
            self._current_mode = p
        except Exception as e:
            logger.exception(f"Erro ao carregar IA: {e}")

    def _setup_openvino_model(self, name: str, d: str, cfg: Dict[str, Any]) -> Tuple[Any, Any]:
        ov_cache_dir = self.project_root / "models" / "ov_cache" / name.replace("/", "_")
        from optimum.intel.openvino import OVModelForSequenceClassification

        if ov_cache_dir.exists():
            model = OVModelForSequenceClassification.from_pretrained(str(ov_cache_dir), device=d.upper())
        else:
            ov_cache_dir.mkdir(parents=True, exist_ok=True)
            model = OVModelForSequenceClassification.from_pretrained(
                name,
                export=True,
                device=d.upper(),
                load_in_8bit=(cfg.get("quantization") == "int8"),
            )
            model.save_pretrained(str(ov_cache_dir))
        return model, AutoTokenizer.from_pretrained(name)

    def sanitize_category(self, category_name: Any) -> str:
        if not category_name:
            return "Desconhecido"
        name = str(category_name).strip()
        name = re.sub(r"[^\w\s\-_]", "", name)
        name = name.replace("..", "").replace("/", "").replace("\\", "")
        return name if name else "Desconhecido"

    def process_file(self, file_path_str: str) -> None:
        file_path = Path(file_path_str).resolve()
        if not file_path.exists() or file_path.is_dir():
            return

        if any(parent == self.project_root for parent in file_path.parents) or file_path == self.project_root:
            return

        filename = file_path.name
        if filename.startswith(".") or filename.endswith((".part", ".crdownload", ".tmp", "~")):
            return

        time.sleep(1)
        try:
            category_raw, confidence = self.classify_file(str(file_path), filename)
            category = self.sanitize_category(category_raw)

            target_dir = self.destination_base / category
            target_dir.mkdir(parents=True, exist_ok=True)

            dest_path = target_dir / filename
            if dest_path.exists():
                timestamp = int(time.time() * 1000)
                dest_path = target_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"

            shutil.move(str(file_path), str(dest_path))
            logger.info(f"Movido: [bold]{filename}[/bold] -> [green]{category}[/green]")
            self.log_history(filename, category, str(dest_path), confidence)
        except FileNotFoundError:
            logger.warning(f"Arquivo desapareceu durante processamento: {filename}")
        except Exception as e:
            logger.exception(f"Erro ao processar {filename}: {e}")

    def process_existing_files(self) -> None:
        directories = self.config.get("directories_to_watch", [])
        for directory in directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue
            for item in dir_path.iterdir():
                if item.is_file():
                    self.process_file(str(item))

    def log_history(self, filename: str, category: str, dest_path: str, confidence: Optional[float] = None) -> None:
        history_file = self.destination_base.parent / "history.log"
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        conf = f" [{confidence:.2f}]" if confidence is not None else ""
        entry = f"[{ts}] {filename} -> {category}{conf} | {dest_path}\n"
        try:
            with open(history_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            logger.error(f"Erro histórico: {e}")

    def extract_text_from_pdf(self, file_path: str) -> str:
        try:
            with open(file_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                return " ".join(p.extract_text() or "" for p in reader.pages).strip()
        except Exception as e:
            logger.error(f"Erro PDF: {e}")
            return ""

    def extract_text_from_image(self, file_path: str) -> str:
        try:
            return str(pytesseract.image_to_string(Image.open(file_path), lang="por")).strip()
        except Exception as e:
            logger.error(f"Erro OCR: {e}")
            return ""

    def classify_file(self, file_path: str, filename: str) -> Tuple[str, Optional[float]]:
        ext = Path(file_path).suffix.lower().lstrip(".")
        video_exts = ("mp4", "mkv", "avi", "mov", "wmv", "flv", "webm")

        if ext in video_exts and self.whisper_model:
            try:
                res = self.whisper_model.transcribe(file_path)
                return str(res.get("text", "")), 1.0
            except Exception:
                return self.fallback_rules.get(ext, "Videos"), 1.0

        if self.power_manager.should_use_fallback():
            return self.fallback_rules.get(ext, "Outros"), None

        text = self._get_file_text(file_path, ext)
        ctx = f"{filename} {text[:500]}"

        if self.ai_config.get("enabled"):
            return self._run_ai_inference(ctx, ext)

        return str(self.fallback_rules.get(ext, "Outros")), None

    def _get_file_text(self, path: str, ext: str) -> str:
        if ext == "pdf":
            return self.extract_text_from_pdf(path)
        if ext in ("jpg", "jpeg", "png"):
            return self.extract_text_from_image(path)
        if ext in ("txt", "md", "csv"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
        return ""

    def _run_ai_inference(self, ctx: str, ext: str) -> Tuple[str, Optional[float]]:
        mode = self.ai_config.get("mode")
        try:
            if mode == "local_ml" and self.ml_model:
                return str(self.ml_model.predict([ctx])[0]), None
            if mode == "zero_shot" and self.zero_shot_classifier:
                cats = self.ai_config.get("categorias_disponiveis", ["Outros"])
                res = self.zero_shot_classifier(ctx, cats)
                return str(res["labels"][0]), float(res["scores"][0])
        except Exception:
            pass
        return str(self.fallback_rules.get(ext, "Outros")), None

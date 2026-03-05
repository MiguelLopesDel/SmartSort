import time
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from smartsort.core.engine import FileProcessor
from smartsort.utils.logger import logger


class SmartSortHandler(FileSystemEventHandler):
    def __init__(self, processor: FileProcessor) -> None:
        self.processor = processor

    def on_created(self, event: FileSystemEvent) -> None:
        src_path = str(event.src_path)
        if not event.is_directory:
            logger.info(f"Novo ficheiro detetado: [bold cyan]{src_path}[/bold cyan]")
            self.processor.process_file(src_path)
        else:
            logger.info(f"Nova pasta detetada: [bold cyan]{src_path}[/bold cyan]")
            self.processor.process_file(src_path)


DEFAULT_CONFIG: Dict[str, Any] = {
    "directories_to_watch": [],
    "destination_base_folder": "data/sorted",
    "ai_classification": {"enabled": False},
    "power_saving": {"enabled": True, "pause_ai_on_battery": True},
    "fallback_rules": {},
}


def load_config(config_path: Path) -> Optional[Dict[str, Any]]:
    try:
        if not config_path.exists():
            return DEFAULT_CONFIG
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            if cfg is None:
                return DEFAULT_CONFIG
            return dict(cfg)
    except Exception as e:
        logger.error(f"Erro ao carregar o {config_path}: {e}")
        return None


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent.parent
    config_path = project_root / "config" / "config.yaml"
    config = load_config(config_path)

    config_error_mode = False
    if config is None:
        logger.error("Falha na configuração inicial. Entrando em modo de espera.")
        config = DEFAULT_CONFIG
        config_error_mode = True

    processor = FileProcessor(config)

    if not config_error_mode:
        processor.process_existing_files()

    observer = Observer()
    handler = SmartSortHandler(processor)

    def setup_observer(cfg: Dict[str, Any]) -> None:
        observer.unschedule_all()
        directories = cfg.get("directories_to_watch", [])
        for directory in directories:
            dir_path = Path(directory)
            if dir_path.exists():
                observer.schedule(handler, str(dir_path), recursive=False)
                logger.info(f"A monitorizar: [yellow]{dir_path}[/yellow]")
            else:
                logger.warning(f"O diretório [red]{dir_path}[/red] não existe.")

    if not config_error_mode:
        setup_observer(config)

    observer.start()
    logger.info("[bold green]SmartSort em execução. Pressione Ctrl+C para parar.[/bold green]")

    try:
        last_mtime = 0.0
        if config_path.exists():
            last_mtime = config_path.stat().st_mtime

        while True:
            time.sleep(5)
            try:
                if config_path.exists():
                    current_mtime = config_path.stat().st_mtime
                    if current_mtime > last_mtime or config_error_mode:
                        new_config = load_config(config_path)
                        if new_config:
                            logger.info("Configuração atualizada/recuperada!")
                            processor.update_config(new_config)
                            setup_observer(new_config)
                            last_mtime = current_mtime
                            config_error_mode = False
            except Exception:
                if not config_error_mode:
                    logger.error("Arquivo de configuração ainda contém erros.")
                    config_error_mode = True

    except KeyboardInterrupt:
        observer.stop()
        logger.info("A parar SmartSort...")

    observer.join()


if __name__ == "__main__":
    main()

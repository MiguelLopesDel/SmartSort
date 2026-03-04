import os
import time

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from smartsort.core.engine import FileProcessor
from smartsort.utils.logger import logger


class SmartSortHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor

    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"Novo ficheiro detetado: [bold cyan]{event.src_path}[/bold cyan]")
            self.processor.process_file(event.src_path)
        else:
            logger.info(f"Nova pasta detetada: [bold cyan]{event.src_path}[/bold cyan]")
            self.processor.process_file(event.src_path)


DEFAULT_CONFIG = {
    "directories_to_watch": [],
    "destination_base_folder": "data/sorted",
    "ai_classification": {"enabled": False},
    "power_saving": {"enabled": True, "pause_ai_on_battery": True},
    "fallback_rules": {},
}


def load_config(config_path="config/config.yaml"):
    try:
        if not os.path.exists(config_path):
            return DEFAULT_CONFIG
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            return cfg if cfg else DEFAULT_CONFIG
    except Exception as e:
        logger.error(f"Erro ao carregar o {config_path}: {e}")
        return None


def main():

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, "config", "config.yaml")
    config = load_config(config_path)

    config_error_mode = False
    if config is None:
        logger.error("Falha na configuração inicial. Entrando em modo de espera/recuperação.")
        config = DEFAULT_CONFIG
        config_error_mode = True

    processor = FileProcessor(config)

    if not config_error_mode:
        processor.process_existing_files()

    observer = Observer()
    handler = SmartSortHandler(processor)

    def setup_observer(cfg):
        observer.unschedule_all()
        directories = cfg.get("directories_to_watch", [])
        for directory in directories:
            if os.path.exists(directory):
                observer.schedule(handler, directory, recursive=False)
                logger.info(f"A monitorizar: [yellow]{directory}[/yellow]")
            else:
                logger.warning(f"O diretório [red]{directory}[/red] não existe.")

    if not config_error_mode:
        setup_observer(config)

    observer.start()
    logger.info("[bold green]SmartSort em execução. Pressione Ctrl+C para parar.[/bold green]")

    try:
        last_mtime = 0
        if os.path.exists(config_path):
            last_mtime = os.path.getmtime(config_path)

        while True:
            time.sleep(5)
            try:
                if os.path.exists(config_path):
                    current_mtime = os.path.getmtime(config_path)
                    if current_mtime > last_mtime or config_error_mode:
                        new_config = load_config(config_path)
                        if new_config:
                            logger.info("Configuração atualizada/recuperada com sucesso!")
                            processor.update_config(new_config)
                            setup_observer(new_config)
                            last_mtime = current_mtime
                            config_error_mode = False
            except Exception:
                if not config_error_mode:
                    logger.error("Arquivo de configuração ainda contém erros. Mantendo modo de espera.")
                    config_error_mode = True

    except KeyboardInterrupt:
        observer.stop()
        logger.info("A parar SmartSort...")

    observer.join()


if __name__ == "__main__":
    main()

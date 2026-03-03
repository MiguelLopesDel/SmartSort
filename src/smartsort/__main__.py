import os
import sys
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


def load_config(config_path="config/config.yaml"):
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar o config.yaml: {e}")
        return None


def main():
    config_path = "config/config.yaml"
    config = load_config(config_path)

    if not config:
        logger.critical("Configuração inicial inválida. A encerrar.")
        sys.exit(1)

    processor = FileProcessor(config)


    processor.process_existing_files()

    observer = Observer()
    handler = SmartSortHandler(processor)

    directories = config.get("directories_to_watch", [])
    if not directories:
        logger.warning("Nenhum diretório para monitorizar configurado.")
        return

    for directory in directories:
        if os.path.exists(directory):
            observer.schedule(handler, directory, recursive=False)
            logger.info(f"A monitorizar o diretório: [yellow]{directory}[/yellow]")
        else:
            logger.warning(f"O diretório [red]{directory}[/red] não existe.")

    observer.start()
    logger.info("[bold green]SmartSort em execução. Pressione Ctrl+C para parar.[/bold green]")

    try:
        last_mtime = os.path.getmtime(config_path)
        while True:
            time.sleep(5)


            try:
                current_mtime = os.path.getmtime(config_path)
                if current_mtime > last_mtime:
                    logger.info("Alteração detetada em config.yaml. A recarregar definições...")
                    new_config = load_config(config_path)
                    if new_config:
                        processor.config = new_config
                        processor.power_manager.config = new_config

                        last_mtime = current_mtime
                        logger.info("Configuração atualizada com sucesso!")
            except Exception as e:
                logger.error(f"Erro ao recarregar configuração: {e}")


            if processor.power_manager.is_on_battery():

                pass

    except KeyboardInterrupt:
        observer.stop()
        logger.info("A parar SmartSort...")

    observer.join()


if __name__ == "__main__":
    main()

import os
import time

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .core.engine import FileProcessor


class FileHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.processor = FileProcessor(config)

    def is_temporary(self, path):
        filename = os.path.basename(path)

        temp_extensions = (".part", ".crdownload", ".tmp", ".kate-swp", ".swp", ".swx")
        if (
            filename.startswith(".")
            or filename.endswith(temp_extensions)
            or filename.endswith("~")
        ):
            return True
        return False

    def on_created(self, event):
        if self.is_temporary(event.src_path):
            return

        if not event.is_directory:
            print(f"Novo ficheiro detetado: {event.src_path}")
            self.processor.process_file(event.src_path)
        else:
            print(f"Nova pasta detetada: {event.src_path}")
            self.processor.process_file(event.src_path)


class ConfigHandler(FileSystemEventHandler):
    def __init__(self, observer, config_path, current_handler):
        self.observer = observer
        self.config_path = config_path
        self.handler = current_handler

    def on_modified(self, event):
        if event.src_path.endswith("config.yaml"):
            print(
                "\\n--- Alteração detetada em config.yaml. A recarregar definições... ---"
            )
            new_config = load_config(self.config_path)
            if new_config:

                self.handler.processor.config = new_config
                self.handler.processor.destination_base = new_config.get(
                    "destination_base_folder", "data/sorted"
                )

                self.observer.unschedule_all()
                setup_observers(self.observer, self.handler, new_config)

                self.observer.schedule(
                    self, path=os.path.dirname(self.config_path), recursive=False
                )
                print("--- Configuração atualizada com sucesso! ---\\n")


def load_config(config_path="config/config.yaml"):
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Erro ao carregar o config.yaml: {e}")
        return None


def setup_observers(observer, handler, config):
    directories = config.get("directories_to_watch", [])
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Diretório criado: {directory}")

        abs_path = os.path.abspath(directory)
        observer.schedule(handler, path=abs_path, recursive=False)
        print(f"A monitorizar o diretório: {abs_path}")


def main():
    config_path = "config/config.yaml"
    config = load_config(config_path)
    if not config:
        print("Configuração inicial inválida.")
        return

    observer = Observer()
    handler = FileHandler(config)

    setup_observers(observer, handler, config)

    config_watcher = ConfigHandler(observer, config_path, handler)
    observer.schedule(
        config_watcher, path=os.path.dirname(config_path), recursive=False
    )

    observer.start()
    
    # Gerenciador de bateria para o loop principal
    from smartsort.utils.power import PowerManager
    power_manager = PowerManager(config)

    try:
        while True:
            # Verifica se deve parar totalmente (bateria crítica)
            if power_manager.should_stop_processing():
                print("Interrompendo monitorização para poupar bateria crítica...")
                time.sleep(60) # Dorme por 1 minuto antes de checar de novo
                continue

            # Ajusta o tempo de sleep (mais longo na bateria)
            interval = power_manager.get_throttle_interval()
            time.sleep(interval)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()

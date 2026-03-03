import time
import os
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .core.engine import FileProcessor

class FileHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.processor = FileProcessor(config)

    def on_created(self, event):
        if not event.is_directory:
            print(f"Novo ficheiro detetado: {event.src_path}")
            self.processor.process_file(event.src_path)

def load_config(config_path="config/config.yaml"):
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Erro ao carregar o config.yaml: {e}")
        return None

def main():
    config = load_config()
    if not config or "directories_to_watch" not in config:
        print("Configuração inválida.")
        return

    directories = config["directories_to_watch"]
    

    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Diretório criado: {directory}")

    observer = Observer()
    handler = FileHandler(config)

    for directory in directories:

        abs_path = os.path.abspath(directory)
        observer.schedule(handler, path=abs_path, recursive=False)
        print(f"A monitorizar o diretório: {abs_path}")

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
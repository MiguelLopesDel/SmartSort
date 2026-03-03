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
        # Apenas processar se for um ficheiro/pasta na RAIZ do diretório vigiado
        # e não for um ficheiro temporário
        if not event.is_directory:
            print(f"Novo ficheiro detetado: {event.src_path}")
            self.processor.process_file(event.src_path)
        else:
            # Se for uma pasta, processar a pasta como um bloco
            print(f"Nova pasta detetada: {event.src_path}")
            self.processor.process_file(event.src_path)

class ConfigHandler(FileSystemEventHandler):
    def __init__(self, observer, config_path, current_handler):
        self.observer = observer
        self.config_path = config_path
        self.handler = current_handler

    def on_modified(self, event):
        if event.src_path.endswith("config.yaml"):
            print("\\n--- Alteração detetada em config.yaml. A recarregar definições... ---")
            new_config = load_config(self.config_path)
            if new_config:
                # Atualizar o processador com as novas definições
                self.handler.processor.config = new_config
                self.handler.processor.destination_base = new_config.get("destination_base_folder", "data/sorted")

                # Atualizar pastas de observação
                self.observer.unschedule_all()
                setup_observers(self.observer, self.handler, new_config)

                # Reaproveitar para monitorizar o próprio config.yaml
                self.observer.schedule(self, path=os.path.dirname(self.config_path), recursive=False)
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

    # Inicializar observadores das pastas
    setup_observers(observer, handler, config)

    # Adicionar observador para o próprio ficheiro de configuração (Hot Reload)
    config_watcher = ConfigHandler(observer, config_path, handler)
    observer.schedule(config_watcher, path=os.path.dirname(config_path), recursive=False)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
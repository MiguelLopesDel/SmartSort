import os
import time

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from smartsort.core.engine import FileProcessor


class FileHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor

    def is_temporary(self, path):
        temp_extensions = [".part", ".tmp", ".crdownload", ".swp", ".swx"]
        if any(path.endswith(ext) for ext in temp_extensions):
            return True
        if os.path.basename(path).startswith("."):
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
            # Pequeno delay para evitar leitura de ficheiro em processo de escrita/renomeação
            time.sleep(0.5)
            new_config = load_config(self.config_path)
            if new_config:
                print("\n--- Alteração detetada em config.yaml. A recarregar definições... ---")
                self.handler.processor.config = new_config
                self.handler.processor.destination_base = new_config.get("destination_base_folder", "data/sorted")

                self.observer.unschedule_all()
                setup_observers(self.observer, self.handler, new_config)

                self.observer.schedule(self, path=os.path.dirname(self.config_path), recursive=False)
                print("--- Configuração atualizada com sucesso! ---\n")


def load_config(config_path="config/config.yaml"):
    # Tenta carregar até 3 vezes com pequeno intervalo para lidar com race conditions
    last_error = None
    for attempt in range(3):
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                if config:
                    return config
        except Exception as e:
            last_error = e
            if attempt < 2:
                time.sleep(0.5)
                continue
    if last_error:
        print(f"Erro ao carregar o config.yaml: {last_error}")
    return None


def setup_observers(observer, handler, config):
    directories = config.get("directories_to_watch", [])
    for directory in directories:
        if os.path.exists(directory):
            observer.schedule(handler, path=directory, recursive=False)
            print(f"A monitorizar o diretório: {directory}")
        else:
            print(f"Aviso: O diretório {directory} não existe.")


def main():
    config_path = "config/config.yaml"
    config = load_config(config_path)

    if not config:
        print("Configuração inicial inválida.")
        return

    processor = FileProcessor(config)
    handler = FileHandler(processor)
    observer = Observer()

    setup_observers(observer, handler, config)

    # Monitoriza mudanças no próprio ficheiro de configuração
    config_watcher = ConfigHandler(observer, config_path, handler)
    observer.schedule(config_watcher, path=os.path.dirname(config_path), recursive=False)

    observer.start()

    # Gerenciador de bateria para o loop principal
    from smartsort.utils.power import PowerManager

    power_manager = PowerManager(config)

    try:
        while True:
            # Verifica se deve parar totalmente (bateria crítica)
            if power_manager.should_stop_processing():
                print("Interrompendo monitorização para poupar bateria crítica...")
                time.sleep(60)  # Dorme por 1 minuto antes de checar de novo
                continue

            # Ajusta o tempo de sleep (mais longo na bateria)
            interval = power_manager.get_throttle_interval()
            time.sleep(interval)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()

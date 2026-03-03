import os
import sys
import yaml
import typer
from rich.console import Console
from rich.table import Table

from smartsort.utils.logger import logger

app = typer.Typer(help="CLI de Configuração do SmartSort")
console = Console()

def load_config():
    config_path = "config/config.yaml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Arquivo de configuração não encontrado em {config_path}")
        return None

def save_config(config):
    config_path = "config/config.yaml"
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar configuração: {e}")
        return False

def show_config():
    config = load_config()
    if not config:
        return

    table = Table(title="Configuração SmartSort")
    table.add_column("Opção", style="cyan")
    table.add_column("Valor", style="magenta")

    table.add_row("Modo IA", config["ai_classification"].get("mode", "N/A"))
    table.add_row("Aceleração", str(config["acceleration"].get("enabled", "N/A")))
    table.add_row("Provedor", config["acceleration"].get("provider", "N/A"))
    table.add_row("Vigiando", ", ".join(config.get("directories_to_watch", [])))

    console.print(table)

def set_model(name: str):
    config = load_config()
    if not config:
        return

    config["ai_classification"]["mode"] = "zero_shot"
    config["ai_classification"]["zero_shot_model"] = name
    if save_config(config):
        console.print(f"Modelo alterado para: [cyan]{name}[/cyan]")

def show_status():
    config = load_config()
    if not config:
        return

    from smartsort.utils.power import PowerManager
    from smartsort.utils.recommender import HardwareRecommender

    pm = PowerManager(config)
    rec = HardwareRecommender(config)

    status_table = Table(title="Status do Sistema")
    status_table.add_column("Componente", style="cyan")
    status_table.add_column("Estado", style="green")

    on_battery = pm.is_on_battery()
    status_table.add_row("Bateria", "Sim" if on_battery else "Não (Tomada)")

    p, d = rec.get_best_acceleration(on_battery)
    status_table.add_row("Hardware Recomendado", f"{p.upper()} em {d.upper()}")

    console.print(status_table)

def add_directory(path: str):
    config = load_config()
    if not config:
        return

    full_path = os.path.abspath(path)
    if not os.path.exists(full_path):
        logger.error(f"Diretório não encontrado: {full_path}")
        return

    if full_path in config.get("directories_to_watch", []):
        logger.warning(f"Este diretório já está sendo vigiado: {full_path}")
        return

    config.setdefault("directories_to_watch", []).append(full_path)
    if save_config(config):
        console.print(f"[green]Sucesso:[/green] Diretório [cyan]{full_path}[/cyan] adicionado!")

@app.command(name="show")
def cli_show():
    show_config()

@app.command(name="model")
def cli_model(name: str):
    set_model(name)

@app.command(name="status")
def cli_status():
    show_status()

@app.command(name="add")
def cli_add(path: str):
    add_directory(path)

@app.command(name="tui")
def cli_tui():
    from smartsort.cli.tui import start_tui
    start_tui()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        from smartsort.cli.tui import start_tui
        start_tui()
    else:
        app()

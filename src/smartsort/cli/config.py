import os

import psutil
import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Ferramenta de Configuração Inteligente do SmartSort")
console = Console()

# Caminho padrão da configuração
CONFIG_PATH = "config/config.yaml"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        console.print(
            "[red]Erro:[/red] Arquivo de configuração não encontrado em config/config.yaml"
        )
        raise typer.Exit()
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False, default_flow_style=False)
    console.print("[green]Sucesso:[/green] Configuração atualizada!")


@app.command()
def show():
    """Mostra as configurações atuais de forma visual."""
    config = load_config()

    table = Table(title="Configurações do SmartSort", border_style="cyan")
    table.add_column("Categoria", style="bold yellow")
    table.add_column("Chave", style="white")
    table.add_column("Valor", style="green")

    # Pastas Vigiadas
    dirs = config.get("directories_to_watch", [])
    table.add_row("Monitorização", "Diretórios", "\n".join(dirs))
    table.add_row("Monitorização", "Destino", config.get("destination_base_folder", ""))
    table.add_row(
        "Sistema", "Sugestões Hardware", str(config.get("show_recommendations", True))
    )

    # IA
    ai = config.get("ai_classification", {})
    table.add_row("IA", "Enabled", str(ai.get("enabled", False)))
    table.add_row("IA", "Modo", ai.get("mode", ""))
    table.add_row("IA", "Modelo", ai.get("zero_shot_model", "Default"))

    # Aceleração
    accel = config.get("acceleration", {})
    table.add_row("Hardware", "Aceleração Ativa", str(accel.get("enabled", False)))
    table.add_row("Hardware", "Provider", accel.get("provider", "auto"))
    table.add_row("Hardware", "Device", accel.get("device", "cpu"))

    # Bateria
    power = config.get("power_saving", {})
    table.add_row("Energia", "Economia Bateria", str(power.get("enabled", False)))
    table.add_row(
        "Energia", "Bateria Crítica", f"{power.get('stop_below_percent', 0)}%"
    )

    console.print(table)


@app.command()
def model(name: str):
    """Troca o modelo de Zero-Shot Classification (HuggingFace)."""
    config = load_config()
    if "ai_classification" not in config:
        config["ai_classification"] = {}
    config["ai_classification"]["zero_shot_model"] = name
    save_config(config)
    console.print(f"Modelo alterado para: [cyan]{name}[/cyan]")


@app.command()
def accel(provider: str = "auto", device: str = "gpu", enabled: bool = True):
    """Configura aceleração (provider: cuda, openvino, cpu | device: gpu, cpu)."""
    config = load_config()
    if "acceleration" not in config:
        config["acceleration"] = {}
    config["acceleration"]["enabled"] = enabled
    config["acceleration"]["provider"] = provider.lower()
    config["acceleration"]["device"] = device.lower()
    save_config(config)
    console.print(
        Panel(
            f"Aceleração: [bold]{'LIGADA' if enabled else 'DESLIGADA'}[/bold]\nProvider: {provider}\nDevice: {device}"
        )
    )


@app.command()
def status():
    """Exibe o status do hardware e bateria detectado pelo sistema."""
    battery = psutil.sensors_battery()

    status_table = Table(title="Status do Hardware (Real-Time)", border_style="magenta")
    status_table.add_column("Componente", style="bold white")
    status_table.add_column("Estado", style="cyan")

    if battery:
        plugged = "Conectado" if battery.power_plugged else "Na Bateria"
        color = "green" if battery.power_plugged else "yellow"
        status_table.add_row("Bateria", f"{battery.percent}% ({plugged})", style=color)
    else:
        status_table.add_row("Bateria", "Não detectada (Desktop?)")

    # Simples detecção de GPU via processos ou psutil (apenas exemplo)
    status_table.add_row("CPU Usage", f"{psutil.cpu_percent()}%")
    status_table.add_row("RAM Usage", f"{psutil.virtual_memory().percent}%")

    console.print(status_table)


@app.command()
def battery_mode(on: bool = True):
    """Ativa ou desativa rapidamente o modo de economia de energia."""
    config = load_config()
    if "power_saving" not in config:
        config["power_saving"] = {}
    config["power_saving"]["enabled"] = on
    save_config(config)
    status = "[green]ATIVADO[/green]" if on else "[red]DESATIVADO[/red]"
    console.print(f"Modo de Economia de Energia: {status}")


@app.command()
def add_dir(path: str):
    """Adiciona um novo diretório para o SmartSort vigiar."""
    config = load_config()
    dirs = config.get("directories_to_watch", [])
    full_path = os.path.abspath(path)
    if full_path not in dirs:
        dirs.append(full_path)
        config["directories_to_watch"] = dirs
        save_config(config)
    else:
        console.print("[yellow]Aviso:[/yellow] Este diretório já está sendo vigiado.")


@app.command()
def rm_dir(path: str):
    """Remove um diretório da lista de vigilância."""
    config = load_config()
    dirs = config.get("directories_to_watch", [])
    full_path = os.path.abspath(path)
    if full_path in dirs:
        dirs.remove(full_path)
        config["directories_to_watch"] = dirs
        save_config(config)
    else:
        console.print("[red]Erro:[/red] Diretório não encontrado.")


if __name__ == "__main__":
    app()

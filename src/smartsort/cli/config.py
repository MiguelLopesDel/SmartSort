import os
import yaml
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Ferramenta de Configuração Inteligente do SmartSort")
console = Console()

# Caminho padrão da configuração
CONFIG_PATH = "config/config.yaml"

def load_config():
    if not os.path.exists(CONFIG_PATH):
        console.print("[red]Erro:[/red] Arquivo de configuração não encontrado em config/config.yaml")
        raise typer.Exit()
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False, default_flow_style=False)
    console.print("[green]Sucesso:[/green] Configuração atualizada com sucesso!")

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
    
    # IA
    ai = config.get("ai_classification", {})
    table.add_row("IA", "Enabled", str(ai.get("enabled", False)))
    table.add_row("IA", "Modo", ai.get("mode", ""))
    
    # Aceleração
    accel = config.get("acceleration", {})
    table.add_row("Hardware", "Aceleração (GPU)", str(accel.get("enabled", False)))
    table.add_row("Hardware", "Dispositivo", accel.get("device", "cpu"))
    
    # Bateria
    power = config.get("power_saving", {})
    table.add_row("Energia", "Economia Bateria", str(power.get("enabled", False)))
    table.add_row("Energia", "Bateria Crítica", f"{power.get('stop_below_percent', 0)}%")
    
    console.print(table)

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
        console.print(f"Diretório [cyan]{full_path}[/cyan] adicionado à lista.")
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
        console.print(f"Diretório [cyan]{full_path}[/cyan] removido.")
    else:
        # Tenta remover pelo nome parcial se o abspath não bater
        found = False
        for d in dirs:
            if path in d:
                dirs.remove(d)
                found = True
                break
        if found:
            save_config(config)
        else:
            console.print("[red]Erro:[/red] Diretório não encontrado na lista.")

@app.command()
def set(key: str, value: str):
    """Altera uma configuração específica (ex: acceleration.enabled true)."""
    config = load_config()
    
    # Converte valores booleanos
    if value.lower() == "true": value = True
    elif value.lower() == "false": value = False
    elif value.isdigit(): value = int(value)
    
    keys = key.split(".")
    target = config
    
    # Navega pelas sub-chaves (ex: ai_classification.enabled)
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]
    
    target[keys[-1]] = value
    save_config(config)
    console.print(f"Chave [yellow]{key}[/yellow] definida para [cyan]{value}[/cyan]")

@app.command()
def battery(on: bool = True):
    """Ativa ou desativa rapidamente o modo de economia de energia."""
    config = load_config()
    if "power_saving" not in config: config["power_saving"] = {}
    config["power_saving"]["enabled"] = on
    save_config(config)
    status = "[green]ATIVADO[/green]" if on else "[red]DESATIVADO[/red]"
    console.print(Panel(f"Modo de Economia de Energia: {status}"))

if __name__ == "__main__":
    app()

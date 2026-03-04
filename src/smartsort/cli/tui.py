import os
import sys
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.prompt import Prompt, IntPrompt
from rich import box

from smartsort.cli.config import load_config, save_config, add_directory, set_model, show_status
from smartsort.utils.logger import logger

console = Console()

class SmartSortTUI:
    def __init__(self):
        self.config = load_config()
        if not self.config:
            console.print("[red]Erro ao carregar configuração. Abortando TUI.[/red]")
            sys.exit(1)

    def draw_header(self):
        return Panel(
            "[bold blue]SmartSort - Painel de Controle Interativo[/bold blue]\n"
            "[dim]Use os números para navegar e configurar seu sistema[/dim]",
            box=box.DOUBLE_EDGE,
            style="cyan"
        )

    def draw_status_summary(self):
        from smartsort.utils.power import PowerManager
        from smartsort.utils.recommender import HardwareRecommender
        
        pm = PowerManager(self.config)
        rec = HardwareRecommender(self.config)
        on_battery = pm.is_on_battery()
        p, d = rec.get_best_acceleration(on_battery)
        
        table = Table(box=box.SIMPLE, expand=True)
        table.add_column("Monitorando", style="green")
        table.add_column("Modo IA", style="magenta")
        table.add_column("Aceleração", style="yellow")
        table.add_column("Energia", style="cyan")
        table.add_column("Impacto App", style="red")
        
        dirs = len(self.config.get("directories_to_watch", []))
        ai_mode = self.config["ai_classification"].get("mode", "off")
        accel = f"{p.upper()} ({d})"
        
        if on_battery:
            battery_pct = pm.get_battery_percent()
            app_impact = pm.estimate_app_impact()
            discharge = pm.get_system_discharge_rate()
            
            power_str = f"🔋 {battery_pct}%"
            impact_str = f"{app_impact:.1f}% do uso"
            if discharge:
                impact_str += f" ({discharge:.1f}W sys)"
        else:
            power_str = "🔌 Tomada"
            impact_str = "N/A"
        
        table.add_row(f"{dirs} pastas", ai_mode, accel, power_str, impact_str)
        return table

    def main_menu(self):
        while True:
            console.clear()
            console.print(self.draw_header())
            console.print(self.draw_status_summary())
            
            menu_table = Table(show_header=False, box=box.ROUNDED, expand=True)
            menu_table.add_row("[bold yellow]1.[/bold yellow] 📊 Ver Status Detalhado")
            menu_table.add_row("[bold yellow]2.[/bold yellow] 📁 Adicionar Pasta para Vigiar")
            menu_table.add_row("[bold yellow]3.[/bold yellow] 🧠 Alterar Modelo de IA")
            menu_table.add_row("[bold yellow]4.[/bold yellow] ⚡ Alternar Aceleração (ON/OFF)")
            menu_table.add_row("[bold yellow]5.[/bold yellow] 📜 Ver Últimos Logs")
            menu_table.add_row("[bold yellow]0.[/bold yellow] 🚪 Sair")
            
            console.print(Panel(menu_table, title="Menu Principal", border_style="blue"))
            
            choice = IntPrompt.ask("Escolha uma opção", choices=["0", "1", "2", "3", "4", "5"], default=0)
            
            if choice == 1:
                show_status()
                Prompt.ask("\nPressione Enter para voltar")
            elif choice == 2:
                path = Prompt.ask("Digite o caminho completo da pasta")
                if path:
                    add_directory(path)
                    self.config = load_config()
                    time.sleep(1.5)
            elif choice == 3:
                model = Prompt.ask("Digite o nome do modelo (ex: MoritzLaurer/mDeBERTa-v3-base-mnli-xnli)")
                if model:
                    set_model(model)
                    self.config = load_config()
                    time.sleep(1.5)
            elif choice == 4:
                enabled = self.config["acceleration"].get("enabled", False)
                self.config["acceleration"]["enabled"] = not enabled
                save_config(self.config)
                console.print(f"Aceleração {'[green]Ativada[/green]' if not enabled else '[red]Desativada[/red]'}")
                time.sleep(1.5)
            elif choice == 5:
                self.show_logs()
            elif choice == 0:
                console.print("[yellow]Saindo do modo TUI...[/yellow]")
                break

    def show_logs(self, lines=15):

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        log_path = os.path.join(project_root, "data", "smartsort.log")
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                content = f.readlines()
                last_logs = "".join(content[-lines:])
                console.print(Panel(last_logs, title="Últimos Logs", border_style="dim"))
        else:
            console.print("[red]Arquivo de log não encontrado.[/red]")
        Prompt.ask("\nPressione Enter para voltar")

def start_tui():
    tui = SmartSortTUI()
    tui.main_menu()

if __name__ == "__main__":
    start_tui()

import platform

import psutil

from smartsort.utils.logger import logger


class HardwareRecommender:
    def __init__(self, config):
        self.config = config

    def get_best_acceleration(self, on_battery=False):
        """
        Recomenda o melhor par (provider, device) baseado no hardware atual.
        """
        cpu_brand = platform.processor().lower()
        has_nvidia = self._check_nvidia_gpu()

        if on_battery:

            if "intel" in cpu_brand or "amd" in cpu_brand:
                return "openvino", "GPU" if "intel" in cpu_brand else "CPU"
            return "auto", "CPU"

        if has_nvidia:
            return "cuda", "GPU"

        if "intel" in cpu_brand or "amd" in cpu_brand:
            return "openvino", "GPU"

        return "auto", "CPU"

    def _check_nvidia_gpu(self):

        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    def show_analysis(self):
        on_battery = False
        try:
            battery = psutil.sensors_battery()
            if battery:
                on_battery = not battery.power_plugged
        except Exception:
            pass

        p, d = self.get_best_acceleration(on_battery)
        reason = "Tomada Detetada" if not on_battery else "Modo Bateria Ativo"

        logger.info("[bold blue]" + "=" * 50 + "[/bold blue]")
        logger.info("[bold]🔍 ANÁLISE DE HARDWARE SMART_SORT[/bold]")
        logger.info("[bold blue]" + "=" * 50 + "[/bold blue]")
        logger.info(f"Status: [cyan]{reason}[/cyan]")

        if on_battery:
            logger.info("💻 [yellow]Notebook detectado em bateria! Priorizando eficiência.[/yellow]")

        logger.info(f"Recomendação: [green]{p.upper()}[/green] usando [green]{d.upper()}[/green]")
        logger.info("[bold blue]" + "=" * 50 + "[/bold blue]")

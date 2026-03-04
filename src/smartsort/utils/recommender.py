import platform
from typing import Any, Dict, Tuple

import psutil

from smartsort.utils.logger import logger


class HardwareRecommender:
    def __init__(self, config: Any) -> None:
        self.config = config

    def get_best_acceleration(self, on_battery: bool = False) -> Tuple[str, str]:
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

    def _check_nvidia_gpu(self) -> bool:

        try:
            import torch

            return bool(torch.cuda.is_available())
        except ImportError:
            return False

    def recommend_audio_config(self, on_battery: bool = False) -> Dict[str, Any]:
        """Sugere uma configuração de áudio baseada no hardware atual."""
        has_nvidia = self._check_nvidia_gpu()
        total_ram_gb = psutil.virtual_memory().total / (1024**3)

        if on_battery:
            if total_ram_gb < 8:
                return {"enabled": False, "model": "tiny", "use_gpu": False}
            return {"enabled": True, "model": "tiny", "use_gpu": False}

        if has_nvidia:
            return {"enabled": True, "model": "base", "use_gpu": True}
        elif total_ram_gb >= 16:
            return {"enabled": True, "model": "base", "use_gpu": False}

        return {"enabled": True, "model": "tiny", "use_gpu": False}

    def show_analysis(self) -> None:
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

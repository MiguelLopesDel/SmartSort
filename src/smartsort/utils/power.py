import logging

import psutil


class PowerManager:
    """Monitora o estado da bateria e fornece recomendações para economia de energia."""

    def __init__(self, config):
        self.config = config.get("power_saving", {})
        self.logger = logging.getLogger(__name__)

    def is_on_battery(self):
        """Verifica se o dispositivo está rodando na bateria (sem cabo conectado)."""
        battery = psutil.sensors_battery()
        if battery:
            return not battery.power_plugged
        return False

    def get_battery_percent(self):
        """Retorna o nível da bateria em porcentagem."""
        battery = psutil.sensors_battery()
        if battery:
            return battery.percent
        return 100

    def should_stop_processing(self):
        """Verifica se o processamento deve ser interrompido por bateria baixa."""
        if not self.config.get("enabled", False):
            return False

        if self.is_on_battery():
            percent = self.get_battery_percent()
            threshold = self.config.get("stop_below_percent", 20)
            if percent < threshold:
                self.logger.warning(f"Bateria em {percent}%. Abaixo do limite de {threshold}%. Parando.")
                return True
        return False

    def should_use_fallback(self):
        """Verifica se o sistema deve evitar modelos pesados de IA."""
        if not self.config.get("enabled", False):
            return False

        if self.is_on_battery() and self.config.get("pause_ai_on_battery", True):
            self.logger.info("Modo Bateria Ativo: Usando regras simples de fallback para economizar energia.")
            return True
        return False

    def get_throttle_interval(self):
        """Retorna o intervalo sugerido de sleep entre processamentos."""
        if not self.config.get("enabled", False):
            return 1

        if self.is_on_battery():
            return self.config.get("throttle_interval_sec", 10)
        return 1

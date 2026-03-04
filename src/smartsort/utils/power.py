import logging
import os

import psutil


class PowerManager:
    """Monitora o estado da bateria e fornece recomendações para economia de energia."""

    def __init__(self, config):
        self.config = config.get("power_saving", {})
        self.logger = logging.getLogger(__name__)
        self.process = psutil.Process(os.getpid())

    def get_process_resource_usage(self):
        """Retorna o uso de CPU e Memória do processo atual."""
        try:
            cpu_pct = self.process.cpu_percent(interval=0.1)
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            return cpu_pct, memory_mb
        except Exception:
            return 0.0, 0.0

    def get_system_discharge_rate(self):
        """Tenta obter a taxa de descarga do sistema em Watts (se disponível no Linux)."""
        power_supply_path = "/sys/class/power_supply/"
        if not os.path.exists(power_supply_path):
            return None

        try:
            for supply in os.listdir(power_supply_path):
                supply_path = os.path.join(power_supply_path, supply)
                type_file = os.path.join(supply_path, "type")
                
                if os.path.exists(type_file):
                    with open(type_file, "r") as f:
                        if f.read().strip() == "Battery":
                            voltage_file = os.path.join(supply_path, "voltage_now")
                            current_file = os.path.join(supply_path, "current_now")
                            power_file = os.path.join(supply_path, "power_now")

                            if os.path.exists(power_file):
                                with open(power_file, "r") as pf:
                                    return abs(int(pf.read().strip())) / 1_000_000.0
                            elif os.path.exists(voltage_file) and os.path.exists(current_file):
                                with open(voltage_file, "r") as vf, open(current_file, "r") as cf:
                                    v = int(vf.read().strip()) / 1_000_000.0
                                    i = abs(int(cf.read().strip())) / 1_000_000.0
                                    return v * i
        except Exception:
            pass
        return None

    def estimate_app_impact(self):
        """Estima o impacto do app no consumo de bateria (%) com base no uso de CPU."""
        cpu_usage, _ = self.get_process_resource_usage()
        on_battery = self.is_on_battery()
        
        if not on_battery:
            return 0.0




        system_cpu_usage = psutil.cpu_percent()
        if system_cpu_usage > 0:
            app_relative_weight = (cpu_usage / system_cpu_usage) * 100
        else:
            app_relative_weight = 0.0
            
        return min(app_relative_weight, 100.0)

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

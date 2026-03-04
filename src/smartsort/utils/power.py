import logging
import os
import time

import psutil


class PowerManager:
    """Monitora o estado da bateria e fornece recomendações para economia de energia."""

    def __init__(self, config):
        self.config = config.get("power_saving", {}) if config else {}
        self.logger = logging.getLogger(__name__)
        try:
            self.process = psutil.Process(os.getpid())
        except Exception:
            self.process = None
        

        self.start_time = time.time()
        self.total_joules_consumed = 0.0
        self.last_update_time = time.time()
        self._battery_voltage_cache = 11.1

    def update_accumulated_energy(self):
        """Calcula e acumula a energia consumida desde a última atualização."""
        now = time.time()
        duration = now - self.last_update_time
        if duration <= 0:
            return

        discharge_rate = self.get_system_discharge_rate()
        if discharge_rate is None:

            discharge_rate = 15.0

        app_impact_ratio = self.estimate_app_impact() / 100.0
        app_watts = discharge_rate * app_impact_ratio
        

        self.total_joules_consumed += app_watts * duration
        self.last_update_time = now

    def get_consumed_stats(self):
        """Retorna estatísticas formatadas do consumo acumulado."""
        self.update_accumulated_energy()
        


        wh = self.total_joules_consumed / 3600.0
        


        v = self._get_battery_voltage() or self._battery_voltage_cache
        mah = (wh * 1000.0) / v
        
        return {
            "joules": self.total_joules_consumed,
            "wh": wh,
            "mah": mah,
            "uptime_sec": time.time() - self.start_time
        }

    def _get_battery_voltage(self):
        """Obtém a voltagem atual da bateria em Volts."""
        power_supply_path = "/sys/class/power_supply/"
        if not os.path.exists(power_supply_path):
            return None
        try:
            for supply in os.listdir(power_supply_path):
                path = os.path.join(power_supply_path, supply)
                if os.path.exists(os.path.join(path, "type")):
                    with open(os.path.join(path, "type"), "r") as f:
                        if f.read().strip() == "Battery":
                            v_file = os.path.join(path, "voltage_now")
                            if os.path.exists(v_file):
                                with open(v_file, "r") as vf:
                                    return int(vf.read().strip()) / 1_000_000.0
        except Exception:
            pass
        return None

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

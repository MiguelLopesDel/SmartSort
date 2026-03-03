import subprocess
import psutil

class HardwareRecommender:
    def __init__(self, config=None):
        self.config = config or {}
        self.show_recommendations = self.config.get("show_recommendations", True)

    def detect_gpu(self):
        """Detecta detalhes da GPU via lspci."""
        try:
            output = subprocess.check_output("lspci -nn | grep -E -i '(VGA|3D)'", shell=True).decode()
            gpu_info = output.lower()
            
            if "nvidia" in gpu_info:
                return "nvidia", "cuda"
            elif "intel" in gpu_info:
                return "intel", "openvino"
            elif "amd" in gpu_info or "ati" in gpu_info:
                return "amd", "openvino"
        except Exception:
            pass
        return "cpu_only", "cpu"

    def get_best_acceleration(self, is_on_battery=False):
        """Resolve dinamicamente o melhor provider e device."""
        gpu_type, provider = self.detect_gpu()
        
        # Se estiver na bateria, priorizamos economia (iGPU ou CPU)
        if is_on_battery:
            if gpu_type in ["intel", "amd"]:
                return "openvino", "gpu" # iGPU é mais eficiente que dedicada
            return "cpu", "cpu"

        # Se estiver na tomada, força performance máxima
        if gpu_type == "nvidia":
            return "cuda", "gpu"
        elif gpu_type in ["intel", "amd"]:
            return "openvino", "gpu"
            
        return "cpu", "cpu"

    def get_recommendation(self):
        """Gera um relatório para o instalador (lógica legada mantida para compatibilidade)."""
        mem = psutil.virtual_memory()
        cpu_count = psutil.cpu_count(logical=False)
        battery = psutil.sensors_battery()
        gpu_type, provider = self.detect_gpu()
        
        is_notebook = battery is not None
        on_battery = not battery.power_plugged if battery else False
        
        best_p, best_d = self.get_best_acceleration(on_battery)
        
        rec = {
            "acceleration": {
                "enabled": True, 
                "provider": best_p, 
                "device": best_d, 
                "quantization": "int8" if mem.total < 8 * 1024**3 else "fp16"
            },
            "power_saving": {"enabled": is_notebook},
            "ai_classification": {"enabled": True}
        }
        
        reason = "Hardware de alta performance detectado." if gpu_type != "cpu_only" else "Usando otimizações de CPU."
        return rec, reason, is_notebook

    def print_formatted_recommendation(self):
        if not self.show_recommendations: return
        rec, reason, is_notebook = self.get_recommendation()
        print("\n" + "="*50)
        print("🔍 ANÁLISE DE HARDWARE SMART_SORT")
        print("="*50)
        print(f"Status: {reason}")
        if is_notebook: print("💻 Notebook detectado!")
        print(f"\nConfiguração Ativa: {rec['acceleration']['provider'].upper()} ({rec['acceleration']['device'].upper()})")
        print("="*50 + "\n")

if __name__ == "__main__":
    HardwareRecommender().print_formatted_recommendation()

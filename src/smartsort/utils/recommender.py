import psutil
import subprocess
import os
import json
import logging

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
                if "arc" in gpu_info or "iris" in gpu_info:
                    return "intel_high", "openvino"
                return "intel_igpu", "openvino"
            elif "amd" in gpu_info or "ati" in gpu_info:
                if "radeon rx" in gpu_info or "navi" in gpu_info:
                    return "amd_dedicated", "openvino"
                return "amd_igpu", "openvino"
        except:
            pass
        return "cpu_only", "cpu"

    def get_recommendation(self):
        """Gera um relatório de recomendações baseado no hardware detectado."""
        mem = psutil.virtual_memory()
        cpu_count = psutil.cpu_count(logical=False)
        battery = psutil.sensors_battery()
        gpu_type, provider = self.detect_gpu()
        
        rec = {
            "acceleration": {"enabled": True, "provider": provider, "device": "gpu", "quantization": "int8"},
            "power_saving": {"enabled": False},
            "ai_classification": {"enabled": True, "zero_shot_model": "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"}
        }

        # Lógica de RAM e CPU (Subestimar vs Sobrecarregar)
        if mem.total < 4 * 1024**3 or cpu_count < 4:
            # Hardware fraco: Desativa IA por padrão para não travar o PC
            rec["ai_classification"]["enabled"] = False
            rec["acceleration"]["enabled"] = False
            reason = "Hardware com recursos limitados (RAM/CPU)."
        elif mem.total < 8 * 1024**3:
            # Hardware médio: IA ligada mas com modelo leve/quantizado
            rec["acceleration"]["quantization"] = "int8"
            reason = "Hardware equilibrado. Usando quantização INT8 para poupar RAM."
        else:
            # Hardware potente: Pode usar FP16
            rec["acceleration"]["quantization"] = "fp16"
            reason = "Hardware de alta performance detectado."

        # Ajuste de GPU
        if gpu_type == "cpu_only":
            rec["acceleration"]["device"] = "cpu"
        elif gpu_type == "nvidia":
            rec["acceleration"]["provider"] = "cuda"
            rec["acceleration"]["device"] = "gpu"
        
        # Ajuste de Notebook
        is_notebook = battery is not None
        if is_notebook:
            rec["power_saving"]["enabled"] = True
            
        return rec, reason, is_notebook

    def print_formatted_recommendation(self):
        """Imprime a sugestão de forma amigável para o instalador."""
        if not self.show_recommendations:
            return

        rec, reason, is_notebook = self.get_recommendation()
        
        print("\n" + "="*50)
        print("🔍 ANÁLISE DE HARDWARE SMART_SORT")
        print("="*50)
        print(f"Status: {reason}")
        if is_notebook:
            print("💻 Notebook detectado! Ativando modo de economia de bateria.")
        
        print("\nConfigurações sugeridas:")
        print(f"  - Aceleração: {rec['acceleration']['provider']} ({rec['acceleration']['device']})")
        print(f"  - Precisão: {rec['acceleration']['quantization']}")
        print(f"  - IA Ativa: {'Sim' if rec['ai_classification']['enabled'] else 'Não'}")
        print("="*50 + "\n")

if __name__ == "__main__":
    recommender = HardwareRecommender()
    recommender.print_formatted_recommendation()

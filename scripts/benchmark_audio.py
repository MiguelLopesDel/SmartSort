import os
import subprocess
import sys
import threading
import time

import psutil
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

REQUIRED_PACKAGES = ["openai-whisper", "torch", "numpy"]


def check_dependencies():
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            console.print(f"[yellow]Instalando dependência necessária: {pkg}...[/yellow]")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


def create_test_video(output_path, duration=10):
    if os.path.exists(output_path):
        return
    console.print(f"[blue]Gerando vídeo de teste ({duration}s)...[/blue]")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc=duration={duration}:size=640x480:rate=30",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=1000:duration={duration}",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        output_path,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class ResourceMonitor(threading.Thread):
    def __init__(self, interval=0.1):
        super().__init__()
        self.interval = interval
        self.stopped = False
        self.stats = {"cpu_percent": [], "ram_mb": []}
        self.process = psutil.Process(os.getpid())

    def run(self):
        while not self.stopped:
            self.stats["cpu_percent"].append(psutil.cpu_percent(interval=None))
            self.stats["ram_mb"].append(self.process.memory_info().rss / (1024 * 1024))
            time.sleep(self.interval)

    def stop(self):
        self.stopped = True


def run_benchmark(model_name, video_path):
    import whisper

    console.print(f"\n[bold green]Testando Whisper: {model_name}[/bold green]")
    model = whisper.load_model(model_name)

    monitor = ResourceMonitor()
    monitor.start()
    transcribe_start = time.time()
    model.transcribe(video_path)
    transcribe_duration = time.time() - transcribe_start
    monitor.stop()
    monitor.join()

    return {
        "model": model_name,
        "transcribe_time": transcribe_duration,
        "avg_cpu": sum(monitor.stats["cpu_percent"]) / len(monitor.stats["cpu_percent"]),
        "max_ram": max(monitor.stats["ram_mb"]),
    }


def main():
    check_dependencies()
    video_path = "data/test_benchmark.mp4"
    os.makedirs("data", exist_ok=True)
    create_test_video(video_path, duration=15)

    results = []
    for model in ["tiny", "base"]:
        try:
            results.append(run_benchmark(model, video_path))
        except Exception as e:
            console.print(f"[red]Erro no modelo {model}: {e}[/red]")

    table = Table(title="📊 Resultado do Benchmark")
    table.add_column("Modelo", style="cyan")
    table.add_column("Tempo (15s vídeo)")
    table.add_column("CPU Média")
    table.add_column("RAM Máxima")
    for r in results:
        table.add_row(r["model"], f"{r['transcribe_time']:.2f}s", f"{r['avg_cpu']:.1f}%", f"{r['max_ram']:.0f}MB")
    console.print(table)

    from smartsort.cli.config import load_config
    from smartsort.utils.recommender import HardwareRecommender

    cfg = load_config()
    rec = HardwareRecommender(cfg)

    ac_rec = rec.recommend_audio_config(on_battery=False)
    batt_rec = rec.recommend_audio_config(on_battery=True)

    recommendation_text = f"""
[bold green]Configuração Recomendada para seu Sistema:[/bold green]

[yellow]Modo TOMADA:[/yellow]
- Ativo: {ac_rec['enabled']}
- Modelo: {ac_rec['model']}
- Aceleração GPU: {ac_rec['use_gpu']}

[yellow]Modo BATERIA:[/yellow]
- Ativo: {batt_rec['enabled']}
- Modelo: {batt_rec['model']}
- Aceleração GPU: {batt_rec['use_gpu']}

[dim]Dica: O modelo 'tiny' é ideal para CPUs integradas. O 'base' oferece mais precisão para memes complexos.[/dim]
"""
    console.print(Panel(recommendation_text, title="🧠 Decisão de Engenharia", border_style="blue"))


if __name__ == "__main__":
    main()

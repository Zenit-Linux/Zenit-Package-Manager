import os
import requests
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TimeRemainingColumn, TransferSpeedColumn
from rich.panel import Panel

console = Console(highlight=True, style="bold white on black")

class Downloader:
    def download_package(self, package_url, package_name):
        try:
            response = requests.get(package_url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            cache_path = f"/var/cache/zenit/packages/{package_name}.rpm"
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "wb") as f, Progress(
                TextColumn("[bold cyan]{task.description}"),
                BarColumn(bar_width=None, style="bar.back", complete_style="green.complete"),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                task = progress.add_task(f"[bold cyan]Downloading {package_name}[/bold cyan]", total=total_size)
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
            console.print(Panel(f"[bold green]Downloaded package {package_name}[/bold green]", title="[bold green]Success[/bold green]", border_style="green"))
            return cache_path
        except Exception as e:
            console.print(Panel(f"[bold red]Error downloading {package_name}: {e}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
            return None

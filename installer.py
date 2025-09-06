import gnupg
import os
import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console(highlight=True, style="bold white on black")

class Installer:
    def __init__(self):
        self.gpg = gnupg.GPG()

    def verify_gpg(self, package_path):
        result = self.gpg.verify_file(open(package_path, "rb"))
        if result.valid:
            console.print(f"[bold green]GPG signature verified for {package_path}[/bold green]")
            return True
        console.print(Panel(f"[bold red]Invalid GPG signature for {package_path}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
        return False

    def install_package(self, package_path, action="install"):
        try:
            if action == "install":
                subprocess.run(["rpm", "-i", "--nodeps", package_path], check=True)
                console.print(Panel(f"[bold green]Installed package {package_path}[/bold green]", title="[bold green]Success[/bold green]", border_style="green"))
            elif action == "remove":
                package_name = os.path.basename(package_path).replace(".rpm", "")
                subprocess.run(["rpm", "-e", package_name], check=True)
                console.print(Panel(f"[bold green]Removed package {package_name}[/bold green]", title="[bold green]Success[/bold green]", border_style="green"))
        except Exception as e:
            console.print(Panel(f"[bold red]Error during {action} {package_path}: {e}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))

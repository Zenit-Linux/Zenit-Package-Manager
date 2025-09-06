import json
import os
from jsonschema import validate
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn, SpinnerColumn
from rich.panel import Panel

console = Console(highlight=True, style="bold white on black")

SOURCES_SCHEMA = {
    "type": "object",
    "properties": {
        "repos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "type": {"type": "string"},
                    "enabled": {"type": "boolean"},
                    "priority": {"type": "integer"},
                    "gpgcheck": {"type": "boolean"},
                    "mirrorlist": {"type": ["string", "null"]},
                    "description": {"type": "string"}
                },
                "required": ["name", "url", "type", "enabled", "priority", "gpgcheck"]
            }
        }
    },
    "required": ["repos"]
}

class RepoManager:
    def __init__(self, sources_file="/etc/zenit/sources.list", cache_dir="/var/cache/zenit"):
        self.sources_file = sources_file
        self.cache_dir = cache_dir
        self.repos = self.load_sources()

    def load_sources(self):
        try:
            with open(self.sources_file, "r") as f:
                data = json.load(f)
                validate(instance=data, schema=SOURCES_SCHEMA)
                return data["repos"]
        except Exception as e:
            console.print(Panel(f"[bold red]Error loading {self.sources_file}: {e}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
            return []

    def save_sources(self):
        try:
            data = {"repos": self.repos}
            with open(self.sources_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            console.print(Panel(f"[bold red]Error saving {self.sources_file}: {e}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))

    def update_cache(self):
        progress = Progress(
            SpinnerColumn(style="bold cyan"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None, style="bar.back", complete_style="green.complete"),
            TaskProgressColumn(text_format="[bold green]{task.percentage:>3.0f}%[/bold green]"),
            TimeRemainingColumn(),
            console=console
        )
        with progress:
            main_task = progress.add_task("[bold cyan]Updating repositories...[/bold cyan]", total=len(self.repos))
            for repo in self.repos:
                if repo["enabled"]:
                    sub_task = progress.add_task(f"[bold blue]Fetching metadata for {repo['name']}...[/bold blue]", total=100)
                    self.download_metadata(repo)
                    progress.update(sub_task, advance=100)
                progress.update(main_task, advance=1)
        console.print(Panel("[bold green]Repository metadata updated successfully.[/bold green]", title="[bold green]Success[/bold green]", border_style="green"))

    def download_metadata(self, repo):
        files = ["repomd.xml", "primary.xml.gz", "filelists.xml.gz", "other.xml.gz"]
        for file in files:
            import requests
            try:
                url = f"{repo['url']}repodata/{file}"
                response = requests.get(url)
                response.raise_for_status()
                cache_path = os.path.join(self.cache_dir, repo["name"], file)
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, "wb") as f:
                    f.write(response.content)
                console.print(f"[bold blue]Downloaded {file} for {repo['name']}[/bold blue]")
            except Exception as e:
                console.print(f"[bold red]Error downloading {file} for {repo['name']}: {e}[/bold red]")

    def add_repo(self, new_repo):
        for existing in self.repos:
            if existing["name"] == new_repo["name"]:
                console.print(Panel("[bold red]Repository with this name already exists.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
                return
        self.repos.append(new_repo)
        self.save_sources()

    def remove_repo(self, name):
        initial_len = len(self.repos)
        self.repos = [r for r in self.repos if r["name"] != name]
        if len(self.repos) < initial_len:
            self.save_sources()
        else:
            console.print(Panel("[bold red]Repository not found.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))

    def enable_repo(self, name):
        for repo in self.repos:
            if repo["name"] == name:
                repo["enabled"] = True
                self.save_sources()
                return
        console.print(Panel("[bold red]Repository not found.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))

    def disable_repo(self, name):
        for repo in self.repos:
            if repo["name"] == name:
                repo["enabled"] = False
                self.save_sources()
                return
        console.print(Panel("[bold red]Repository not found.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))

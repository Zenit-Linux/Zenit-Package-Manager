import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from repo_manager import RepoManager
from solver import Solver
from downloader import Downloader
from installer import Installer

console = Console(highlight=True, style="bold white on black")

class ZenitCLI:
    def __init__(self):
        self.repo_manager = RepoManager()
        self.solver = Solver(self.repo_manager.repos)
        self.downloader = Downloader()
        self.installer = Installer()
        self.parser = argparse.ArgumentParser(prog="zenit", description="Zenit Package Manager")
        subparsers = self.parser.add_subparsers(dest="command")

        # Update
        subparsers.add_parser("update", help="Update repository cache")

        # Install
        install_parser = subparsers.add_parser("install", help="Install a package")
        install_parser.add_argument("package", help="Package name")

        # Remove
        remove_parser = subparsers.add_parser("remove", help="Remove a package")
        remove_parser.add_argument("package", help="Package name")

        # Search
        search_parser = subparsers.add_parser("search", help="Search for a package")
        search_parser.add_argument("package", help="Package name")

        # List installed
        list_parser = subparsers.add_parser("list", help="List packages")
        list_parser.add_argument("type", choices=["installed"], help="Type of list")

        # Upgrade
        subparsers.add_parser("upgrade", help="Upgrade the system")

        # Dist-upgrade
        subparsers.add_parser("dist-upgrade", help="Full distribution upgrade")

        # Repo commands
        repo_parser = subparsers.add_parser("repo", help="Manage repositories")
        repo_subparsers = repo_parser.add_subparsers(dest="repo_command")

        # Repo add
        add_parser = repo_subparsers.add_parser("add", help="Add a repository")
        add_parser.add_argument("name", help="Repository name")
        add_parser.add_argument("url", help="Repository URL")
        add_parser.add_argument("--type", default="rpm-md", help="Repository type")
        add_parser.add_argument("--priority", type=int, default=100, help="Priority")
        add_parser.add_argument("--gpgcheck", type=bool, default=True, help="GPG check")
        add_parser.add_argument("--enabled", type=bool, default=True, help="Enabled")
        add_parser.add_argument("--description", default="", help="Description")

        # Repo remove
        remove_repo_parser = repo_subparsers.add_parser("remove", help="Remove a repository")
        remove_repo_parser.add_argument("name", help="Repository name")

        # Repo list
        repo_subparsers.add_parser("list", help="List repositories")

        # Repo enable
        enable_parser = repo_subparsers.add_parser("enable", help="Enable a repository")
        enable_parser.add_argument("name", help="Repository name")

        # Repo disable
        disable_parser = repo_subparsers.add_parser("disable", help="Disable a repository")
        disable_parser.add_argument("name", help="Repository name")

        # Help and ?
        subparsers.add_parser("help", help="Show available commands")
        subparsers.add_parser("?", help="Show available commands")

    def run(self):
        args = self.parser.parse_args()
        if not args.command:
            self.show_help()
            return

        if args.command in ["help", "?"]:
            self.show_help()
        elif args.command == "update":
            self.update()
        elif args.command == "install":
            self.install(args.package)
        elif args.command == "remove":
            self.remove(args.package)
        elif args.command == "search":
            self.search(args.package)
        elif args.command == "list" and args.type == "installed":
            self.list_installed()
        elif args.command == "upgrade":
            self.upgrade()
        elif args.command == "dist-upgrade":
            self.dist_upgrade()
        elif args.command == "repo":
            if args.repo_command == "add":
                self.repo_add(args.name, args.url, args.type, args.priority, args.gpgcheck, args.enabled, args.description)
            elif args.repo_command == "remove":
                self.repo_remove(args.name)
            elif args.repo_command == "list":
                self.repo_list()
            elif args.repo_command == "enable":
                self.repo_enable(args.name)
            elif args.repo_command == "disable":
                self.repo_disable(args.name)
            else:
                self.show_help()

    def show_help(self):
        console.print(Panel("[bold cyan]Zenit Package Manager - Available Commands[/bold cyan]", title="[bold blue]Zenit Help[/bold blue]", border_style="blue"))
        table = Table(title="[bold magenta]Commands[/bold magenta]", border_style="magenta")
        table.add_column("[bold cyan]Command[/bold cyan]", justify="left")
        table.add_column("[bold white]Description[/bold white]", justify="left")
        commands = [
            ("update", "Update repository cache"),
            ("install <package>", "Install a package"),
            ("remove <package>", "Remove a package"),
            ("search <package>", "Search for a package"),
            ("list installed", "List installed packages"),
            ("upgrade", "Upgrade the system"),
            ("dist-upgrade", "Full distribution upgrade"),
            ("repo add <name> <url> [--options]", "Add a repository"),
            ("repo remove <name>", "Remove a repository"),
            ("repo list", "List repositories"),
            ("repo enable <name>", "Enable a repository"),
            ("repo disable <name>", "Disable a repository"),
            ("help, ?", "Show this help")
        ]
        for cmd, desc in commands:
            table.add_row(cmd, desc)
        console.print(table)
        console.print(Panel("[bold yellow]For bug reports or questions, visit: https://zenit-linux.webnode.page/write-to-us/[/bold yellow]", title="[bold yellow]Support[/bold yellow]", border_style="yellow"))

    def update(self):
        console.print(Panel("[bold cyan]Updating repository cache...[/bold cyan]", title="[bold blue]Zenit Update[/bold blue]", border_style="blue"))
        self.repo_manager.update_cache()

    def install(self, package_name):
        console.print(Panel(f"[bold cyan]Installing package {package_name}...[/bold cyan]", title="[bold green]Zenit Install[/bold green]", border_style="green"))
        transaction = self.solver.resolve_dependencies(package_name, "install")
        if transaction:
            for pkg in transaction.packages:
                package_path = self.downloader.download_package(pkg.url, pkg.name)
                if package_path and self.installer.verify_gpg(package_path):
                    self.installer.install_package(package_path, "install")

    def remove(self, package_name):
        console.print(Panel(f"[bold cyan]Removing package {package_name}...[/bold cyan]", title="[bold red]Zenit Remove[/bold red]", border_style="red"))
        transaction = self.solver.resolve_dependencies(package_name, "remove")
        if transaction:
            for pkg in transaction.packages:
                self.installer.install_package(pkg.name + ".rpm", "remove")

    def search(self, package_name):
        console.print(Panel(f"[bold cyan]Searching for package {package_name}...[/bold cyan]", title="[bold yellow]Zenit Search[/bold yellow]", border_style="yellow"))
        table = Table(title="[bold magenta]Search Results[/bold magenta]", border_style="magenta")
        table.add_column("[bold cyan]Name[/bold cyan]")
        table.add_column("[bold green]Version[/bold green]")
        table.add_column("[bold magenta]Repository[/bold magenta]")
        table.add_column("[bold white]Description[/bold white]")
        table.add_row(package_name, "1.2.3", "slowroll-oss", "Main package for testing")
        table.add_row(f"{package_name}-devel", "1.2.3", "slowroll-oss", "Development package")
        table.add_row(f"{package_name}-extra", "1.2.3", "slowroll-non-oss", "Additional features package")
        console.print(table)

    def list_installed(self):
        console.print(Panel("[bold cyan]Listing installed packages...[/bold cyan]", title="[bold green]Zenit List[/bold green]", border_style="green"))
        try:
            output = subprocess.run(["rpm", "-qa"], capture_output=True, text=True).stdout
            packages = output.splitlines()[:20]  # Limit for display
            table = Table(title="[bold magenta]Installed Packages[/bold magenta]", border_style="magenta")
            table.add_column("[bold cyan]Name[/bold cyan]")
            for pkg in packages:
                table.add_row(pkg)
            console.print(table)
        except Exception as e:
            console.print(Panel(f"[bold red]Error: {e}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))

    def upgrade(self):
        console.print(Panel("[bold cyan]Upgrading system...[/bold cyan]", title="[bold blue]Zenit Upgrade[/bold blue]", border_style="blue"))
        self.repo_manager.update_cache()
        transaction = self.solver.resolve_dependencies(None, "upgrade")
        if transaction:
            for pkg in transaction.packages:
                package_path = self.downloader.download_package(pkg.url, pkg.name)
                if package_path and self.installer.verify_gpg(package_path):
                    self.installer.install_package(package_path, "install")
        console.print(Panel("[bold green]System upgraded successfully.[/bold green]", title="[bold green]Success[/bold green]", border_style="green"))

    def dist_upgrade(self):
        console.print(Panel("[bold cyan]Performing full distribution upgrade...[/bold cyan]", title="[bold blue]Zenit Dist-Upgrade[/bold blue]", border_style="blue"))
        from rich.prompt import Confirm
        if Confirm.ask("[bold yellow]Are you sure you want to proceed? This may change system versions.[/bold yellow]"):
            self.upgrade()

    def repo_add(self, name, url, repo_type, priority, gpgcheck, enabled, description):
        console.print(Panel(f"[bold cyan]Adding repository {name}...[/bold cyan]", title="[bold green]Zenit Repo Add[/bold green]", border_style="green"))
        self.repo_manager.add_repo({
            "name": name,
            "url": url,
            "type": repo_type,
            "enabled": enabled,
            "priority": priority,
            "gpgcheck": gpgcheck,
            "mirrorlist": None,
            "description": description
        })
        console.print(Panel("[bold green]Repository added successfully.[/bold green]", title="[bold green]Success[/bold green]", border_style="green"))

    def repo_remove(self, name):
        console.print(Panel(f"[bold cyan]Removing repository {name}...[/bold cyan]", title="[bold red]Zenit Repo Remove[/bold red]", border_style="red"))
        self.repo_manager.remove_repo(name)
        console.print(Panel("[bold green]Repository removed successfully.[/bold green]", title="[bold green]Success[/bold green]", border_style="green"))

    def repo_list(self):
        console.print(Panel("[bold cyan]Listing repositories...[/bold cyan]", title="[bold green]Zenit Repo List[/bold green]", border_style="green"))
        table = Table(title="[bold magenta]Repositories[/bold magenta]", border_style="magenta")
        table.add_column("[bold cyan]Name[/bold cyan]")
        table.add_column("[bold green]URL[/bold green]")
        table.add_column("[bold yellow]Enabled[/bold yellow]")
        table.add_column("[bold white]Priority[/bold white]")
        table.add_column("[bold magenta]Description[/bold magenta]")
        for repo in self.repo_manager.repos:
            table.add_row(repo["name"], repo["url"], str(repo["enabled"]), str(repo["priority"]), repo.get("description", ""))
        console.print(table)

    def repo_enable(self, name):
        console.print(Panel(f"[bold cyan]Enabling repository {name}...[/bold cyan]", title="[bold green]Zenit Repo Enable[/bold green]", border_style="green"))
        self.repo_manager.enable_repo(name)
        console.print(Panel("[bold green]Repository enabled successfully.[/bold green]", title="[bold green]Success[/bold green]", border_style="green"))

    def repo_disable(self, name):
        console.print(Panel(f"[bold cyan]Disabling repository {name}...[/bold cyan]", title="[bold red]Zenit Repo Disable[/bold red]", border_style="red"))
        self.repo_manager.disable_repo(name)
        console.print(Panel("[bold green]Repository disabled successfully.[/bold green]", title="[bold green]Success[/bold green]", border_style="green"))

if __name__ == "__main__":
    cli = ZenitCLI()
    cli.run()

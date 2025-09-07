import solv
from rich.console import Console
from rich.panel import Panel
import os
import xml.etree.ElementTree as ET

console = Console(highlight=True, style="bold white on black")

class Solver:
    def __init__(self, repos):
        self.pool = solv.Pool()
        self.pool.setarch()
        self.cache_dir = "/var/cache/zenit"
        self.repos = repos
        self.repo_urls = {}  # Store repo URLs for package downloading
        for repo in self.repos:
            if repo["enabled"]:
                repo_handle = self.add_repo(repo)
                if repo_handle:
                    self.repo_urls[repo["name"]] = repo["url"]

    def add_repo(self, repo):
        repo_handle = self.pool.add_repo(repo["name"])
        repomd_path = os.path.join(self.cache_dir, repo["name"], "repomd.xml")
        if not os.path.exists(repomd_path):
            console.print(Panel(f"[bold yellow]Warning: Metadata file {repomd_path} not found. Skipping repository {repo['name']}.[/bold yellow]", title="[bold yellow]Warning[/bold yellow]", border_style="yellow"))
            return None
        try:
            # Use solv.xfopen for compatibility with libsolv
            f = solv.xfopen(repomd_path)
            repo_handle.add_repomdxml(f, 0)
            solv.xfclose(f)
            console.print(f"[bold blue]Added repomd.xml for {repo['name']} to solver[/bold blue]")
        except Exception as e:
            console.print(Panel(f"[bold red]Error adding repomd.xml for repository {repo['name']}: {e}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
            return None
        # Parse repomd.xml to load primary, filelists, other
        try:
            tree = ET.parse(repomd_path)
            root = tree.getroot()
            ns = {'repo': 'http://linux.duke.edu/metadata/repo'}
            for data in root.findall('repo:data', ns):
                type_ = data.get('type')
                if type_ in ['primary', 'filelists', 'other']:
                    location = data.find('repo:location', ns).get('href')
                    file_name = os.path.basename(location)
                    file_path = os.path.join(self.cache_dir, repo["name"], file_name)
                    if not os.path.exists(file_path):
                        console.print(f"[bold yellow]Warning: Metadata file {file_name} not found for {repo['name']}. Skipping.[/bold yellow]")
                        continue
                    f = solv.xfopen(file_path)
                    repo_handle.add_rpmmd(f, type_, 0)
                    solv.xfclose(f)
                    console.print(f"[bold blue]Added {type_} metadata for {repo['name']} to solver[/bold blue]")
        except Exception as e:
            console.print(Panel(f"[bold red]Error loading additional metadata for {repo['name']}: {e}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
        return repo_handle

    def search_packages(self, package_name):
        self.pool.createwhatprovides()
        selection = self.pool.Selection()
        for pkg in self.pool.select(str(package_name), solv.Selection.SELECTION_NAME | solv.Selection.SELECTION_GLOB).solvables():
            selection.add(pkg)
        return selection.solvables()

    def resolve_dependencies(self, package_name=None, action="install"):
        console.print(Panel(f"[bold yellow]Resolving dependencies for {action} {package_name or 'system'}...[/bold yellow]", title="[bold yellow]Solver[/bold yellow]", border_style="yellow"))
        self.pool.createwhatprovides()
        if action == "install":
            if not package_name:
                console.print(Panel("[bold red]Package name required for install action.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
                return None
            name_id = self.pool.str2id(package_name, 1)  # Convert package name to Id
            job = self.pool.Job(solv.Job.SOLVER_INSTALL | solv.Job.SOLVER_SOLVABLE_NAME, name_id)
        elif action == "remove":
            if not package_name:
                console.print(Panel("[bold red]Package name required for remove action.[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
                return None
            name_id = self.pool.str2id(package_name, 1)  # Convert package name to Id
            job = self.pool.Job(solv.Job.SOLVER_ERASE | solv.Job.SOLVER_SOLVABLE_NAME, name_id)
        elif action in ["upgrade", "dist-upgrade"]:
            job = self.pool.Job(solv.Job.SOLVER_UPDATE, 0)
        else:
            console.print(Panel(f"[bold red]Invalid action: {action}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
            return None
        solver = self.pool.Solver()
        problems = solver.solve([job])
        if problems:
            console.print(Panel(f"[bold red]Dependency problems: {problems}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
            return None
        transaction = solver.transaction()
        console.print(f"[bold green]Found {len(transaction.newsolvables())} packages to process.[/bold green]")
        return transaction

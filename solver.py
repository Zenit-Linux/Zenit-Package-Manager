import solv  # Assuming Python binding
from rich.console import Console
from rich.panel import Panel

console = Console(highlight=True, style="bold white on black")

class Solver:
    def __init__(self, repos):
        self.pool = solv.Pool()
        self.pool.setarch()
        for repo in repos:
            if repo["enabled"]:
                self.add_repo(repo)

    def add_repo(self, repo):
        repo_handle = self.pool.add_repo(repo["name"])
        repo_handle.add_rpmmd(f"/var/cache/zenit/{repo['name']}/repomd.xml", None)
        return repo_handle

    def resolve_dependencies(self, package_name=None, action="install"):
        console.print(Panel(f"[bold yellow]Resolving dependencies for {action} {package_name or 'system'}...[/bold yellow]", title="[bold yellow]Solver[/bold yellow]", border_style="yellow"))
        self.pool.createwhatprovides()
        if action == "install":
            job = self.pool.Job(solv.Job.SOLVER_INSTALL | solv.Job.SOLVER_SOLVABLE_NAME, package_name)
        elif action == "remove":
            job = self.pool.Job(solv.Job.SOLVER_ERASE | solv.Job.SOLVER_SOLVABLE_NAME, package_name)
        elif action in ["upgrade", "dist-upgrade"]:
            job = self.pool.Job(solv.Job.SOLVER_UPDATE, None)
        else:
            return None
        solver = self.pool.Solver()
        problems = solver.solve([job])
        if problems:
            console.print(Panel(f"[bold red]Dependency problems: {problems}[/bold red]", title="[bold red]Error[/bold red]", border_style="red"))
            return None
        transaction = solver.get_transaction()
        console.print(f"[bold green]Found {len(transaction.packages)} packages to process.[/bold green]")
        return transaction

"""FORGE Command Line Interface."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from forge.adapters.registry import get_adapter_registry
from forge.core.application_service import ApplicationService
from forge.core.doctor import DiagnosticStatus, Doctor
from forge.core.manifest_service import get_manifest_service
from forge.domain.execution import TestRunStatus
from forge.persistence.audit_journal import AuditJournal
from forge.persistence.migrations import apply_migrations

app = typer.Typer(
    name="forge",
    help="FORGE: Local-first AI integration development desktop platform.",
    no_args_is_help=True,
)
console = Console()

project_app = typer.Typer(help="Manage FORGE workspace projects.")
manifest_app = typer.Typer(help="Inspect and validate integration manifests.")
adapter_app = typer.Typer(help="Discover and inspect application adapters.")
build_app = typer.Typer(help="List and inspect connector package builds.")
audit_app = typer.Typer(help="Query and verify the cryptographic audit trail.")
approvals_app = typer.Typer(help="List and inspect tool execution approval requests.")

app.add_typer(project_app, name="project")
app.add_typer(manifest_app, name="manifest")
app.add_typer(adapter_app, name="adapter")
app.add_typer(build_app, name="build")
app.add_typer(audit_app, name="audit")
app.add_typer(approvals_app, name="approvals")


@app.callback()
def main_callback():
    """Ensure database migrations are applied upon invocation."""
    try:
        apply_migrations()
    except Exception as exc:
        console.print(f"[yellow]Warning: DB migration initialization: {exc}[/yellow]")


@app.command(name="gui")
def launch_gui():
    """Launch the PySide6 Desktop User Interface."""
    console.print("[green]Launching FORGE Desktop GUI...[/green]")
    from forge.ui.app import main as gui_main

    gui_main()


@app.command(name="doctor")
def run_doctor(
    workspace: Annotated[
        Optional[Path], typer.Option("--workspace", "-w", help="Workspace path to check")
    ] = None,
):
    """Run environment and installation diagnostic checks."""
    doctor = Doctor()
    report = doctor.run_diagnostics(workspace)

    table = Table(title="FORGE Doctor Diagnostics", show_lines=True)
    table.add_column("Status", justify="center", width=8)
    table.add_column("Check", style="bold", width=30)
    table.add_column("Message")

    for check in report.checks:
        status_color = {
            DiagnosticStatus.PASS: "green",
            DiagnosticStatus.WARN: "yellow",
            DiagnosticStatus.FAIL: "red",
        }[check.status]
        table.add_row(
            f"[{status_color}]{check.status.value}[/{status_color}]",
            check.name,
            check.message,
        )

    console.print(table)

    if report.overall_status == DiagnosticStatus.FAIL:
        console.print(
            "[bold red]Doctor check failed. Please resolve reported errors above.[/bold red]"
        )
        raise typer.Exit(code=1) from None
    elif report.overall_status == DiagnosticStatus.WARN:
        console.print("[bold yellow]Doctor check passed with warnings.[/bold yellow]")
    else:
        console.print(
            "[bold green]System check passed! All core components operational.[/bold green]"
        )


@project_app.command("create")
def project_create(
    path: Annotated[Path, typer.Argument(help="Path to create project directory")],
    name: Annotated[
        str, typer.Option("--name", "-n", help="Display name of the project")
    ] = "New Project",
    manifest: Annotated[
        Optional[Path], typer.Option("--manifest", "-m", help="Initial manifest to copy")
    ] = None,
):
    """Create a new FORGE project workspace."""
    svc = ApplicationService()
    try:
        proj = svc.create_project(path, name, manifest)
        console.print(
            f"[bold green]Project created successfully:[/bold green] {proj.name} ({proj.id})"
        )
        console.print(f"Workspace: {proj.workspace_path}")
        console.print(f"Manifest: {proj.manifest_path}")
    except Exception as exc:
        console.print(f"[red]Failed to create project:[/red] {exc}")
        raise typer.Exit(code=1) from None


@project_app.command("list")
def project_list():
    """List all registered FORGE projects."""
    svc = ApplicationService()
    projects = svc.list_projects()
    if not projects:
        console.print("[dim]No projects registered yet.[/dim]")
        return

    table = Table(title="FORGE Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Workspace")
    table.add_column("Updated At")

    for p in projects:
        table.add_row(p.id[:8], p.name, p.workspace_path, p.updated_at[:19])

    console.print(table)


@manifest_app.command("validate")
def manifest_validate(
    path: Annotated[Path, typer.Argument(help="Path to manifest.yaml or manifest.json")],
):
    """Validate an integration manifest against schema and domain rules."""
    ms = get_manifest_service()
    try:
        manifest = ms.load_and_validate(path)
        console.print(
            f"[bold green]Manifest valid:[/bold green] {manifest.integration.id} v{manifest.integration.version}"
        )
        console.print(
            f"Application: {manifest.application.display_name} ({manifest.application.id})"
        )
        console.print(f"Adapter: {manifest.adapter.id} v{manifest.adapter.version}")
        console.print(f"Declared capabilities ({len(manifest.capabilities)}):")
        for cap in manifest.capabilities:
            console.print(f" - [cyan]{cap.name}[/cyan] ({cap.risk.value}): {cap.description}")
    except Exception as exc:
        console.print(f"[bold red]Manifest validation failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


@adapter_app.command("list")
def adapter_list():
    """List all available application adapters."""
    reg = get_adapter_registry()
    adapters = reg.list_adapters()
    table = Table(title="Registered Adapters")
    table.add_column("Adapter ID", style="cyan")
    table.add_column("Version")
    table.add_column("App ID", style="bold")
    table.add_column("Status")
    table.add_column("Capabilities")

    for ad in adapters:
        detection = ad.detect_application()
        status_str = (
            f"[{'green' if detection.get('available') else 'yellow'}]{detection.get('status')}[/]"
        )
        caps = len(ad.list_capabilities())
        table.add_row(ad.id, ad.version, ad.supported_app_id, status_str, str(caps))

    console.print(table)


@adapter_app.command("inspect")
def adapter_inspect(
    adapter_id: Annotated[str, typer.Argument(help="Identifier of the adapter to inspect")],
):
    """Inspect detailed capabilities and handlers of an adapter."""
    reg = get_adapter_registry()
    try:
        adapter = reg.get_adapter(adapter_id)
    except Exception as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from None

    detection = adapter.detect_application()
    console.print(
        Panel(
            f"Adapter: [bold]{adapter.id}[/bold] v{adapter.version}\nTarget App: {adapter.supported_app_id}\nStatus: {detection.get('message')}"
        )
    )

    table = Table(title=f"Capabilities in {adapter.id}")
    table.add_column("Name", style="cyan")
    table.add_column("Handler", style="dim")
    table.add_column("Risk")
    table.add_column("Timeout (s)", justify="right")
    table.add_column("Description")

    for cap in adapter.list_capabilities():
        risk_color = {
            "read": "green",
            "write": "yellow",
            "destructive": "red",
            "external": "magenta",
        }.get(cap.risk.value, "white")
        table.add_row(
            cap.name,
            cap.handler,
            f"[{risk_color}]{cap.risk.value}[/{risk_color}]",
            str(cap.timeout_seconds),
            cap.description,
        )

    console.print(table)


@app.command("generate")
def generate_connector(
    manifest_path: Annotated[Path, typer.Argument(help="Path to valid manifest.yaml")],
    workspace: Annotated[Path, typer.Option("--workspace", "-w", help="Workspace path")] = Path(
        "."
    ),
):
    """Generate a runnable MCP connector package from an integration manifest."""
    svc = ApplicationService()
    ws = Path(workspace).resolve()
    try:
        proj = svc.open_project(ws)
        build = svc.generate_connector(proj.id, ws, manifest_path)
        console.print(
            f"[bold green]Connector build generated successfully:[/bold green] Build ID: {build.id}"
        )
        console.print(f"Build output directory: {build.build_dir}")
        console.print(f"Generated source hash: {build.generated_source_hash[:16]}...")
        console.print(f"Files: {', '.join(build.files)}")
    except Exception as exc:
        console.print(f"[bold red]Generation failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


@build_app.command("list")
def build_list(
    workspace: Annotated[Path, typer.Option("--workspace", "-w", help="Workspace path")] = Path(
        "."
    ),
):
    """List connector builds for the current workspace."""
    svc = ApplicationService()
    ws = Path(workspace).resolve()
    proj = svc.open_project(ws)
    builds = svc.build_repo.list_by_project(proj.id)

    if not builds:
        console.print("[dim]No builds found for this project.[/dim]")
        return

    table = Table(title=f"Builds for {proj.name}")
    table.add_column("Build ID", style="cyan")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Created At")
    table.add_column("Directory")

    for b in builds:
        table.add_row(b.id[:8], b.version, b.status.value, b.created_at[:19], b.build_dir)

    console.print(table)


@app.command("inspect")
def inspect_build(
    build_id: Annotated[str, typer.Argument(help="Build ID (or prefix) to inspect")],
    workspace: Annotated[Path, typer.Option("--workspace", "-w", help="Workspace path")] = Path(
        "."
    ),
):
    """Inspect generated files, tools catalog, and metadata for a build."""
    svc = ApplicationService()
    build = svc.build_repo.get_by_id(build_id)
    if not build:
        # Check prefix match
        ws = Path(workspace).resolve()
        proj = svc.open_project(ws)
        all_builds = svc.build_repo.list_by_project(proj.id)
        matching = [b for b in all_builds if b.id.startswith(build_id)]
        if matching:
            build = matching[0]

    if not build:
        console.print(f"[red]Build '{build_id}' not found.[/red]")
        raise typer.Exit(code=1) from None

    console.print(
        Panel(
            f"Build ID: [bold]{build.id}[/bold]\nVersion: {build.version}\nStatus: {build.status.value}\nDir: {build.build_dir}"
        )
    )
    b_dir = Path(build.build_dir)
    tools_file = b_dir / "tools.json"
    if tools_file.is_file():
        with open(tools_file, "r", encoding="utf-8") as f:
            tools = json.load(f)
        table = Table(title="Generated Tools Catalog")
        table.add_column("Tool Name", style="cyan")
        table.add_column("Risk")
        table.add_column("Description")
        for t in tools:
            table.add_row(t["name"], t["risk"], t["description"])
        console.print(table)


@app.command("test")
def test_build(
    build_id: Annotated[str, typer.Argument(help="Build ID to test")],
    workspace: Annotated[Path, typer.Option("--workspace", "-w", help="Workspace path")] = Path(
        "."
    ),
    live_blender: Annotated[
        bool, typer.Option("--live-blender", help="Run live Blender scene test")
    ] = False,
):
    """Execute automated tests against a generated connector build."""
    svc = ApplicationService()
    build = svc.build_repo.get_by_id(build_id)
    if not build:
        ws = Path(workspace).resolve()
        proj = svc.open_project(ws)
        matching = [b for b in svc.build_repo.list_by_project(proj.id) if b.id.startswith(build_id)]
        if matching:
            build = matching[0]

    if not build:
        console.print(f"[red]Build '{build_id}' not found.[/red]")
        raise typer.Exit(code=1) from None

    ws = Path(workspace).resolve()
    console.print(
        f"[bold cyan]Running verification test suite for build {build.id[:8]}...[/bold cyan]"
    )

    # Run contract test
    contract_run = asyncio.run(svc.test_orchestrator.run_mcp_contract_tests(build, ws))

    # Run fixturelab e2e test if applicable
    e2e_run = svc.test_orchestrator.run_fixturelab_e2e(build, ws)

    # Run blender live test if requested
    blender_run = None
    if live_blender:
        blender_run = svc.test_orchestrator.run_blender_live_test(build, ws)

    runs = [("MCP Contract", contract_run), ("FixtureLab E2E", e2e_run)]
    if blender_run:
        runs.append(("Blender Live", blender_run))

    all_passed = True
    for suite_name, run in runs:
        table = Table(title=f"Suite: {suite_name} (Status: {run.status.value})")
        table.add_column("Test Case", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Duration (s)", justify="right")
        table.add_column("Notes")

        for tc in run.test_cases:
            color = {"passed": "green", "failed": "red", "skipped": "yellow"}.get(
                tc.status.value, "white"
            )
            table.add_row(
                tc.name,
                f"[{color}]{tc.status.value.upper()}[/{color}]",
                str(tc.duration_seconds),
                tc.error_message or tc.skip_reason or "",
            )
        console.print(table)
        if run.status == TestRunStatus.FAILED:
            all_passed = False

    if not all_passed:
        console.print("[bold red]One or more test suites failed.[/bold red]")
        raise typer.Exit(code=1) from None
    else:
        console.print("[bold green]All verification suites passed successfully![/bold green]")


@app.command("serve")
def serve_connector(
    build_id: Annotated[str, typer.Argument(help="Build ID to serve")],
    workspace: Annotated[Path, typer.Option("--workspace", "-w", help="Workspace path")] = Path(
        "."
    ),
):
    """Run the generated connector server in the foreground over stdio."""
    svc = ApplicationService()
    build = svc.build_repo.get_by_id(build_id)
    if not build:
        ws = Path(workspace).resolve()
        proj = svc.open_project(ws)
        matching = [b for b in svc.build_repo.list_by_project(proj.id) if b.id.startswith(build_id)]
        if matching:
            build = matching[0]

    if not build:
        console.print(f"[red]Build '{build_id}' not found.[/red]")
        raise typer.Exit(code=1) from None

    launcher = Path(build.build_dir) / "launcher.py"
    console.print(f"[green]Starting MCP server on stdio from {launcher}...[/green]")
    import os

    env = dict(os.environ)
    env["FORGE_WORKSPACE"] = str(Path(workspace).resolve())
    subprocess.run([sys.executable, str(launcher)], env=env)


@app.command("package")
def package_build(
    build_id: Annotated[str, typer.Argument(help="Build ID to package")],
    workspace: Annotated[Path, typer.Option("--workspace", "-w", help="Workspace path")] = Path(
        "."
    ),
):
    """Package a tested connector build into a standalone ZIP distribution archive."""
    svc = ApplicationService()
    build = svc.build_repo.get_by_id(build_id)
    if not build:
        ws = Path(workspace).resolve()
        proj = svc.open_project(ws)
        matching = [b for b in svc.build_repo.list_by_project(proj.id) if b.id.startswith(build_id)]
        if matching:
            build = matching[0]

    if not build:
        console.print(f"[red]Build '{build_id}' not found.[/red]")
        raise typer.Exit(code=1) from None

    try:
        pkg = svc.export_package(build.id, workspace)
        console.print(f"[bold green]Package exported successfully:[/bold green] {pkg.id}")
        console.print(f"Archive: {pkg.archive_path}")
        console.print(f"SHA-256: {pkg.sha256}")
        console.print(f"Size: {pkg.size_bytes} bytes")
    except Exception as exc:
        console.print(f"[bold red]Packaging failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from None


@audit_app.command("list")
def audit_list(
    workspace: Annotated[Path, typer.Option("--workspace", "-w", help="Workspace path")] = Path(
        "."
    ),
    limit: Annotated[int, typer.Option("--limit", "-l", help="Max events to display")] = 25,
):
    """Display the append-only audit journal."""
    journal = AuditJournal()
    events = journal.list_events(limit=limit)

    if not events:
        console.print("[dim]No audit events recorded yet.[/dim]")
        return

    table = Table(title="FORGE Audit Journal")
    table.add_column("ID", justify="right")
    table.add_column("Timestamp")
    table.add_column("Actor", style="cyan")
    table.add_column("Action", style="bold")
    table.add_column("Target")
    table.add_column("Outcome")
    table.add_column("Event Hash", style="dim")

    for e in events:
        outcome_color = {"success": "green", "denied": "yellow", "failed": "red"}.get(
            e.outcome, "white"
        )
        table.add_row(
            str(e.id),
            e.timestamp[:19],
            e.actor,
            e.action,
            e.target,
            f"[{outcome_color}]{e.outcome}[/{outcome_color}]",
            e.event_hash[:12] + "...",
        )

    console.print(table)


@audit_app.command("verify")
def audit_verify(
    workspace: Annotated[Path, typer.Option("--workspace", "-w", help="Workspace path")] = Path(
        "."
    ),
):
    """Verify cryptographic hash-chain integrity of the audit journal."""
    journal = AuditJournal()
    is_valid, msg, broken_id = journal.verify_integrity()

    if is_valid:
        console.print(f"[bold green]INTEGRITY OK:[/bold green] {msg}")
    else:
        console.print(f"[bold red]TAMPERING DETECTED at record {broken_id}:[/bold red] {msg}")
        raise typer.Exit(code=1) from None


@approvals_app.command("list")
def approvals_list(
    workspace: Annotated[Path, typer.Option("--workspace", "-w", help="Workspace path")] = Path(
        "."
    ),
):
    """List pending and recent approval grants."""
    svc = ApplicationService()
    pending = svc.list_pending_approvals()
    recent = svc.approval_repo.list_recent(limit=20)

    if pending:
        console.print("[bold yellow]Pending Approval Requests:[/bold yellow]")
        for req in pending:
            console.print(
                f"Request {req['request_id'][:8]} | Tool: {req['tool_name']} | Args Hash: {req['argument_hash'][:12]}"
            )
    else:
        console.print("[dim]No pending approval requests.[/dim]")

    if recent:
        table = Table(title="Recent Approval Grants")
        table.add_column("ID", style="cyan")
        table.add_column("Tool Name", style="bold")
        table.add_column("Arg Hash", style="dim")
        table.add_column("Granted At")
        table.add_column("Consumed")

        for g in recent:
            table.add_row(
                g.id[:8],
                g.tool_name,
                g.argument_hash[:12],
                g.granted_at[:19],
                "[green]YES[/green]" if g.consumed else "[yellow]NO[/yellow]",
            )
        console.print(table)


if __name__ == "__main__":
    app()

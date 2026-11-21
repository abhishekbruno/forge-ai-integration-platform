"""Packaging and distribution exporter for tested MCP connectors."""

from __future__ import annotations

import zipfile
from pathlib import Path
from uuid import uuid4

from forge.domain.project import Build, PackageMetadata
from forge.events.bus import get_event_bus
from forge.events.models import EVENT_PACKAGE_EXPORTED, ForgeEvent
from forge.persistence.audit_journal import AuditJournal
from forge.persistence.repositories import PackageRepository
from forge.security.hashes import hash_file


class PackageExporter:
    """Exports and verifies standalone distributable ZIP packages of generated connectors."""

    def __init__(self, db_path: Path | None = None):
        self.repo = PackageRepository(db_path)
        self.audit_journal = AuditJournal(db_path)

    def export_package(self, build: Build, workspace_path: Path | str) -> PackageMetadata:
        """Create a clean, self-contained ZIP archive of the tested build."""
        ws = Path(workspace_path).resolve()
        build_dir = Path(build.build_dir).resolve()
        if not build_dir.is_dir():
            raise FileNotFoundError(f"Build directory does not exist: {build_dir}")

        packages_dir = ws / ".forge" / "packages"
        packages_dir.mkdir(parents=True, exist_ok=True)

        package_id = str(uuid4())
        archive_name = f"connector-{build.version}-{build.id[:8]}.zip"
        archive_path = packages_dir / archive_name

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for item in sorted(build_dir.iterdir()):
                if item.is_file():
                    # Write relative to root of archive
                    zf.write(item, arcname=item.name)

        archive_hash = hash_file(archive_path)
        archive_size = archive_path.stat().st_size

        pkg = PackageMetadata(
            id=package_id,
            build_id=build.id,
            version=build.version,
            archive_path=str(archive_path),
            sha256=archive_hash,
            size_bytes=archive_size,
            verified=True,
        )

        self.repo.save(pkg)

        self.audit_journal.record_event(
            action="package.export",
            target=f"{build.id}:{package_id}",
            outcome="success",
            correlation_id=package_id,
            details={"sha256": archive_hash, "size_bytes": archive_size, "path": str(archive_path)},
        )

        get_event_bus().publish(
            ForgeEvent(
                name=EVENT_PACKAGE_EXPORTED,
                correlation_id=package_id,
                details=pkg.model_dump(),
            )
        )

        return pkg

    def verify_package(self, package_path: Path | str) -> tuple[bool, str, list[str]]:
        """Verify archive integrity, absence of path traversal (zip-slip), and presence of key files."""
        path = Path(package_path).resolve()
        if not path.is_file():
            return False, f"Package file does not exist: {path}", []

        extracted_names = []
        try:
            with zipfile.ZipFile(path, "r") as zf:
                for member in zf.namelist():
                    # Check for zip slip
                    if member.startswith("/") or member.startswith("\\") or ".." in member:
                        return (
                            False,
                            f"Zip-slip path traversal attempt in archive member '{member}'",
                            [],
                        )
                    extracted_names.append(member)

            required_files = {
                "server.py",
                "launcher.py",
                "pyproject.toml",
                "README.md",
                "tools.json",
            }
            missing = required_files - set(extracted_names)
            if missing:
                return (
                    False,
                    f"Archive missing required connector files: {missing}",
                    extracted_names,
                )

            return True, "Package integrity and structure verified successfully.", extracted_names
        except Exception as exc:
            return False, f"Corrupted or invalid zip archive: {exc}", []

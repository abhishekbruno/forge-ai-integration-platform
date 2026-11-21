"""Unit tests for deterministic connector generator."""

from pathlib import Path

from forge.core.generator import ConnectorGenerator
from forge.core.manifest_service import ManifestService


def test_deterministic_generator(temp_workspace):
    svc = ManifestService()
    manifest = svc.load_and_validate(Path("manifests/fixturelab.yaml"))

    gen = ConnectorGenerator()
    out_dir_1 = temp_workspace / "gen1"
    out_dir_2 = temp_workspace / "gen2"

    files_1 = gen.generate(manifest, out_dir_1, temp_workspace, build_id="fixed-build-id")
    files_2 = gen.generate(manifest, out_dir_2, temp_workspace, build_id="fixed-build-id")

    # Ensure same files generated
    assert set(files_1.keys()) == set(files_2.keys())

    # Ensure identical content hashes for deterministic files
    for fname in ["pyproject.toml", "tools.json", "policy.json", "launcher.py"]:
        assert files_1[fname] == files_2[fname]

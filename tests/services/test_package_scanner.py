import json
from pathlib import Path

from fs24_mod_manager.models.package_info import PackageStatus
from fs24_mod_manager.services.package_scanner import PackageScanner


def _package(root: Path, name: str, title: str = "Test") -> Path:
    path = root / name
    path.mkdir()
    (path / "manifest.json").write_text(
        json.dumps({"title": title, "package_version": "1.2.3", "creator": "Creator"}),
        encoding="utf-8",
    )
    (path / "layout.json").write_text("{}", encoding="utf-8")
    return path


def test_scan_reads_direct_packages_and_excludes_application(tmp_path: Path) -> None:
    community, disabled = tmp_path / "Community", tmp_path / "Community_disabled"
    community.mkdir()
    disabled.mkdir()
    _package(community, "alpha", "Alpha")
    application = _package(community, "manager", "Manager")
    packages = PackageScanner(application).scan(community, disabled)
    assert [(item.title, item.version, item.status) for item in packages] == [
        ("Alpha", "1.2.3", PackageStatus.ENABLED)
    ]


def test_scan_marks_case_insensitive_conflicts(tmp_path: Path) -> None:
    community, disabled = tmp_path / "Community", tmp_path / "Community_disabled"
    community.mkdir()
    disabled.mkdir()
    _package(community, "Same")
    _package(disabled, "same")
    packages = PackageScanner(tmp_path / "app").scan(community, disabled)
    assert len(packages) == 2
    assert all(item.status is PackageStatus.CONFLICTED for item in packages)


def test_scan_reports_malformed_manifest_as_invalid(tmp_path: Path) -> None:
    community, disabled = tmp_path / "Community", tmp_path / "Community_disabled"
    community.mkdir()
    disabled.mkdir()
    broken = community / "broken"
    broken.mkdir()
    (broken / "manifest.json").write_text("not json", encoding="utf-8")
    (broken / "layout.json").write_text("{}", encoding="utf-8")
    package = PackageScanner(tmp_path / "app").scan(community, disabled)[0]
    assert package.status is PackageStatus.INVALID
    assert package.diagnostic

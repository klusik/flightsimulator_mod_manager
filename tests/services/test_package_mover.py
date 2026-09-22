import json
from pathlib import Path

from fs24_mod_manager.models.package_info import PackageInfo, PackageStatus
from fs24_mod_manager.services.package_mover import PackageMover
from fs24_mod_manager.services.path_validator import PathValidator


def _enabled_package(root: Path) -> PackageInfo:
    path = root / "sample"
    path.mkdir()
    (path / "manifest.json").write_text(json.dumps({"title": "Sample"}), encoding="utf-8")
    (path / "layout.json").write_text("{}", encoding="utf-8")
    return PackageInfo("sample", path, "Sample", "", "", "", PackageStatus.ENABLED)


def test_disable_moves_and_verifies_package(tmp_path: Path) -> None:
    community, disabled = tmp_path / "Community", tmp_path / "Community_disabled"
    community.mkdir()
    disabled.mkdir()
    package = _enabled_package(community)
    result = PackageMover(PathValidator(), tmp_path / "app").move(package, community, disabled)
    assert result.success
    assert not package.path.exists()
    assert (disabled / "sample" / "manifest.json").is_file()


def test_move_refuses_destination_collision(tmp_path: Path) -> None:
    community, disabled = tmp_path / "Community", tmp_path / "Community_disabled"
    community.mkdir()
    disabled.mkdir()
    package = _enabled_package(community)
    (disabled / "sample").mkdir()
    result = PackageMover(PathValidator(), tmp_path / "app").move(package, community, disabled)
    assert not result.success
    assert package.path.exists()

import json
from pathlib import Path

from fs24_mod_manager.models.user_settings import UserSettings
from fs24_mod_manager.services.settings_store import SettingsStore


def test_settings_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    store = SettingsStore(path)
    expected = UserSettings(tmp_path / "Community", tmp_path / "Community_disabled", "900x600")
    store.save(expected)
    actual = store.load()
    assert actual == expected


def test_invalid_settings_are_preserved(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"settings_version": 999}), encoding="utf-8")
    settings = SettingsStore(path).load()
    assert settings.community_path is None
    assert not path.exists()
    assert len(list(tmp_path.glob("settings.*.invalid.json"))) == 1

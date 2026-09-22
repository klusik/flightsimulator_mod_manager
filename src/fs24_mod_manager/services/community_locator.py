"""Flight Simulator Community directory discovery."""

import os
import re
from pathlib import Path


class CommunityLocator:
    """Find credible Community directory candidates from UserCfg files."""

    _PATH_PATTERN = re.compile(r'^\s*InstalledPackagesPath\s+["\']?(.*?)["\']?\s*$')

    def discover(self, saved: Path | None = None) -> list[Path]:
        """Return unique validated candidates in priority order.

        @param saved: Previously confirmed Community path.
        @return: Existing Community directories.
        """
        candidates: list[Path] = []
        if saved and saved.is_dir():
            candidates.append(saved.resolve())
        for config_path in self._user_config_candidates():
            installed = self._read_installed_path(config_path)
            if installed:
                candidate = installed / "Community"
                if candidate.is_dir():
                    candidates.append(candidate.resolve())
        unique: dict[str, Path] = {}
        for candidate in candidates:
            unique.setdefault(str(candidate).casefold(), candidate)
        return list(unique.values())

    def suggested_disabled_path(self, community: Path) -> Path:
        """Create the default sibling disabled path.

        @param community: Selected Community directory.
        @return: Suggested disabled root.
        """
        return community.with_name(f"{community.name}_disabled")

    def _user_config_candidates(self) -> list[Path]:
        """Return known FS24 user configuration locations.

        @return: Candidate configuration files.
        """
        appdata = Path(os.environ.get("APPDATA", ""))
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        return [
            appdata / "Microsoft Flight Simulator 2024" / "UserCfg.opt",
            local / "Packages" / "Microsoft.Limitless_8wekyb3d8bbwe" / "LocalCache" / "UserCfg.opt",
        ]

    def _read_installed_path(self, config_path: Path) -> Path | None:
        """Parse `InstalledPackagesPath` from one configuration file.

        @param config_path: UserCfg file to parse.
        @return: Installed packages root or `None`.
        """
        try:
            for line in config_path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                match = self._PATH_PATTERN.match(line)
                if match:
                    return Path(match.group(1).strip())
        except OSError:
            return None
        return None

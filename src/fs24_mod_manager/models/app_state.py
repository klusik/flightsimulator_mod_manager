"""Current application state model."""

from dataclasses import dataclass, field

from fs24_mod_manager.models.operation_result import OperationResult
from fs24_mod_manager.models.package_info import PackageInfo
from fs24_mod_manager.models.user_settings import UserSettings


@dataclass(slots=True)
class AppState:
    """Hold the replaceable in-memory snapshot displayed by the view."""

    settings: UserSettings
    packages: list[PackageInfo] = field(default_factory=list)
    scan_generation: int = 0
    busy: bool = False
    latest_results: list[OperationResult] = field(default_factory=list)

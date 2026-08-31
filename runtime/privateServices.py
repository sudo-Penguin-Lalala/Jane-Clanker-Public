from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from runtime.optionalImports import importOptionalModule


def _tryImportModule(moduleName: str, *, enabled: bool = True) -> Any | None:
    return importOptionalModule(moduleName, enabled=enabled)


class _DepartmentOrbatSheetsFallback:
    @staticmethod
    def hasConfiguredLayouts() -> bool:
        return False

    @staticmethod
    def touchupAllDepartmentSheets() -> dict[str, object]:
        return {"reason": "private extensions disabled", "results": {}}


class _OrbatSheetsFallback:
    @staticmethod
    def organizeOrbatRows() -> dict[str, object]:
        return {"reason": "private extensions disabled"}

    @staticmethod
    def incrementEventCount(*args, **kwargs) -> int:
        return 0


class _OrbatRoleSyncFallback:
    @staticmethod
    async def syncMemberRoleOrbats(*args, **kwargs) -> dict[str, object]:
        return {"changed": False, "results": []}


def _loadMultiOrbatRegistryFallback() -> dict[str, object]:
    return {}


@dataclass(slots=True)
class PrivateServices:
    privateExtensionsEnabled: bool
    departmentOrbatSheets: Any
    orbatSheets: Any
    orbatRoleSync: Any
    loadMultiOrbatRegistry: Callable[[], dict[str, object]]
    orbatAuditRuntime: Any | None
    serverSafetyService: Any | None
    gitUpdateModule: Any | None
    processControlModule: Any | None


def loadPrivateServices(*, configModule: Any) -> PrivateServices:
    privateExtensionsEnabled = bool(getattr(configModule, "enablePrivateExtensions", True))

    return PrivateServices(
        privateExtensionsEnabled=privateExtensionsEnabled,
        departmentOrbatSheets=_DepartmentOrbatSheetsFallback(),
        orbatSheets=_OrbatSheetsFallback(),
        orbatRoleSync=_OrbatRoleSyncFallback(),
        loadMultiOrbatRegistry=_loadMultiOrbatRegistryFallback,
        orbatAuditRuntime=None,
        serverSafetyService=None,
        gitUpdateModule=None,
        processControlModule=None,
    )


#!/usr/bin/env python3
"""Effect-free platform adapter for Haven 42 managed local setup."""

from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from typing import Any, FrozenSet

from windows_alpha import ResourceHistory, SessionTokenTotals, validate_provider_metrics


class PlatformAdapterError(ValueError):
    """The requested platform or platform operation is outside the release boundary."""


SHARED_PLATFORM_OPERATIONS: FrozenSet[str] = frozenset({
    "readiness.inspect",
    "provider.metrics.validate",
})
PLANNING_PLATFORM_OPERATIONS: FrozenSet[str] = frozenset({
    "component-registry.load",
    "driver.guidance",
    "hardware.evaluate",
    "model-catalog.load",
    "model.select",
    "setup.plan",
})
MANAGED_PLATFORM_OPERATIONS: FrozenSet[str] = frozenset({
    "component-registry.load",
    "driver.guidance",
    "hardware.evaluate",
    "model-catalog.load",
    "model.select",
    "setup.approve",
    "setup.execute",
    "setup.plan",
    "setup.remove",
    "setup.resume",
})


@dataclass(frozen=True)
class PlatformAdapter:
    """Immutable capability declaration; it never accepts commands or paths."""

    platform_id: str
    platform_family: str
    managed_setup_supported: bool
    supported_operations: FrozenSet[str]

    def require(self, operation_id: str) -> None:
        if not isinstance(operation_id, str) or operation_id not in self.supported_operations:
            raise PlatformAdapterError("unsupported-platform-operation")

    def public_summary(self) -> dict[str, Any]:
        return {
            "schemaVersion": 1,
            "platformId": self.platform_id,
            "platformFamily": self.platform_family,
            "managedSetupSupported": self.managed_setup_supported,
            "supportedOperations": sorted(self.supported_operations),
        }


SUPPORTED_PLATFORM_ADAPTERS = {
    platform_id: PlatformAdapter(
        platform_id=platform_id,
        platform_family=family,
        managed_setup_supported=True,
        supported_operations=SHARED_PLATFORM_OPERATIONS | MANAGED_PLATFORM_OPERATIONS,
    )
    for platform_id, family in (("windows-x64", "windows"), ("linux-x64", "linux"))
}
SUPPORTED_PLATFORM_ADAPTERS["macos-arm64"] = PlatformAdapter(
    platform_id="macos-arm64",
    platform_family="macos",
    managed_setup_supported=False,
    supported_operations=SHARED_PLATFORM_OPERATIONS | PLANNING_PLATFORM_OPERATIONS,
)


def resolve_platform_adapter(platform_id: str) -> PlatformAdapter:
    """Resolve only an exact compiled-in platform identifier."""
    if not isinstance(platform_id, str) or platform_id not in SUPPORTED_PLATFORM_ADAPTERS:
        raise PlatformAdapterError("unsupported-platform-adapter")
    return SUPPORTED_PLATFORM_ADAPTERS[platform_id]


def _active_adapter() -> PlatformAdapter:
    if os.name == "nt":
        return resolve_platform_adapter("windows-x64")
    if sys.platform.startswith("linux"):
        return resolve_platform_adapter("linux-x64")
    if sys.platform == "darwin":
        return resolve_platform_adapter("macos-arm64")
    return PlatformAdapter(
        platform_id="shared-ui-only",
        platform_family="unsupported",
        managed_setup_supported=False,
        supported_operations=SHARED_PLATFORM_OPERATIONS,
    )


ACTIVE_PLATFORM_ADAPTER = _active_adapter()


def require_platform_operation(operation_id: str) -> None:
    """Fail closed before a platform-specific operation is invoked."""
    ACTIVE_PLATFORM_ADAPTER.require(operation_id)


if os.name == "nt":
    MANAGED_SETUP_SUPPORTED = True
    from windows_alpha import (  # noqa: F401
        WindowsAlphaError as AlphaPlatformError,
        automatic_setup_admitted,
        driver_guidance,
        evaluate_hardware,
        load_component_registry,
        load_model_catalog,
        select_model,
    )
    from windows_alpha_setup import (  # noqa: F401
        COMPONENT_DECISION_CODES,
        MANAGED_OLLAMA_URL,
        MODEL_DECISION_CODES,
        SetupCoordinator,
        SetupError,
        build_plan,
    )
    build_resume_plan = build_plan
    resume_setup_admitted = automatic_setup_admitted
elif sys.platform.startswith("linux"):
    MANAGED_SETUP_SUPPORTED = True
    from linux_alpha import (  # noqa: F401
        LinuxAlphaError as AlphaPlatformError,
        driver_guidance,
        evaluate_hardware,
        build_resume_plan,
        load_catalog as load_model_catalog,
        load_registry as load_component_registry,
        resume_setup_admitted,
        select_model,
    )
    from linux_alpha import build_plan
    from linux_alpha_setup import (  # noqa: F401
        COMPONENT_DECISION_CODES,
        MANAGED_OLLAMA_URL,
        MODEL_DECISION_CODES,
        SetupCoordinator,
        SetupError,
    )

    def automatic_setup_admitted(selected_model: dict[str, Any], snapshot: dict[str, Any]) -> bool:
        """Confirm that the current evidence still selects this exact model."""
        decision = select_model(snapshot)
        selected = decision.get("selected")
        return (
            decision.get("automaticExecutionAllowed") is True
            and isinstance(selected, dict)
            and selected.get("id") == selected_model.get("id")
            and selected.get("manifestDigest") == selected_model.get("manifestDigest")
        )

else:
    # The shared application still builds on macOS, but managed Alpha 2 setup
    # is intentionally limited to the reviewed Windows and Linux targets.
    MANAGED_SETUP_SUPPORTED = False
    from windows_alpha import (  # noqa: F401
        WindowsAlphaError as AlphaPlatformError,
        automatic_setup_admitted,
        driver_guidance,
        evaluate_hardware,
        load_component_registry,
        load_model_catalog,
        select_model,
    )
    from windows_alpha_setup import (  # noqa: F401
        COMPONENT_DECISION_CODES,
        MANAGED_OLLAMA_URL,
        MODEL_DECISION_CODES,
        SetupCoordinator,
        SetupError,
        build_plan,
    )
    build_resume_plan = build_plan
    resume_setup_admitted = automatic_setup_admitted

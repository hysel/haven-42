#!/usr/bin/env python3
"""Effect-free platform adapter for Haven 42 managed local setup."""

from __future__ import annotations

import os
import sys
from typing import Any

from windows_alpha import ResourceHistory, SessionTokenTotals, validate_provider_metrics


if os.name == "nt":
    MANAGED_SETUP_SUPPORTED = True
    from windows_alpha import (  # noqa: F401
        WindowsAlphaError as AlphaPlatformError,
        automatic_setup_admitted,
        driver_guidance,
        evaluate_hardware,
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
elif sys.platform.startswith("linux"):
    MANAGED_SETUP_SUPPORTED = True
    from linux_alpha import (  # noqa: F401
        LinuxAlphaError as AlphaPlatformError,
        evaluate_hardware,
        load_catalog as load_model_catalog,
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

    def driver_guidance(snapshot: dict[str, Any]) -> dict[str, Any]:
        """Linux Alpha never changes drivers; provide a bounded user-facing state."""
        hardware = evaluate_hardware(snapshot)
        backend = hardware.get("managedBackendCandidate")
        blockers = hardware.get("blockers", [])
        if backend == "cuda":
            state = "ready"
            message = "The installed NVIDIA driver exposed a usable CUDA accelerator. Haven 42 will not change it."
        elif "nvidia-capacity-or-driver-unverified" in blockers:
            state = "action-required"
            message = "Install a driver recommended by your Linux distribution, then run the check again. Haven 42 does not install drivers."
        else:
            state = "not-required"
            message = "No graphics-driver change is required for the reviewed CPU setup."
        return {
            "decision": state,
            "message": message,
            "automaticInstallationAllowed": False,
            "consumerDriverRequired": False,
        }
else:
    # The shared application still builds on macOS, but managed Alpha 2 setup
    # is intentionally limited to the reviewed Windows and Linux targets.
    MANAGED_SETUP_SUPPORTED = False
    from windows_alpha import (  # noqa: F401
        WindowsAlphaError as AlphaPlatformError,
        automatic_setup_admitted,
        driver_guidance,
        evaluate_hardware,
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

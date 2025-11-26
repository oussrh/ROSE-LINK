"""
Setup Wizard API Routes
=======================

Endpoints for the first-time setup wizard.

Endpoints:
- GET /api/setup/status: Check if setup is required
- GET /api/setup/state: Get current setup state
- POST /api/setup/start: Start the setup wizard
- GET /api/setup/step/{step}: Get step data
- POST /api/setup/step/{step}: Submit step data
- POST /api/setup/complete: Complete the setup
- POST /api/setup/skip: Skip the setup (advanced users)
- POST /api/setup/reset: Reset setup (for testing)

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field

from services.setup_service import SetupService, SetupStep

logger = logging.getLogger("rose-link.api.setup")

router = APIRouter(prefix="/setup")


class StartSetupRequest(BaseModel):
    """Request model for starting setup."""
    language: str = Field(default="en", description="UI language (en, fr)")


class StepDataRequest(BaseModel):
    """Request model for step data submission."""
    data: dict = Field(default_factory=dict, description="Step-specific data")


VALID_STEPS = {s.value for s in SetupStep}


@router.get("/status")
async def get_status() -> dict[str, Any]:
    """
    Check if setup wizard is required.

    Returns:
        Setup status including whether setup is required
    """
    return SetupService.get_status()


@router.get("/state")
async def get_state() -> dict[str, Any]:
    """
    Get current setup wizard state.

    Returns:
        Complete setup state
    """
    state = SetupService.get_state()
    return state.to_dict()


@router.post("/start")
async def start_setup(
    request: StartSetupRequest = Body(default=StartSetupRequest()),
) -> dict[str, Any]:
    """
    Start the setup wizard.

    Args:
        request: Start configuration (language)

    Returns:
        Initial setup state
    """
    logger.info(f"Starting setup wizard, language: {request.language}")

    state = SetupService.start_setup(language=request.language)
    return {
        "status": "started",
        "state": state.to_dict(),
    }


@router.get("/step/{step}")
async def get_step_data(
    step: str = Path(..., description="Setup step name"),
) -> dict[str, Any]:
    """
    Get data needed for a specific setup step.

    Args:
        step: Step name (welcome, network, vpn, hotspot, security, adguard, summary)

    Returns:
        Step-specific data

    Raises:
        HTTPException 400: If invalid step name
    """
    if step not in VALID_STEPS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step: {step}. Valid steps: {', '.join(VALID_STEPS)}"
        )

    return SetupService.get_step_data(step)


@router.post("/step/{step}")
async def submit_step(
    step: str = Path(..., description="Setup step name"),
    request: StepDataRequest = Body(...),
) -> dict[str, Any]:
    """
    Submit data for a setup step.

    Args:
        step: Step name
        request: Step data

    Returns:
        Result with next step information

    Raises:
        HTTPException 400: If invalid step or data
        HTTPException 500: If step processing fails
    """
    if step not in VALID_STEPS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step: {step}"
        )

    logger.info(f"Processing setup step: {step}")

    result = SetupService.submit_step(step, request.data)

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Step processing failed")
        )

    return result


@router.post("/complete")
async def complete_setup() -> dict[str, Any]:
    """
    Complete the setup wizard.

    Finalizes configuration and marks setup as done.

    Returns:
        Completion result

    Raises:
        HTTPException 500: If completion fails
    """
    logger.info("Completing setup wizard")

    result = SetupService.complete_setup()

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Setup completion failed")
        )

    return result


@router.post("/skip")
async def skip_setup() -> dict[str, Any]:
    """
    Skip the setup wizard.

    For advanced users who want to configure manually.

    Returns:
        Skip result
    """
    logger.info("Skipping setup wizard")

    return SetupService.skip_setup()


@router.post("/reset")
async def reset_setup() -> dict[str, str]:
    """
    Reset the setup wizard.

    For testing or re-configuration. Requires re-running setup.

    Returns:
        Reset status
    """
    logger.info("Resetting setup wizard")

    success = SetupService.reset_setup()

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to reset setup"
        )

    return {"status": "reset"}

"""
Speed Test Routes
=================

Internet speed test endpoints.

Endpoints:
- GET /speedtest/status - Check if test is running
- POST /speedtest/run - Start a speed test
- GET /speedtest/history - Get test history
- GET /speedtest/last - Get last test result
- DELETE /speedtest/history - Clear test history

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from api.dependencies import require_auth
from services.speedtest_service import SpeedTestService

logger = logging.getLogger("rose-link.speedtest-routes")

router = APIRouter()


@router.get("/speedtest/status")
async def get_speedtest_status() -> Dict[str, Any]:
    """
    Check speed test status.

    Returns:
        Current status and last result if available
    """
    last_result = SpeedTestService.get_last_result()
    return {
        "is_running": SpeedTestService.is_test_running(),
        "last_result": last_result.to_dict() if last_result else None,
    }


@router.post("/speedtest/run", dependencies=[Depends(require_auth)])
async def run_speedtest(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Start a speed test.

    The test runs asynchronously. Poll /speedtest/status to check progress.

    Returns:
        Status indicating test started
    """
    if SpeedTestService.is_test_running():
        raise HTTPException(
            status_code=409,
            detail="A speed test is already running"
        )

    # Run test in background
    background_tasks.add_task(SpeedTestService.run_test)

    return {
        "status": "started",
        "message": "Speed test started. Check /speedtest/status for results.",
    }


@router.get("/speedtest/run-sync", dependencies=[Depends(require_auth)])
async def run_speedtest_sync() -> Dict[str, Any]:
    """
    Run a speed test synchronously.

    Warning: This may take up to 2 minutes.

    Returns:
        Speed test results
    """
    if SpeedTestService.is_test_running():
        raise HTTPException(
            status_code=409,
            detail="A speed test is already running"
        )

    try:
        result = await SpeedTestService.run_test()
        return {
            "success": result.success,
            "result": result.to_dict(),
        }
    except Exception as e:
        logger.error(f"Speed test failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Speed test failed: {e}"
        )


@router.get("/speedtest/history")
async def get_speedtest_history() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get speed test history.

    Returns:
        List of previous test results
    """
    history = SpeedTestService.get_history()
    return {
        "history": [r.to_dict() for r in history],
        "count": len(history),
    }


@router.get("/speedtest/last")
async def get_last_speedtest() -> Dict[str, Any]:
    """
    Get the most recent speed test result.

    Returns:
        Last test result or null
    """
    result = SpeedTestService.get_last_result()
    return {
        "result": result.to_dict() if result else None,
    }


@router.delete("/speedtest/history", dependencies=[Depends(require_auth)])
async def clear_speedtest_history() -> Dict[str, bool]:
    """
    Clear speed test history.

    Returns:
        Success status
    """
    success = SpeedTestService.clear_history()
    return {"success": success}

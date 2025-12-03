"""
Backup Routes
=============

Configuration backup and restore endpoints.

Endpoints:
- GET /backup/list - List available backups
- POST /backup/create - Create a new backup
- POST /backup/restore/{filename} - Restore from backup
- GET /backup/download/{filename} - Download backup file
- POST /backup/upload - Upload/import backup file
- DELETE /backup/{filename} - Delete a backup

Author: ROSE Link Team
License: MIT
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, Field

from api.dependencies import require_auth
from services.backup_service import BackupService

logger = logging.getLogger("rose-link.backup-routes")

router = APIRouter()


class CreateBackupRequest(BaseModel):
    """Request model for creating a backup."""
    components: Optional[List[str]] = Field(
        None,
        description="Components to backup (None = all)"
    )
    description: str = Field(
        "",
        max_length=200,
        description="Optional description"
    )


class RestoreBackupRequest(BaseModel):
    """Request model for restoring a backup."""
    components: Optional[List[str]] = Field(
        None,
        description="Components to restore (None = all)"
    )


@router.get("/backup/list")
async def list_backups() -> Dict[str, Any]:
    """
    List all available configuration backups.

    Returns:
        Dictionary containing list of backups and available components
    """
    backups = BackupService.list_backups()
    return {
        "backups": [b.to_dict() for b in backups],
        "available_components": list(BackupService.COMPONENTS.keys()),
    }


@router.post("/backup/create", dependencies=[Depends(require_auth)])
async def create_backup(request: CreateBackupRequest) -> Dict[str, Any]:
    """
    Create a new configuration backup.

    Args:
        request: Backup creation parameters

    Returns:
        Information about the created backup
    """
    try:
        backup_info = BackupService.create_backup(
            components=request.components,
            description=request.description,
        )
        return {
            "success": True,
            "backup": backup_info.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OSError as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backup")


@router.post("/backup/restore/{filename}", dependencies=[Depends(require_auth)])
async def restore_backup(
    filename: str,
    request: RestoreBackupRequest
) -> Dict[str, Any]:
    """
    Restore configuration from a backup file.

    Args:
        filename: Backup filename to restore
        request: Restore parameters

    Returns:
        Restore operation results
    """
    try:
        result = BackupService.restore_backup(
            filename=filename,
            components=request.components,
        )
        return {
            "success": len(result["errors"]) == 0,
            "restored": result["restored"],
            "errors": result["errors"],
            "metadata": result["backup_metadata"],
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/backup/download/{filename}")
async def download_backup(filename: str) -> Response:
    """
    Download a backup file.

    Args:
        filename: Backup filename to download

    Returns:
        Backup file as downloadable response
    """
    try:
        data = BackupService.get_backup_data(filename)
        return Response(
            content=data,
            media_type="application/gzip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(data)),
            },
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")


@router.post("/backup/upload", dependencies=[Depends(require_auth)])
async def upload_backup(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload and import a backup file.

    Args:
        file: Uploaded backup file

    Returns:
        Information about the imported backup
    """
    # Validate file extension
    if not file.filename or not file.filename.endswith((".tar.gz", ".tgz")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Expected .tar.gz or .tgz"
        )

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    # Validate file size (max 10MB)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB"
        )

    try:
        backup_info = BackupService.import_backup(content, file.filename)
        return {
            "success": True,
            "backup": backup_info.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/backup/{filename}", dependencies=[Depends(require_auth)])
async def delete_backup(filename: str) -> Dict[str, bool]:
    """
    Delete a backup file.

    Args:
        filename: Backup filename to delete

    Returns:
        Success status
    """
    success = BackupService.delete_backup(filename)
    if not success:
        raise HTTPException(status_code=404, detail="Backup not found")

    return {"success": True}

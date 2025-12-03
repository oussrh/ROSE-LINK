"""
Backup Service
==============

Handles configuration backup and restore operations.

Features:
- Create configuration backups (VPN profiles, hotspot config, settings)
- Restore configurations from backup files
- List available backups
- Delete old backups

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import tarfile
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import Paths, Security

logger = logging.getLogger("rose-link.backup")


@dataclass
class BackupInfo:
    """Information about a backup file."""
    filename: str
    created_at: str
    size_bytes: int
    components: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "filename": self.filename,
            "created_at": self.created_at,
            "size_bytes": self.size_bytes,
            "size_formatted": self._format_size(self.size_bytes),
            "components": self.components,
        }

    @staticmethod
    def _format_size(size: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if abs(size) < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


class BackupService:
    """
    Service for configuration backup and restore.

    This service handles creating, restoring, and managing
    configuration backups for ROSE Link.
    """

    # Backup directory
    BACKUP_DIR = Paths.SYSTEM_DIR / "backups"

    # Components that can be backed up
    COMPONENTS = {
        "vpn_profiles": {
            "path": Paths.WG_PROFILES_DIR,
            "description": "VPN profiles",
        },
        "vpn_settings": {
            "path": Paths.VPN_SETTINGS_CONF,
            "description": "VPN watchdog settings",
        },
        "hotspot": {
            "path": Paths.HOSTAPD_CONF,
            "description": "Hotspot configuration",
        },
        "interfaces": {
            "path": Paths.INTERFACES_CONF,
            "description": "Interface configuration",
        },
    }

    @classmethod
    def ensure_backup_dir(cls) -> None:
        """Ensure backup directory exists."""
        cls.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def create_backup(
        cls,
        components: Optional[List[str]] = None,
        description: str = ""
    ) -> BackupInfo:
        """
        Create a backup of specified components.

        Args:
            components: List of component names to backup (None = all)
            description: Optional description for the backup

        Returns:
            BackupInfo with details about the created backup

        Raises:
            ValueError: If invalid component specified
            OSError: If backup creation fails
        """
        cls.ensure_backup_dir()

        # Validate components
        if components is None:
            components = list(cls.COMPONENTS.keys())
        else:
            for comp in components:
                if comp not in cls.COMPONENTS:
                    raise ValueError(f"Invalid component: {comp}")

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"rose-backup_{timestamp}.tar.gz"
        backup_path = cls.BACKUP_DIR / filename

        # Create backup archive
        backed_up = []
        with tarfile.open(backup_path, "w:gz") as tar:
            # Add metadata
            metadata = {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "description": description,
                "components": components,
            }
            metadata_bytes = json.dumps(metadata, indent=2).encode("utf-8")
            metadata_info = tarfile.TarInfo(name="backup_metadata.json")
            metadata_info.size = len(metadata_bytes)
            tar.addfile(metadata_info, BytesIO(metadata_bytes))

            # Add each component
            for comp in components:
                comp_info = cls.COMPONENTS[comp]
                path = comp_info["path"]

                if not path.exists():
                    logger.warning(f"Component path not found: {path}")
                    continue

                try:
                    if path.is_dir():
                        for file in path.iterdir():
                            if file.is_file():
                                arcname = f"{comp}/{file.name}"
                                tar.add(file, arcname=arcname)
                                backed_up.append(comp)
                    else:
                        arcname = f"{comp}/{path.name}"
                        tar.add(path, arcname=arcname)
                        backed_up.append(comp)
                except (OSError, PermissionError) as e:
                    logger.error(f"Failed to backup {comp}: {e}")

        # Get backup info
        stat = backup_path.stat()
        backup_info = BackupInfo(
            filename=filename,
            created_at=datetime.now().isoformat(),
            size_bytes=stat.st_size,
            components=list(set(backed_up)),
        )

        logger.info(f"Created backup: {filename}")
        return backup_info

    @classmethod
    def restore_backup(
        cls,
        filename: str,
        components: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Restore configuration from a backup file.

        Args:
            filename: Backup filename to restore
            components: List of components to restore (None = all)

        Returns:
            Dictionary with restore results

        Raises:
            FileNotFoundError: If backup file not found
            ValueError: If backup is invalid
        """
        backup_path = cls.BACKUP_DIR / filename

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {filename}")

        restored = []
        errors = []

        with tarfile.open(backup_path, "r:gz") as tar:
            # Read metadata
            try:
                metadata_file = tar.extractfile("backup_metadata.json")
                if metadata_file:
                    metadata = json.load(metadata_file)
                else:
                    metadata = {}
            except (KeyError, json.JSONDecodeError):
                metadata = {}

            # Determine which components to restore
            available = metadata.get("components", list(cls.COMPONENTS.keys()))
            if components is None:
                components = available
            else:
                components = [c for c in components if c in available]

            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as tmpdir:
                tar.extractall(tmpdir, filter="data")

                for comp in components:
                    if comp not in cls.COMPONENTS:
                        continue

                    comp_info = cls.COMPONENTS[comp]
                    target_path = comp_info["path"]
                    source_dir = Path(tmpdir) / comp

                    if not source_dir.exists():
                        continue

                    try:
                        if target_path.is_dir() or not target_path.exists():
                            # Restore directory contents
                            target_path.mkdir(parents=True, exist_ok=True)
                            for file in source_dir.iterdir():
                                if file.is_file():
                                    dest = target_path / file.name
                                    shutil.copy2(file, dest)
                                    os.chmod(dest, Security.SECURE_FILE_MODE)
                        else:
                            # Restore single file
                            source_file = list(source_dir.iterdir())[0]
                            shutil.copy2(source_file, target_path)
                            os.chmod(target_path, Security.SECURE_FILE_MODE)

                        restored.append(comp)
                        logger.info(f"Restored component: {comp}")

                    except (OSError, PermissionError) as e:
                        error_msg = f"Failed to restore {comp}: {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)

        return {
            "restored": restored,
            "errors": errors,
            "backup_metadata": metadata,
        }

    @classmethod
    def list_backups(cls) -> List[BackupInfo]:
        """
        List all available backups.

        Returns:
            List of BackupInfo objects
        """
        cls.ensure_backup_dir()

        backups = []
        for file in cls.BACKUP_DIR.glob("rose-backup_*.tar.gz"):
            try:
                stat = file.stat()

                # Try to read metadata
                components = []
                created_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

                try:
                    with tarfile.open(file, "r:gz") as tar:
                        metadata_file = tar.extractfile("backup_metadata.json")
                        if metadata_file:
                            metadata = json.load(metadata_file)
                            components = metadata.get("components", [])
                            created_at = metadata.get("created_at", created_at)
                except Exception:
                    pass

                backups.append(BackupInfo(
                    filename=file.name,
                    created_at=created_at,
                    size_bytes=stat.st_size,
                    components=components,
                ))
            except OSError:
                continue

        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b.created_at, reverse=True)
        return backups

    @classmethod
    def delete_backup(cls, filename: str) -> bool:
        """
        Delete a backup file.

        Args:
            filename: Backup filename to delete

        Returns:
            True if deleted, False otherwise
        """
        backup_path = cls.BACKUP_DIR / filename

        if not backup_path.exists():
            return False

        try:
            backup_path.unlink()
            logger.info(f"Deleted backup: {filename}")
            return True
        except OSError as e:
            logger.error(f"Failed to delete backup {filename}: {e}")
            return False

    @classmethod
    def get_backup_data(cls, filename: str) -> bytes:
        """
        Get backup file data for download.

        Args:
            filename: Backup filename

        Returns:
            Backup file bytes

        Raises:
            FileNotFoundError: If backup not found
        """
        backup_path = cls.BACKUP_DIR / filename

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {filename}")

        return backup_path.read_bytes()

    @classmethod
    def import_backup(cls, data: bytes, filename: str) -> BackupInfo:
        """
        Import a backup file from uploaded data.

        Args:
            data: Backup file bytes
            filename: Original filename

        Returns:
            BackupInfo for the imported backup

        Raises:
            ValueError: If backup is invalid
        """
        cls.ensure_backup_dir()

        # Validate it's a valid tar.gz
        try:
            with tarfile.open(fileobj=BytesIO(data), mode="r:gz") as tar:
                # Check for metadata
                names = tar.getnames()
                if "backup_metadata.json" not in names:
                    logger.warning("Imported backup has no metadata")
        except tarfile.TarError as e:
            raise ValueError(f"Invalid backup file: {e}")

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"rose-backup_{timestamp}_imported.tar.gz"
        backup_path = cls.BACKUP_DIR / new_filename

        # Save the backup
        backup_path.write_bytes(data)

        logger.info(f"Imported backup: {new_filename}")

        # Return info
        return BackupInfo(
            filename=new_filename,
            created_at=datetime.now().isoformat(),
            size_bytes=len(data),
            components=[],
        )

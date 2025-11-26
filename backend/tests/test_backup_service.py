"""
Backup Service Tests
====================

Unit tests for the backup service with mocked file operations.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import json
import tarfile
from io import BytesIO
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from services.backup_service import BackupService, BackupInfo


class TestBackupInfo:
    """Tests for BackupInfo dataclass."""

    def test_to_dict_basic(self) -> None:
        """Should convert BackupInfo to dictionary."""
        info = BackupInfo(
            filename="test.tar.gz",
            created_at="2024-01-01T12:00:00",
            size_bytes=1024,
            components=["vpn_profiles"],
        )
        result = info.to_dict()

        assert result["filename"] == "test.tar.gz"
        assert result["created_at"] == "2024-01-01T12:00:00"
        assert result["size_bytes"] == 1024
        assert result["components"] == ["vpn_profiles"]

    def test_to_dict_includes_formatted_size(self) -> None:
        """Should include formatted size in dictionary."""
        info = BackupInfo(
            filename="test.tar.gz",
            created_at="2024-01-01T12:00:00",
            size_bytes=1024,
        )
        result = info.to_dict()

        assert "size_formatted" in result
        assert "KB" in result["size_formatted"]

    def test_format_size_bytes(self) -> None:
        """Should format bytes correctly."""
        result = BackupInfo._format_size(512)
        assert "512" in result
        assert "B" in result

    def test_format_size_kilobytes(self) -> None:
        """Should format kilobytes correctly."""
        result = BackupInfo._format_size(2048)
        assert "KB" in result

    def test_format_size_megabytes(self) -> None:
        """Should format megabytes correctly."""
        result = BackupInfo._format_size(2 * 1024 * 1024)
        assert "MB" in result

    def test_format_size_gigabytes(self) -> None:
        """Should format gigabytes correctly."""
        result = BackupInfo._format_size(2 * 1024 * 1024 * 1024)
        assert "GB" in result


class TestBackupServiceEnsureDir:
    """Tests for ensure_backup_dir method."""

    def test_creates_backup_directory(self, temp_dir: Path) -> None:
        """Should create backup directory if it doesn't exist."""
        backup_dir = temp_dir / "backups"
        assert not backup_dir.exists()

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            BackupService.ensure_backup_dir()

        assert backup_dir.exists()

    def test_does_not_fail_if_directory_exists(self, temp_dir: Path) -> None:
        """Should not fail if directory already exists."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            BackupService.ensure_backup_dir()

        assert backup_dir.exists()


class TestBackupServiceCreateBackup:
    """Tests for create_backup method."""

    def test_creates_backup_file(self, temp_dir: Path) -> None:
        """Should create a backup tar.gz file."""
        backup_dir = temp_dir / "backups"
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir(parents=True)

        # Create a test profile
        (profiles_dir / "test.conf").write_text("[Interface]\nPrivateKey=abc")

        components = {
            "vpn_profiles": {
                "path": profiles_dir,
                "description": "VPN profiles",
            },
        }

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with patch.object(BackupService, "COMPONENTS", components):
                result = BackupService.create_backup()

        assert backup_dir.exists()
        assert (backup_dir / result.filename).exists()
        assert result.filename.startswith("rose-backup_")
        assert result.filename.endswith(".tar.gz")

    def test_backup_contains_metadata(self, temp_dir: Path) -> None:
        """Should include metadata in backup."""
        backup_dir = temp_dir / "backups"
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir(parents=True)
        (profiles_dir / "test.conf").write_text("[Interface]")

        components = {
            "vpn_profiles": {"path": profiles_dir, "description": "VPN"},
        }

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with patch.object(BackupService, "COMPONENTS", components):
                result = BackupService.create_backup()

        backup_path = backup_dir / result.filename
        with tarfile.open(backup_path, "r:gz") as tar:
            assert "backup_metadata.json" in tar.getnames()

    def test_backup_with_description(self, temp_dir: Path) -> None:
        """Should include description in metadata."""
        backup_dir = temp_dir / "backups"
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir(parents=True)
        (profiles_dir / "test.conf").write_text("[Interface]")

        components = {
            "vpn_profiles": {"path": profiles_dir, "description": "VPN"},
        }

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with patch.object(BackupService, "COMPONENTS", components):
                result = BackupService.create_backup(description="Test backup")

        backup_path = backup_dir / result.filename
        with tarfile.open(backup_path, "r:gz") as tar:
            metadata_file = tar.extractfile("backup_metadata.json")
            metadata = json.load(metadata_file)
            assert metadata["description"] == "Test backup"

    def test_backup_specific_components(self, temp_dir: Path) -> None:
        """Should backup only specified components."""
        backup_dir = temp_dir / "backups"
        profiles_dir = temp_dir / "profiles"
        hotspot_dir = temp_dir / "hotspot"
        profiles_dir.mkdir(parents=True)
        hotspot_dir.mkdir(parents=True)
        (profiles_dir / "test.conf").write_text("[Interface]")
        (hotspot_dir / "hostapd.conf").write_text("ssid=test")

        components = {
            "vpn_profiles": {"path": profiles_dir, "description": "VPN"},
            "hotspot": {"path": hotspot_dir, "description": "Hotspot"},
        }

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with patch.object(BackupService, "COMPONENTS", components):
                result = BackupService.create_backup(components=["vpn_profiles"])

        assert "vpn_profiles" in result.components
        # hotspot should not be included
        backup_path = backup_dir / result.filename
        with tarfile.open(backup_path, "r:gz") as tar:
            names = tar.getnames()
            assert any("vpn_profiles" in n for n in names)
            assert not any("hotspot" in n for n in names)

    def test_invalid_component_raises_error(self, temp_dir: Path) -> None:
        """Should raise ValueError for invalid component."""
        backup_dir = temp_dir / "backups"

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with patch.object(BackupService, "COMPONENTS", {}):
                with pytest.raises(ValueError, match="Invalid component"):
                    BackupService.create_backup(components=["nonexistent"])

    def test_missing_component_path_skipped(self, temp_dir: Path) -> None:
        """Should skip components with missing paths."""
        backup_dir = temp_dir / "backups"
        nonexistent = temp_dir / "nonexistent"

        components = {
            "missing": {"path": nonexistent, "description": "Missing"},
        }

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with patch.object(BackupService, "COMPONENTS", components):
                result = BackupService.create_backup()

        assert result.components == []


class TestBackupServiceRestoreBackup:
    """Tests for restore_backup method."""

    def test_restore_backup(self, temp_dir: Path) -> None:
        """Should restore components from backup."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir(parents=True)

        # Create a backup with test data
        backup_path = backup_dir / "rose-backup_test.tar.gz"
        with tarfile.open(backup_path, "w:gz") as tar:
            # Add metadata
            metadata = {
                "version": "1.0",
                "created_at": "2024-01-01T12:00:00",
                "components": ["vpn_profiles"],
            }
            metadata_bytes = json.dumps(metadata).encode()
            info = tarfile.TarInfo(name="backup_metadata.json")
            info.size = len(metadata_bytes)
            tar.addfile(info, BytesIO(metadata_bytes))

            # Add a profile file
            profile_data = b"[Interface]\nPrivateKey=restored"
            info = tarfile.TarInfo(name="vpn_profiles/test.conf")
            info.size = len(profile_data)
            tar.addfile(info, BytesIO(profile_data))

        components = {
            "vpn_profiles": {"path": profiles_dir, "description": "VPN"},
        }

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with patch.object(BackupService, "COMPONENTS", components):
                result = BackupService.restore_backup("rose-backup_test.tar.gz")

        assert "vpn_profiles" in result["restored"]
        assert (profiles_dir / "test.conf").exists()

    def test_restore_nonexistent_backup_raises_error(self, temp_dir: Path) -> None:
        """Should raise FileNotFoundError for missing backup."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with pytest.raises(FileNotFoundError, match="not found"):
                BackupService.restore_backup("nonexistent.tar.gz")

    def test_restore_specific_components(self, temp_dir: Path) -> None:
        """Should restore only specified components."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)
        profiles_dir = temp_dir / "profiles"
        profiles_dir.mkdir(parents=True)
        hotspot_file = temp_dir / "hostapd.conf"

        # Create a backup with multiple components
        backup_path = backup_dir / "rose-backup_test.tar.gz"
        with tarfile.open(backup_path, "w:gz") as tar:
            metadata = {
                "version": "1.0",
                "components": ["vpn_profiles", "hotspot"],
            }
            metadata_bytes = json.dumps(metadata).encode()
            info = tarfile.TarInfo(name="backup_metadata.json")
            info.size = len(metadata_bytes)
            tar.addfile(info, BytesIO(metadata_bytes))

            # VPN profile
            profile_data = b"[Interface]"
            info = tarfile.TarInfo(name="vpn_profiles/test.conf")
            info.size = len(profile_data)
            tar.addfile(info, BytesIO(profile_data))

            # Hotspot config
            hotspot_data = b"ssid=test"
            info = tarfile.TarInfo(name="hotspot/hostapd.conf")
            info.size = len(hotspot_data)
            tar.addfile(info, BytesIO(hotspot_data))

        components = {
            "vpn_profiles": {"path": profiles_dir, "description": "VPN"},
            "hotspot": {"path": hotspot_file, "description": "Hotspot"},
        }

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with patch.object(BackupService, "COMPONENTS", components):
                result = BackupService.restore_backup(
                    "rose-backup_test.tar.gz",
                    components=["vpn_profiles"]
                )

        assert "vpn_profiles" in result["restored"]
        assert "hotspot" not in result["restored"]


class TestBackupServiceListBackups:
    """Tests for list_backups method."""

    def test_list_empty_directory(self, temp_dir: Path) -> None:
        """Should return empty list for empty directory."""
        backup_dir = temp_dir / "backups"

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            result = BackupService.list_backups()

        assert result == []

    def test_list_finds_backup_files(self, temp_dir: Path) -> None:
        """Should find all backup files."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)

        # Create some backup files
        for i in range(3):
            backup_path = backup_dir / f"rose-backup_test{i}.tar.gz"
            with tarfile.open(backup_path, "w:gz") as tar:
                metadata = {"version": "1.0", "components": []}
                data = json.dumps(metadata).encode()
                info = tarfile.TarInfo(name="backup_metadata.json")
                info.size = len(data)
                tar.addfile(info, BytesIO(data))

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            result = BackupService.list_backups()

        assert len(result) == 3

    def test_list_ignores_non_backup_files(self, temp_dir: Path) -> None:
        """Should ignore files not matching backup pattern."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)

        # Create non-backup files
        (backup_dir / "readme.txt").write_text("test")
        (backup_dir / "other.tar.gz").write_text("test")

        # Create one backup file
        backup_path = backup_dir / "rose-backup_test.tar.gz"
        with tarfile.open(backup_path, "w:gz") as tar:
            data = json.dumps({"version": "1.0"}).encode()
            info = tarfile.TarInfo(name="backup_metadata.json")
            info.size = len(data)
            tar.addfile(info, BytesIO(data))

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            result = BackupService.list_backups()

        assert len(result) == 1

    def test_list_sorted_by_date_newest_first(self, temp_dir: Path) -> None:
        """Should sort backups by creation date, newest first."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)

        dates = ["2024-01-01T00:00:00", "2024-01-03T00:00:00", "2024-01-02T00:00:00"]
        for i, date in enumerate(dates):
            backup_path = backup_dir / f"rose-backup_test{i}.tar.gz"
            with tarfile.open(backup_path, "w:gz") as tar:
                metadata = {"created_at": date, "components": []}
                data = json.dumps(metadata).encode()
                info = tarfile.TarInfo(name="backup_metadata.json")
                info.size = len(data)
                tar.addfile(info, BytesIO(data))

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            result = BackupService.list_backups()

        # Should be sorted newest first
        assert result[0].created_at == "2024-01-03T00:00:00"
        assert result[2].created_at == "2024-01-01T00:00:00"


class TestBackupServiceDeleteBackup:
    """Tests for delete_backup method."""

    def test_delete_existing_backup(self, temp_dir: Path) -> None:
        """Should delete existing backup and return True."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)
        backup_file = backup_dir / "rose-backup_test.tar.gz"
        backup_file.write_bytes(b"test")

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            result = BackupService.delete_backup("rose-backup_test.tar.gz")

        assert result is True
        assert not backup_file.exists()

    def test_delete_nonexistent_backup(self, temp_dir: Path) -> None:
        """Should return False for nonexistent backup."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            result = BackupService.delete_backup("nonexistent.tar.gz")

        assert result is False


class TestBackupServiceGetBackupData:
    """Tests for get_backup_data method."""

    def test_get_existing_backup_data(self, temp_dir: Path) -> None:
        """Should return backup file bytes."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)
        backup_file = backup_dir / "rose-backup_test.tar.gz"
        backup_file.write_bytes(b"backup content")

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            result = BackupService.get_backup_data("rose-backup_test.tar.gz")

        assert result == b"backup content"

    def test_get_nonexistent_backup_raises_error(self, temp_dir: Path) -> None:
        """Should raise FileNotFoundError for missing backup."""
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir(parents=True)

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with pytest.raises(FileNotFoundError, match="not found"):
                BackupService.get_backup_data("nonexistent.tar.gz")


class TestBackupServiceImportBackup:
    """Tests for import_backup method."""

    def test_import_valid_backup(self, temp_dir: Path) -> None:
        """Should import valid backup file."""
        backup_dir = temp_dir / "backups"

        # Create valid backup data
        buffer = BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
            metadata = {"version": "1.0", "components": []}
            data = json.dumps(metadata).encode()
            info = tarfile.TarInfo(name="backup_metadata.json")
            info.size = len(data)
            tar.addfile(info, BytesIO(data))
        backup_data = buffer.getvalue()

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            result = BackupService.import_backup(backup_data, "uploaded.tar.gz")

        assert result.filename.endswith("_imported.tar.gz")
        assert (backup_dir / result.filename).exists()

    def test_import_invalid_backup_raises_error(self, temp_dir: Path) -> None:
        """Should raise ValueError for invalid backup."""
        backup_dir = temp_dir / "backups"

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            with pytest.raises(ValueError, match="Invalid backup"):
                BackupService.import_backup(b"not a tar file", "invalid.tar.gz")

    def test_import_backup_without_metadata_logs_warning(
        self, temp_dir: Path
    ) -> None:
        """Should import backup without metadata but log warning."""
        backup_dir = temp_dir / "backups"

        # Create tar without metadata
        buffer = BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
            data = b"some content"
            info = tarfile.TarInfo(name="data.txt")
            info.size = len(data)
            tar.addfile(info, BytesIO(data))
        backup_data = buffer.getvalue()

        with patch.object(BackupService, "BACKUP_DIR", backup_dir):
            result = BackupService.import_backup(backup_data, "uploaded.tar.gz")

        # Should still import despite missing metadata
        assert (backup_dir / result.filename).exists()

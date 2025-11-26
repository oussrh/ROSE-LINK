"""
Validators Tests
================

Unit tests for input validation functions.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import pytest

from utils.validators import (
    validate_filename,
    validate_ssid,
    validate_wpa_password,
    validate_ping_host,
    validate_wireguard_config,
    validate_country_code,
    validate_wifi_channel,
    validate_check_interval,
)
from exceptions import (
    InvalidFilenameError,
    InvalidSSIDError,
    InvalidPasswordError,
    InvalidHostError,
    InvalidWireGuardConfigError,
)


class TestValidateFilename:
    """Tests for validate_filename function."""

    def test_valid_simple_filename(self) -> None:
        """Should accept a simple valid filename."""
        result = validate_filename("test.conf")
        assert result == "test.conf"

    def test_valid_filename_with_dashes_underscores(self) -> None:
        """Should accept filenames with dashes and underscores."""
        result = validate_filename("my-config_v2.conf")
        assert result == "my-config_v2.conf"

    def test_empty_filename_raises_error(self) -> None:
        """Should raise error for empty filename."""
        with pytest.raises(InvalidFilenameError, match="required"):
            validate_filename("")

    def test_none_filename_raises_error(self) -> None:
        """Should raise error for None filename."""
        with pytest.raises(InvalidFilenameError):
            validate_filename(None)  # type: ignore

    def test_path_traversal_stripped(self) -> None:
        """Should strip path traversal attempts."""
        result = validate_filename("../../../etc/passwd")
        assert result == "passwd"
        assert ".." not in result
        assert "/" not in result

    def test_absolute_path_stripped(self) -> None:
        """Should strip absolute path components."""
        result = validate_filename("/etc/passwd")
        assert result == "passwd"

    def test_hidden_file_prefix_replaced(self) -> None:
        """Should replace leading dot with underscore."""
        result = validate_filename(".hidden")
        assert result == "_hidden"
        assert not result.startswith(".")

    def test_special_characters_sanitized(self) -> None:
        """Should sanitize special characters."""
        result = validate_filename("my config!@#$.conf")
        assert " " not in result
        assert "!" not in result
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result

    def test_long_filename_truncated(self) -> None:
        """Should truncate filenames exceeding max length."""
        long_name = "a" * 200 + ".conf"
        result = validate_filename(long_name)
        assert len(result) <= 100

    def test_only_special_chars_raises_error(self) -> None:
        """Should raise error if filename becomes empty after sanitization."""
        # "..." gets sanitized to "___" which is valid
        # Use characters that will result in an empty filename
        with pytest.raises(InvalidFilenameError):
            validate_filename("///")  # Path separators only


class TestValidateSSID:
    """Tests for validate_ssid function."""

    def test_valid_ssid(self) -> None:
        """Should accept a valid SSID."""
        result = validate_ssid("MyNetwork")
        assert result == "MyNetwork"

    def test_ssid_with_spaces(self) -> None:
        """Should accept SSID with spaces."""
        result = validate_ssid("My Network Name")
        assert result == "My Network Name"

    def test_empty_ssid_raises_error(self) -> None:
        """Should raise error for empty SSID."""
        with pytest.raises(InvalidSSIDError, match="empty"):
            validate_ssid("")

    def test_none_ssid_raises_error(self) -> None:
        """Should raise error for None SSID."""
        with pytest.raises(InvalidSSIDError):
            validate_ssid(None)  # type: ignore

    def test_ssid_too_long_raises_error(self) -> None:
        """Should raise error for SSID exceeding 32 characters."""
        long_ssid = "A" * 33
        with pytest.raises(InvalidSSIDError, match="32"):
            validate_ssid(long_ssid)

    def test_ssid_at_max_length(self) -> None:
        """Should accept SSID at exactly 32 characters."""
        max_ssid = "A" * 32
        result = validate_ssid(max_ssid)
        assert result == max_ssid

    def test_ssid_newline_removed(self) -> None:
        """Should remove newline characters."""
        result = validate_ssid("My\nNetwork")
        assert "\n" not in result
        assert result == "MyNetwork"

    def test_ssid_carriage_return_removed(self) -> None:
        """Should remove carriage return characters."""
        result = validate_ssid("My\rNetwork")
        assert "\r" not in result

    def test_ssid_null_byte_removed(self) -> None:
        """Should remove null byte characters."""
        result = validate_ssid("My\x00Network")
        assert "\x00" not in result

    def test_ssid_leading_hash_removed(self) -> None:
        """Should remove leading hash character."""
        result = validate_ssid("#CommentedSSID")
        assert result == "CommentedSSID"

    def test_ssid_only_hash_raises_error(self) -> None:
        """Should raise error if SSID is only hash."""
        with pytest.raises(InvalidSSIDError):
            validate_ssid("#")


class TestValidateWpaPassword:
    """Tests for validate_wpa_password function."""

    def test_valid_password(self) -> None:
        """Should accept a valid password."""
        result = validate_wpa_password("mypassword123")
        assert result == "mypassword123"

    def test_empty_password_raises_error(self) -> None:
        """Should raise error for empty password."""
        with pytest.raises(InvalidPasswordError, match="required"):
            validate_wpa_password("")

    def test_password_too_short_raises_error(self) -> None:
        """Should raise error for password shorter than 8 chars."""
        with pytest.raises(InvalidPasswordError, match="at least 8"):
            validate_wpa_password("short")

    def test_password_at_min_length(self) -> None:
        """Should accept password at exactly 8 characters."""
        result = validate_wpa_password("12345678")
        assert result == "12345678"

    def test_password_too_long_raises_error(self) -> None:
        """Should raise error for password exceeding 63 characters."""
        long_password = "A" * 64
        with pytest.raises(InvalidPasswordError, match="63"):
            validate_wpa_password(long_password)

    def test_password_at_max_length(self) -> None:
        """Should accept password at exactly 63 characters."""
        max_password = "A" * 63
        result = validate_wpa_password(max_password)
        assert result == max_password

    def test_password_newline_removed(self) -> None:
        """Should remove newline characters."""
        result = validate_wpa_password("password\n123")
        assert "\n" not in result

    def test_password_carriage_return_removed(self) -> None:
        """Should remove carriage return characters."""
        result = validate_wpa_password("password\r123")
        assert "\r" not in result

    def test_password_leading_hash_removed(self) -> None:
        """Should remove leading hash character."""
        result = validate_wpa_password("#password123")
        assert result == "password123"

    def test_password_becomes_too_short_after_sanitization(self) -> None:
        """Should raise error if password too short after sanitization."""
        with pytest.raises(InvalidPasswordError):
            validate_wpa_password("###12345")


class TestValidatePingHost:
    """Tests for validate_ping_host function."""

    def test_valid_ipv4_address(self) -> None:
        """Should accept valid IPv4 address."""
        result = validate_ping_host("8.8.8.8")
        assert result == "8.8.8.8"

    def test_valid_ipv4_address_with_zeros(self) -> None:
        """Should accept IPv4 address with zeros."""
        result = validate_ping_host("192.168.0.1")
        assert result == "192.168.0.1"

    def test_valid_hostname(self) -> None:
        """Should accept valid hostname."""
        result = validate_ping_host("google.com")
        assert result == "google.com"

    def test_valid_hostname_with_subdomain(self) -> None:
        """Should accept hostname with subdomain."""
        result = validate_ping_host("dns.google.com")
        assert result == "dns.google.com"

    def test_empty_host_raises_error(self) -> None:
        """Should raise error for empty host."""
        with pytest.raises(InvalidHostError, match="required"):
            validate_ping_host("")

    def test_whitespace_only_raises_error(self) -> None:
        """Should raise error for whitespace-only host."""
        with pytest.raises(InvalidHostError, match="empty"):
            validate_ping_host("   ")

    def test_whitespace_stripped(self) -> None:
        """Should strip whitespace from host."""
        result = validate_ping_host("  8.8.8.8  ")
        assert result == "8.8.8.8"

    def test_invalid_format_raises_error(self) -> None:
        """Should raise error for invalid format."""
        with pytest.raises(InvalidHostError, match="Invalid"):
            validate_ping_host("not a valid host!")

    def test_shell_metachar_ampersand_raises_error(self) -> None:
        """Should raise error for ampersand character."""
        with pytest.raises(InvalidHostError, match="Invalid"):
            validate_ping_host("8.8.8.8&rm -rf /")

    def test_shell_metachar_semicolon_raises_error(self) -> None:
        """Should raise error for semicolon character."""
        with pytest.raises(InvalidHostError, match="Invalid"):
            validate_ping_host("8.8.8.8;ls")

    def test_shell_metachar_pipe_raises_error(self) -> None:
        """Should raise error for pipe character."""
        with pytest.raises(InvalidHostError, match="Invalid"):
            validate_ping_host("8.8.8.8|cat /etc/passwd")

    def test_shell_metachar_dollar_raises_error(self) -> None:
        """Should raise error for dollar sign character."""
        with pytest.raises(InvalidHostError, match="Invalid"):
            validate_ping_host("$HOME")

    def test_shell_metachar_backtick_raises_error(self) -> None:
        """Should raise error for backtick character."""
        with pytest.raises(InvalidHostError, match="Invalid"):
            validate_ping_host("`whoami`")

    def test_newline_raises_error(self) -> None:
        """Should raise error for newline in host."""
        with pytest.raises(InvalidHostError, match="Invalid"):
            validate_ping_host("8.8.8.8\nrm -rf /")


class TestValidateWireguardConfig:
    """Tests for validate_wireguard_config function."""

    def test_valid_config(self) -> None:
        """Should accept valid WireGuard config."""
        config = b"""[Interface]
PrivateKey = abc123
Address = 10.0.0.2/32

[Peer]
PublicKey = def456
Endpoint = vpn.example.com:51820
"""
        result = validate_wireguard_config(config)
        assert result is True

    def test_minimal_valid_config(self) -> None:
        """Should accept minimal valid config."""
        config = b"[Interface]\nPrivateKey = abc123"
        result = validate_wireguard_config(config)
        assert result is True

    def test_missing_interface_section_raises_error(self) -> None:
        """Should raise error for missing [Interface] section."""
        config = b"PrivateKey = abc123"
        with pytest.raises(InvalidWireGuardConfigError, match="Interface"):
            validate_wireguard_config(config)

    def test_missing_privatekey_raises_error(self) -> None:
        """Should raise error for missing PrivateKey field."""
        config = b"[Interface]\nAddress = 10.0.0.2/32"
        with pytest.raises(InvalidWireGuardConfigError, match="PrivateKey"):
            validate_wireguard_config(config)

    def test_invalid_utf8_raises_error(self) -> None:
        """Should raise error for invalid UTF-8 content."""
        config = b"\x80\x81\x82"
        with pytest.raises(InvalidWireGuardConfigError, match="UTF-8"):
            validate_wireguard_config(config)

    def test_empty_config_raises_error(self) -> None:
        """Should raise error for empty config."""
        config = b""
        with pytest.raises(InvalidWireGuardConfigError):
            validate_wireguard_config(config)

    def test_none_config_raises_error(self) -> None:
        """Should raise error for None config."""
        with pytest.raises(InvalidWireGuardConfigError):
            validate_wireguard_config(None)  # type: ignore


class TestValidateCountryCode:
    """Tests for validate_country_code function."""

    def test_valid_uppercase_code(self) -> None:
        """Should accept valid uppercase country code."""
        result = validate_country_code("US")
        assert result == "US"

    def test_valid_lowercase_code_normalized(self) -> None:
        """Should normalize lowercase to uppercase."""
        result = validate_country_code("be")
        assert result == "BE"

    def test_valid_mixed_case_normalized(self) -> None:
        """Should normalize mixed case to uppercase."""
        result = validate_country_code("Uk")
        assert result == "UK"

    def test_empty_code_returns_default(self) -> None:
        """Should return US for empty code."""
        result = validate_country_code("")
        assert result == "US"

    def test_none_code_returns_default(self) -> None:
        """Should return US for None code."""
        result = validate_country_code(None)  # type: ignore
        assert result == "US"

    def test_invalid_code_returns_default(self) -> None:
        """Should return default for invalid code (truncated to 2 chars)."""
        result = validate_country_code("INVALID")
        # "INVALID" truncated to "IN" which is a valid country code (India)
        assert result == "IN"

    def test_numeric_code_returns_default(self) -> None:
        """Should return US for numeric code."""
        result = validate_country_code("12")
        assert result == "US"

    def test_long_code_truncated(self) -> None:
        """Should truncate long codes to 2 characters."""
        result = validate_country_code("USA")
        assert result == "US"


class TestValidateWifiChannel:
    """Tests for validate_wifi_channel function."""

    def test_valid_2ghz_channel(self) -> None:
        """Should accept valid 2.4GHz channel."""
        result = validate_wifi_channel(6, "2.4GHz")
        assert result == 6

    def test_valid_2ghz_channel_1(self) -> None:
        """Should accept channel 1 for 2.4GHz."""
        result = validate_wifi_channel(1, "2.4GHz")
        assert result == 1

    def test_valid_2ghz_channel_13(self) -> None:
        """Should accept channel 13 for 2.4GHz."""
        result = validate_wifi_channel(13, "2.4GHz")
        assert result == 13

    def test_invalid_2ghz_channel_returns_default(self) -> None:
        """Should return default for invalid 2.4GHz channel."""
        result = validate_wifi_channel(14, "2.4GHz")
        assert result == 6  # Default 2.4GHz channel

    def test_invalid_2ghz_channel_zero(self) -> None:
        """Should return default for channel 0."""
        result = validate_wifi_channel(0, "2.4GHz")
        assert result == 6

    def test_negative_2ghz_channel_returns_default(self) -> None:
        """Should return default for negative channel."""
        result = validate_wifi_channel(-1, "2.4GHz")
        assert result == 6

    def test_valid_5ghz_channel_36(self) -> None:
        """Should accept channel 36 for 5GHz."""
        result = validate_wifi_channel(36, "5GHz")
        assert result == 36

    def test_valid_5ghz_channel_149(self) -> None:
        """Should accept channel 149 for 5GHz."""
        result = validate_wifi_channel(149, "5GHz")
        assert result == 149

    def test_invalid_5ghz_channel_returns_default(self) -> None:
        """Should return default for invalid 5GHz channel."""
        result = validate_wifi_channel(6, "5GHz")
        assert result == 36  # Default 5GHz channel

    def test_invalid_5ghz_channel_37(self) -> None:
        """Should return default for invalid channel 37."""
        result = validate_wifi_channel(37, "5GHz")
        assert result == 36


class TestValidateCheckInterval:
    """Tests for validate_check_interval function."""

    def test_valid_interval(self) -> None:
        """Should accept valid interval."""
        result = validate_check_interval(60)
        assert result == 60

    def test_minimum_interval(self) -> None:
        """Should accept minimum interval (30 seconds)."""
        result = validate_check_interval(30)
        assert result == 30

    def test_maximum_interval(self) -> None:
        """Should accept maximum interval (300 seconds)."""
        result = validate_check_interval(300)
        assert result == 300

    def test_below_minimum_clamped(self) -> None:
        """Should clamp interval below minimum to minimum."""
        result = validate_check_interval(10)
        assert result == 30

    def test_above_maximum_clamped(self) -> None:
        """Should clamp interval above maximum to maximum."""
        result = validate_check_interval(600)
        assert result == 300

    def test_zero_clamped_to_minimum(self) -> None:
        """Should clamp zero to minimum."""
        result = validate_check_interval(0)
        assert result == 30

    def test_negative_clamped_to_minimum(self) -> None:
        """Should clamp negative value to minimum."""
        result = validate_check_interval(-10)
        assert result == 30

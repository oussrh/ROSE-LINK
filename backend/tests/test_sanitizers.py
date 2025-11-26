"""
Sanitizers Tests
================

Unit tests for input sanitization functions.

Author: ROSE Link Team
License: MIT
"""

from __future__ import annotations

import pytest

from utils.sanitizers import (
    sanitize_filename,
    escape_hostapd_value,
    sanitize_service_name,
    sanitize_log_lines,
    strip_ansi_codes,
    normalize_mac_address,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_filename_unchanged(self) -> None:
        """Should return simple filename unchanged."""
        result = sanitize_filename("test.conf")
        assert result == "test.conf"

    def test_filename_with_dashes_underscores(self) -> None:
        """Should preserve dashes and underscores."""
        result = sanitize_filename("my-config_v2.conf")
        assert result == "my-config_v2.conf"

    def test_path_traversal_attack_blocked(self) -> None:
        """Should strip path traversal attempts."""
        result = sanitize_filename("../../../etc/passwd")
        assert result == "passwd"
        assert ".." not in result
        assert "/" not in result

    def test_absolute_path_stripped(self) -> None:
        """Should strip absolute path components."""
        result = sanitize_filename("/etc/passwd")
        assert result == "passwd"

    def test_windows_path_stripped(self) -> None:
        """Should strip Windows path components."""
        result = sanitize_filename("C:\\Windows\\System32\\config")
        assert ".." not in result
        assert "\\" not in result

    def test_hidden_file_prefix_replaced(self) -> None:
        """Should replace leading dot with underscore."""
        result = sanitize_filename(".hidden_file")
        assert result == "_hidden_file"
        assert not result.startswith(".")

    def test_special_characters_replaced(self) -> None:
        """Should replace special characters with underscores."""
        result = sanitize_filename("my file!@#$%.conf")
        assert " " not in result
        assert "!" not in result
        assert "@" not in result
        assert "#" not in result
        assert "%" not in result

    def test_long_filename_truncated(self) -> None:
        """Should truncate filenames exceeding max length."""
        long_name = "a" * 200 + ".conf"
        result = sanitize_filename(long_name)
        assert len(result) <= 100

    def test_empty_filename_raises_error(self) -> None:
        """Should raise ValueError for empty filename."""
        with pytest.raises(ValueError, match="required"):
            sanitize_filename("")

    def test_none_filename_raises_error(self) -> None:
        """Should raise ValueError for None filename."""
        with pytest.raises(ValueError):
            sanitize_filename(None)  # type: ignore

    def test_only_dots_returns_underscores(self) -> None:
        """Leading dot gets replaced with underscore."""
        # "..." has leading dot replaced, resulting in "_.."
        result = sanitize_filename("...")
        assert result == "_.."

    def test_only_path_separator_raises_error(self) -> None:
        """Should raise ValueError for path separator only."""
        with pytest.raises(ValueError):
            sanitize_filename("/")


class TestEscapeHostapdValue:
    """Tests for escape_hostapd_value function."""

    def test_simple_value_unchanged(self) -> None:
        """Should return simple value unchanged."""
        result = escape_hostapd_value("MyNetwork")
        assert result == "MyNetwork"

    def test_value_with_spaces_preserved(self) -> None:
        """Should preserve spaces in value."""
        result = escape_hostapd_value("My Network Name")
        assert result == "My Network Name"

    def test_newline_removed(self) -> None:
        """Should remove newline characters."""
        result = escape_hostapd_value("line1\nline2")
        assert result == "line1line2"
        assert "\n" not in result

    def test_carriage_return_removed(self) -> None:
        """Should remove carriage return characters."""
        result = escape_hostapd_value("line1\rline2")
        assert result == "line1line2"
        assert "\r" not in result

    def test_crlf_removed(self) -> None:
        """Should remove CRLF sequences."""
        result = escape_hostapd_value("line1\r\nline2")
        assert result == "line1line2"

    def test_null_byte_removed(self) -> None:
        """Should remove null byte characters."""
        result = escape_hostapd_value("before\x00after")
        assert result == "beforeafter"
        assert "\x00" not in result

    def test_leading_hash_stripped(self) -> None:
        """Should strip leading hash character."""
        result = escape_hostapd_value("#CommentedValue")
        assert result == "CommentedValue"

    def test_multiple_leading_hashes_stripped(self) -> None:
        """Should strip multiple leading hash characters."""
        result = escape_hostapd_value("###Value")
        assert result == "Value"

    def test_hash_in_middle_preserved(self) -> None:
        """Should preserve hash not at beginning."""
        result = escape_hostapd_value("My#Network")
        assert result == "My#Network"

    def test_injection_attack_blocked(self) -> None:
        """Should block config injection via newlines."""
        result = escape_hostapd_value("valid\nssid=evil")
        assert result == "validssid=evil"
        assert "\n" not in result

    def test_empty_string_returns_empty(self) -> None:
        """Should return empty string for empty input."""
        result = escape_hostapd_value("")
        assert result == ""


class TestSanitizeServiceName:
    """Tests for sanitize_service_name function."""

    def test_valid_service_name(self) -> None:
        """Should return valid service name."""
        allowed = ("hostapd", "dnsmasq", "rose-backend")
        result = sanitize_service_name("hostapd", allowed)
        assert result == "hostapd"

    def test_all_allowed_services(self) -> None:
        """Should accept all services in allowed list."""
        allowed = ("hostapd", "dnsmasq", "rose-backend")
        for service in allowed:
            result = sanitize_service_name(service, allowed)
            assert result == service

    def test_invalid_service_raises_error(self) -> None:
        """Should raise ValueError for invalid service."""
        allowed = ("hostapd", "dnsmasq")
        with pytest.raises(ValueError, match="Invalid service"):
            sanitize_service_name("malicious", allowed)

    def test_error_message_shows_allowed_services(self) -> None:
        """Should include allowed services in error message."""
        allowed = ("hostapd", "dnsmasq")
        with pytest.raises(ValueError, match="hostapd") as excinfo:
            sanitize_service_name("invalid", allowed)
        assert "dnsmasq" in str(excinfo.value)

    def test_empty_service_raises_error(self) -> None:
        """Should raise ValueError for empty service name."""
        allowed = ("hostapd", "dnsmasq")
        with pytest.raises(ValueError):
            sanitize_service_name("", allowed)

    def test_service_with_path_raises_error(self) -> None:
        """Should raise ValueError for service with path."""
        allowed = ("hostapd",)
        with pytest.raises(ValueError):
            sanitize_service_name("/etc/passwd", allowed)

    def test_case_sensitive(self) -> None:
        """Should be case sensitive."""
        allowed = ("hostapd",)
        with pytest.raises(ValueError):
            sanitize_service_name("HOSTAPD", allowed)


class TestSanitizeLogLines:
    """Tests for sanitize_log_lines function."""

    def test_valid_lines_returned(self) -> None:
        """Should return valid line count."""
        result = sanitize_log_lines(100)
        assert result == 100

    def test_negative_clamped_to_one(self) -> None:
        """Should clamp negative to 1."""
        result = sanitize_log_lines(-10)
        assert result == 1

    def test_zero_clamped_to_one(self) -> None:
        """Should clamp zero to 1."""
        result = sanitize_log_lines(0)
        assert result == 1

    def test_above_max_clamped(self) -> None:
        """Should clamp values above max to max."""
        result = sanitize_log_lines(2000, max_lines=1000)
        assert result == 1000

    def test_at_max_allowed(self) -> None:
        """Should allow values at max."""
        result = sanitize_log_lines(1000, max_lines=1000)
        assert result == 1000

    def test_custom_max_lines(self) -> None:
        """Should respect custom max_lines parameter."""
        result = sanitize_log_lines(500, max_lines=200)
        assert result == 200

    def test_one_allowed(self) -> None:
        """Should allow 1 line."""
        result = sanitize_log_lines(1)
        assert result == 1


class TestStripAnsiCodes:
    """Tests for strip_ansi_codes function."""

    def test_plain_text_unchanged(self) -> None:
        """Should return plain text unchanged."""
        result = strip_ansi_codes("Hello World")
        assert result == "Hello World"

    def test_remove_red_color(self) -> None:
        """Should remove red color codes."""
        result = strip_ansi_codes("\x1b[31mError\x1b[0m")
        assert result == "Error"

    def test_remove_green_color(self) -> None:
        """Should remove green color codes."""
        result = strip_ansi_codes("\x1b[32mSuccess\x1b[0m")
        assert result == "Success"

    def test_remove_bold(self) -> None:
        """Should remove bold formatting."""
        result = strip_ansi_codes("\x1b[1mBold\x1b[0m")
        assert result == "Bold"

    def test_remove_multiple_codes(self) -> None:
        """Should remove multiple ANSI codes."""
        result = strip_ansi_codes("\x1b[1m\x1b[31mBold Red\x1b[0m")
        assert result == "Bold Red"

    def test_remove_complex_codes(self) -> None:
        """Should remove complex ANSI codes."""
        result = strip_ansi_codes("\x1b[38;5;196mCustom Color\x1b[0m")
        assert result == "Custom Color"

    def test_empty_string_returns_empty(self) -> None:
        """Should return empty string for empty input."""
        result = strip_ansi_codes("")
        assert result == ""

    def test_multiline_text(self) -> None:
        """Should handle multiline text."""
        text = "\x1b[32mLine 1\x1b[0m\n\x1b[31mLine 2\x1b[0m"
        result = strip_ansi_codes(text)
        assert result == "Line 1\nLine 2"


class TestNormalizeMacAddress:
    """Tests for normalize_mac_address function."""

    def test_colon_separated_lowercase(self) -> None:
        """Should normalize colon-separated lowercase."""
        result = normalize_mac_address("aa:bb:cc:dd:ee:ff")
        assert result == "aa:bb:cc:dd:ee:ff"

    def test_colon_separated_uppercase_normalized(self) -> None:
        """Should normalize uppercase to lowercase."""
        result = normalize_mac_address("AA:BB:CC:DD:EE:FF")
        assert result == "aa:bb:cc:dd:ee:ff"

    def test_dash_separated_normalized(self) -> None:
        """Should normalize dash-separated format."""
        result = normalize_mac_address("AA-BB-CC-DD-EE-FF")
        assert result == "aa:bb:cc:dd:ee:ff"

    def test_no_separator_normalized(self) -> None:
        """Should normalize format without separators."""
        result = normalize_mac_address("AABBCCDDEEFF")
        assert result == "aa:bb:cc:dd:ee:ff"

    def test_dot_separated_normalized(self) -> None:
        """Should normalize dot-separated format."""
        result = normalize_mac_address("AA.BB.CC.DD.EE.FF")
        assert result == "aa:bb:cc:dd:ee:ff"

    def test_cisco_format_normalized(self) -> None:
        """Should normalize Cisco format (xxxx.xxxx.xxxx)."""
        # After removing dots: aabbccddeeff
        result = normalize_mac_address("aabb.ccdd.eeff")
        assert result == "aa:bb:cc:dd:ee:ff"

    def test_mixed_case_normalized(self) -> None:
        """Should normalize mixed case."""
        result = normalize_mac_address("Aa:Bb:Cc:Dd:Ee:Ff")
        assert result == "aa:bb:cc:dd:ee:ff"

    def test_invalid_length_returns_lowercase_original(self) -> None:
        """Should return lowercase original for invalid length."""
        result = normalize_mac_address("AABBCC")
        assert result == "aabbcc"

    def test_empty_returns_empty(self) -> None:
        """Should return empty for empty input."""
        result = normalize_mac_address("")
        assert result == ""

    def test_too_long_returns_lowercase_original(self) -> None:
        """Should return lowercase original for too-long input."""
        result = normalize_mac_address("AABBCCDDEEFF00")
        assert result == "aabbccddeeff00"

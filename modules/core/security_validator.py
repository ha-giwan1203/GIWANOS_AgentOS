#!/usr/bin/env python3
"""
VELOS Security Validator
Centralized input validation and sanitization for VELOS system.
"""

import html
import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse


class VelosSecurityValidator:
    """Security validation and sanitization for VELOS inputs"""

    # Safe characters for different input types
    SAFE_FILENAME_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")
    SAFE_PATH_PATTERN = re.compile(r"^[a-zA-Z0-9._/\\:-]+$")
    SAFE_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

    # Maximum lengths for inputs
    MAX_FILENAME_LENGTH = 255
    MAX_PATH_LENGTH = 4096
    MAX_IDENTIFIER_LENGTH = 128
    MAX_TEXT_LENGTH = 65535
    MAX_TAG_LENGTH = 64

    # Dangerous SQL patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"[';\"--]",
        r"(\bOR\b.*=.*=|\bAND\b.*=.*=)",
        r"(\bUNION\b.*\bSELECT\b)",
    ]

    def __init__(self):
        self.sql_pattern = re.compile("|".join(self.SQL_INJECTION_PATTERNS), re.IGNORECASE)

    def validate_filename(self, filename: str, max_length: Optional[int] = None) -> bool:
        """Validate filename for safety"""
        if not filename or not isinstance(filename, str):
            return False

        max_len = max_length or self.MAX_FILENAME_LENGTH
        if len(filename) > max_len:
            return False

        # Check for dangerous characters
        if not self.SAFE_FILENAME_PATTERN.match(filename):
            return False

        # Check for reserved names (Windows)
        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        }

        if filename.upper().split(".")[0] in reserved_names:
            return False

        return True

    def sanitize_filename(self, filename: str, replacement: str = "_") -> str:
        """Sanitize filename by removing/replacing dangerous characters"""
        if not filename:
            return "untitled"

        # Remove/replace dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', replacement, filename)

        # Limit length
        if len(sanitized) > self.MAX_FILENAME_LENGTH:
            name, ext = os.path.splitext(sanitized)
            sanitized = name[: self.MAX_FILENAME_LENGTH - len(ext)] + ext

        # Ensure not empty and doesn't start with dot (hidden file)
        if not sanitized or sanitized.startswith("."):
            sanitized = "file" + sanitized

        return sanitized

    def validate_file_path(self, path: str, allowed_roots: Optional[List[str]] = None) -> bool:
        """Validate file path for safety and containment"""
        if not path or not isinstance(path, str):
            return False

        if len(path) > self.MAX_PATH_LENGTH:
            return False

        try:
            # Normalize path to prevent traversal attacks
            normalized_path = os.path.normpath(os.path.abspath(path))

            # Check for path traversal attempts
            if ".." in path or "~" in path:
                return False

            # If allowed roots specified, verify path is within them
            if allowed_roots:
                path_obj = Path(normalized_path)
                allowed = False
                for root in allowed_roots:
                    root_obj = Path(os.path.normpath(os.path.abspath(root)))
                    try:
                        # Check if path is within allowed root
                        path_obj.relative_to(root_obj)
                        allowed = True
                        break
                    except ValueError:
                        continue
                if not allowed:
                    return False

            return True

        except (OSError, ValueError):
            return False

    def sanitize_path(self, path: str, allowed_roots: Optional[List[str]] = None) -> Optional[str]:
        """Sanitize file path"""
        if not path:
            return None

        try:
            # Basic cleanup
            cleaned_path = os.path.normpath(path)

            # Remove dangerous patterns
            cleaned_path = cleaned_path.replace("..", "").replace("~", "")

            # Validate against allowed roots if specified
            if allowed_roots and not self.validate_file_path(cleaned_path, allowed_roots):
                return None

            return cleaned_path

        except Exception:
            return None

    def validate_sql_input(self, input_text: str) -> bool:
        """Validate input for SQL injection attempts"""
        if not input_text or not isinstance(input_text, str):
            return True  # Empty is safe

        # Check for SQL injection patterns
        if self.sql_pattern.search(input_text):
            return False

        return True

    def sanitize_sql_input(self, input_text: str, max_length: Optional[int] = None) -> str:
        """Sanitize input for safe SQL usage"""
        if not input_text:
            return ""

        max_len = max_length or self.MAX_TEXT_LENGTH

        # Truncate if too long
        if len(input_text) > max_len:
            input_text = input_text[:max_len]

        # Remove null bytes and control characters
        sanitized = input_text.replace("\x00", "").replace("\r", "").replace("\x1a", "")

        # HTML encode potentially dangerous characters
        sanitized = html.escape(sanitized)

        return sanitized

    def validate_identifier(self, identifier: str) -> bool:
        """Validate identifier (variable names, table names, etc.)"""
        if not identifier or not isinstance(identifier, str):
            return False

        if len(identifier) > self.MAX_IDENTIFIER_LENGTH:
            return False

        return bool(self.SAFE_IDENTIFIER_PATTERN.match(identifier))

    def validate_tags(self, tags: List[str]) -> bool:
        """Validate list of tags"""
        if not isinstance(tags, list):
            return False

        if len(tags) > 50:  # Reasonable tag limit
            return False

        for tag in tags:
            if not isinstance(tag, str):
                return False
            if len(tag) > self.MAX_TAG_LENGTH:
                return False
            if not re.match(r"^[a-zA-Z0-9_-]+$", tag):
                return False

        return True

    def sanitize_tags(self, tags: List[str]) -> List[str]:
        """Sanitize list of tags"""
        if not isinstance(tags, list):
            return []

        sanitized_tags = []
        for tag in tags[:50]:  # Limit number of tags
            if isinstance(tag, str):
                # Clean tag: alphanumeric, underscore, hyphen only
                clean_tag = re.sub(r"[^a-zA-Z0-9_-]", "", tag)
                if clean_tag and len(clean_tag) <= self.MAX_TAG_LENGTH:
                    sanitized_tags.append(clean_tag)

        return sanitized_tags

    def validate_memory_record(self, record: Dict[str, Any]) -> bool:
        """Validate a complete memory record"""
        required_fields = ["ts", "role", "insight"]

        # Check required fields
        for field in required_fields:
            if field not in record:
                return False

        # Validate timestamp
        try:
            ts = int(record["ts"])
            if ts < 0 or ts > 2147483647:  # Reasonable timestamp range
                return False
        except (ValueError, TypeError):
            return False

        # Validate role
        if not isinstance(record["role"], str) or len(record["role"]) > 32:
            return False
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", record["role"]):
            return False

        # Validate insight
        if not isinstance(record["insight"], str) or len(record["insight"]) > self.MAX_TEXT_LENGTH:
            return False
        if not self.validate_sql_input(record["insight"]):
            return False

        # Validate optional fields
        if "raw" in record:
            if not isinstance(record["raw"], str) or len(record["raw"]) > self.MAX_TEXT_LENGTH:
                return False
            if not self.validate_sql_input(record["raw"]):
                return False

        if "tags" in record:
            if not self.validate_tags(record["tags"]):
                return False

        return True

    def sanitize_memory_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize a memory record for safe storage"""
        sanitized = {}

        # Sanitize timestamp
        try:
            sanitized["ts"] = max(0, min(2147483647, int(record.get("ts", 0))))
        except (ValueError, TypeError):
            sanitized["ts"] = 0

        # Sanitize role
        role = record.get("role", "unknown")
        if isinstance(role, str):
            role = re.sub(r"[^a-zA-Z0-9_]", "", role)[:32]
        if not role:
            role = "unknown"
        sanitized["role"] = role

        # Sanitize insight
        insight = record.get("insight", "")
        if isinstance(insight, str):
            sanitized["insight"] = self.sanitize_sql_input(insight)
        else:
            sanitized["insight"] = ""

        # Sanitize optional raw field
        if "raw" in record:
            raw = record["raw"]
            if isinstance(raw, str):
                sanitized["raw"] = self.sanitize_sql_input(raw)
            else:
                sanitized["raw"] = str(raw) if raw is not None else ""

        # Sanitize tags
        if "tags" in record:
            sanitized["tags"] = self.sanitize_tags(record["tags"])

        return sanitized

    def create_safe_sql_params(self, **kwargs) -> tuple:
        """Create safe SQL parameters from keyword arguments"""
        params = []
        for key, value in kwargs.items():
            if isinstance(value, str):
                params.append(self.sanitize_sql_input(value))
            elif isinstance(value, (int, float)):
                params.append(value)
            elif isinstance(value, list):
                if key == "tags":
                    params.append(self.sanitize_tags(value))
                else:
                    params.append([self.sanitize_sql_input(str(item)) for item in value])
            else:
                params.append(str(value) if value is not None else "")

        return tuple(params)


# Global instance for easy access
_security_validator = VelosSecurityValidator()


# Convenience functions
def validate_filename(filename: str) -> bool:
    """Validate filename for safety"""
    return _security_validator.validate_filename(filename)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename"""
    return _security_validator.sanitize_filename(filename)


def validate_path(path: str, allowed_roots: Optional[List[str]] = None) -> bool:
    """Validate file path"""
    return _security_validator.validate_file_path(path, allowed_roots)


def sanitize_path(path: str, allowed_roots: Optional[List[str]] = None) -> Optional[str]:
    """Sanitize file path"""
    return _security_validator.sanitize_path(path, allowed_roots)


def validate_sql_safe(input_text: str) -> bool:
    """Validate input is SQL-safe"""
    return _security_validator.validate_sql_input(input_text)


def sanitize_for_sql(input_text: str) -> str:
    """Sanitize input for SQL"""
    return _security_validator.sanitize_sql_input(input_text)


def validate_memory_record(record: Dict[str, Any]) -> bool:
    """Validate memory record"""
    return _security_validator.validate_memory_record(record)


def sanitize_memory_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize memory record"""
    return _security_validator.sanitize_memory_record(record)


if __name__ == "__main__":
    # Self-validation tests
    print("=== VELOS Security Validator Self-Validation ===")

    validator = VelosSecurityValidator()

    # Test filename validation
    test_filenames = [
        "valid_file.txt",
        "../dangerous.txt",  # Path traversal
        "file<script>.txt",  # HTML injection
        "CON",  # Reserved name
        "valid-file_123.py",  # Valid
    ]

    print("Filename validation:")
    for filename in test_filenames:
        valid = validator.validate_filename(filename)
        sanitized = validator.sanitize_filename(filename)
        print(f"  {filename}: Valid={valid}, Sanitized='{sanitized}'")

    # Test SQL injection detection
    test_sql_inputs = [
        "normal text",
        "'; DROP TABLE users; --",
        "user OR 1=1",
        "UNION SELECT password FROM users",
        "safe string with numbers 123",
    ]

    print("\nSQL injection detection:")
    for sql_input in test_sql_inputs:
        safe = validator.validate_sql_input(sql_input)
        sanitized = validator.sanitize_sql_input(sql_input)
        print(f"  '{sql_input}': Safe={safe}")

    # Test memory record validation
    test_record = {
        "ts": 1634567890,
        "role": "user",
        "insight": "This is a test insight",
        "raw": "Raw data here",
        "tags": ["test", "validation", "security"],
    }

    valid_record = validator.validate_memory_record(test_record)
    sanitized_record = validator.sanitize_memory_record(test_record)

    print(f"\nMemory record validation: {valid_record}")
    print(f"Sanitized record: {sanitized_record}")

    print("=== Self-validation complete ===")

"""
IDShield-X: Security, Validation & Access Control Module (Step 10)
Smart India Hackathon 2026 | Problem Statement: SIH26188
Ministry of Home Affairs (MHA) | Sashastra Seema Bal (SSB)

Implements:
1. Binary Magic-Byte File Header Inspection (PNG, JPEG, PDF, WEBP)
2. Disguised Executable Defense (Blocks PE/EXE, ELF, Mach-O, scripts)
3. Path Traversal & Filename Sanitization (prohibits '..', slashes, null bytes)
4. Sliding Window Rate Limiting (mitigates brute force / DoS attempts)
5. Demo Role-Based Access Control (RBAC: OPERATOR vs SUPERVISOR)
6. Safe Error Response Sanitization
"""

import re
import time
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Supported file magic signatures
MAGIC_SIGNATURES = {
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
    "pdf": b"%PDF",
    "webp": b"RIFF"  # and bytes 8..12 == b"WEBP"
}

# Malicious / executable binary signatures to reject immediately
BLOCKED_EXECUTABLE_SIGNATURES = [
    b"MZ",              # Windows PE executable
    b"\x7fELF",          # Linux ELF binary
    b"\xca\xfe\xba\xbe", # Java class or Mach-O fat binary
    b"\xfe\xed\xfa\xce", # Mach-O binary
    b"\xfe\xed\xfa\xcf", # Mach-O 64-bit binary
    b"<!DOCTYPE",       # HTML disguised as image
    b"<html",           # HTML
    b"<?php",           # PHP script
    b"#!/bin/",         # Shell script
]


def sanitize_filename(filename: str) -> str:
    """
    Strips directory traversal sequences, path separators, and null bytes.
    Ensures filename contains only safe alphanumeric characters, dots, and dashes.
    """
    if not filename:
        return "unnamed_document.png"

    # Remove path traversal tokens
    clean = filename.replace("..", "").replace("/", "").replace("\\", "").replace("\x00", "")
    # Remove potentially dangerous characters
    clean = re.sub(r"[^\w\.\-\_]", "_", clean)
    # Ensure at least a safe base
    if not clean or clean.startswith("."):
        clean = f"doc_{clean}"
    return clean


def validate_file_bytes(data: bytes, declared_filename: str) -> Tuple[bool, str]:
    """
    Validates binary header magic bytes against the declared file extension.
    Guarantees that an executable or script disguised as an image is rejected.
    """
    if len(data) == 0:
        return False, "File is completely empty (0 bytes)."

    if len(data) > 10 * 1024 * 1024:
        return False, f"File exceeds maximum allowed size of 10 MB ({round(len(data)/(1024*1024), 2)} MB)."

    # 1. Block dangerous executable signatures
    for sig in BLOCKED_EXECUTABLE_SIGNATURES:
        if data.startswith(sig) or data[:64].lower().startswith(sig.lower()):
            return False, "Security Alert: Executable or script payload detected. Upload rejected."

    # 2. Extract declared extension
    ext = Path(declared_filename).suffix.lower().replace(".", "")
    if ext not in ("png", "jpg", "jpeg", "pdf", "webp"):
        return False, f"Unsupported file extension '.{ext}'. Allowed: .png, .jpg, .jpeg, .pdf, .webp."

    # 3. Check magic byte match
    if ext == "png":
        if not data.startswith(MAGIC_SIGNATURES["png"]):
            return False, "Corrupted or invalid PNG binary header (Magic bytes do not match PNG standard)."
    elif ext in ("jpg", "jpeg"):
        if not data.startswith(MAGIC_SIGNATURES["jpg"]):
            return False, "Corrupted or invalid JPEG binary header (Magic bytes do not match JPEG SOI marker)."
    elif ext == "pdf":
        if not data.startswith(MAGIC_SIGNATURES["pdf"]):
            return False, "Corrupted or invalid PDF header (Missing %PDF header)."
    elif ext == "webp":
        if not (data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP"):
            return False, "Corrupted or invalid WEBP header (Missing RIFF/WEBP container marker)."

    return True, "File verified: Extension and binary magic bytes align securely."


class TokenBucketRateLimiter:
    """
    Sliding window in-memory rate limiter for border inspection endpoints.
    Protects checkpoint API against denial-of-service or automated brute force.
    """
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.client_records: Dict[str, list] = {}

    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        timestamps = self.client_records.get(client_ip, [])

        # Prune expired timestamps
        valid_timestamps = [t for t in timestamps if now - t < self.window_seconds]
        self.client_records[client_ip] = valid_timestamps

        remaining = self.max_requests - len(valid_timestamps)
        if len(valid_timestamps) >= self.max_requests:
            return False, 0

        valid_timestamps.append(now)
        return True, remaining - 1


class RoleBasedAccessControl:
    """
    Demo Role-Based Access Control (RBAC).
    - OPERATOR: Routine document ingestion, OCR, validation, and risk review.
    - SUPERVISOR: Access to cryptographic audit verification, settings, and checkpoint configuration.
    """
    ROLES = {
        "OPERATOR": {
            "title": "Sub-Inspector on Duty",
            "permissions": ["screening:create", "screening:read", "screening:save", "risk:read"]
        },
        "SUPERVISOR": {
            "title": "Station Commandant / Inspector",
            "permissions": ["screening:create", "screening:read", "screening:save", "risk:read", "audit:verify", "settings:manage"]
        }
    }

    def __init__(self, current_role: str = "OPERATOR"):
        self.current_role = current_role if current_role in self.ROLES else "OPERATOR"

    def set_role(self, role: str) -> bool:
        if role.upper() in self.ROLES:
            self.current_role = role.upper()
            return True
        return False

    def can_access(self, permission: str) -> bool:
        return permission in self.ROLES[self.current_role]["permissions"]

    def get_role_info(self) -> Dict[str, Any]:
        return {
            "current_role": self.current_role,
            "title": self.ROLES[self.current_role]["title"],
            "permissions": self.ROLES[self.current_role]["permissions"]
        }


# Global Singletons
rate_limiter = TokenBucketRateLimiter(max_requests=100, window_seconds=60)
rbac_manager = RoleBasedAccessControl(current_role="OPERATOR")

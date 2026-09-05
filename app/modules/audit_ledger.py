"""
IDShield-X: Screening History & Cryptographic Audit Trail Module (Step 8)
Smart India Hackathon 2026 | Problem Statement: SIH26188
Ministry of Home Affairs (MHA) | Sashastra Seema Bal (SSB)

Provides:
1. Minimal Screening History Registry (zero retention of raw documents or biometrics)
2. Cryptographic SHA-256 Tamper-Evident Audit Trail Ledger
3. Search and filtering across historical screening records
4. Cryptographic chain integrity verification
"""

import os
import json
import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.core import config

# Storage directories
HISTORY_DIR = config.DATA_DIR / "history"
AUDIT_DIR = config.DATA_DIR / "audit"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = HISTORY_DIR / "screenings.json"
AUDIT_FILE = AUDIT_DIR / "audit_chain.json"


def _calc_sha256(data_str: str) -> str:
    """Computes SHA-256 hex digest for cryptographic chaining."""
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()


class AuditTrailLedger:
    """
    Cryptographic SHA-256 Tamper-Evident Audit Ledger.
    Secures chain of custody for all border checkpoint screening events.
    Blocks are cryptographically chained: Hash_n = SHA256(Index + Time + Event + ScreeningID + PrevHash)
    """
    def __init__(self, filepath: Path = AUDIT_FILE):
        self.filepath = filepath
        self.chain: List[Dict[str, Any]] = []
        self._load_or_initialize()

    def _load_or_initialize(self):
        if self.filepath.exists() and self.filepath.stat().st_size > 0:
            try:
                self.chain = json.loads(self.filepath.read_text(encoding="utf-8"))
                return
            except Exception:
                self.chain = []

        # Initialize with Genesis Block
        genesis_block = {
            "index": 0,
            "timestamp": "2026-09-01T00:00:00Z",
            "event_type": "GENESIS_LEDGER_INITIALIZED",
            "screening_id": "SYSTEM_ROOT",
            "actor_role": "SSB_COMMAND_CENTRAL",
            "details_summary": "IDShield-X Cryptographic Audit Trail Initialized at Raxaul ICP Border Checkpost.",
            "prev_hash": "0" * 64,
            "hash": _calc_sha256("GENESIS_BLOCK_0_SSB_IDSHIELD_X_SECURE_TRAIL")
        }
        self.chain = [genesis_block]
        self._save()

    def _save(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(json.dumps(self.chain, indent=2), encoding="utf-8")

    def record_event(
        self,
        event_type: str,
        screening_id: str,
        details_summary: str,
        actor_role: str = "Sub-Inspector on Duty"
    ) -> Dict[str, Any]:
        """
        Appends a new cryptographically chained audit block.
        Ensures NO sensitive biometric vectors or raw document images are logged.
        """
        prev_block = self.chain[-1]
        new_index = len(self.chain)
        timestamp = datetime.utcnow().isoformat() + "Z"

        block_payload = f"{new_index}:{timestamp}:{event_type}:{screening_id}:{actor_role}:{details_summary}:{prev_block['hash']}"
        new_hash = _calc_sha256(block_payload)

        block = {
            "index": new_index,
            "timestamp": timestamp,
            "event_type": event_type,
            "screening_id": screening_id,
            "actor_role": actor_role,
            "details_summary": details_summary,
            "prev_hash": prev_block["hash"],
            "hash": new_hash
        }

        self.chain.append(block)
        self._save()
        return block

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verifies every block's SHA-256 hash against its predecessor.
        Returns whether the cryptographic chain is intact or tampered.
        """
        if not self.chain:
            return {"valid": False, "total_blocks": 0, "error": "Ledger is empty"}

        for i in range(1, len(self.chain)):
            curr = self.chain[i]
            prev = self.chain[i - 1]

            # 1. Verify previous hash pointer
            if curr["prev_hash"] != prev["hash"]:
                return {
                    "valid": False,
                    "tampered_block_index": curr["index"],
                    "error": f"Broken pointer at block {curr['index']}: expected {prev['hash']}, got {curr['prev_hash']}"
                }

            # 2. Re-compute current hash
            block_payload = f"{curr['index']}:{curr['timestamp']}:{curr['event_type']}:{curr['screening_id']}:{curr['actor_role']}:{curr['details_summary']}:{curr['prev_hash']}"
            recomputed = _calc_sha256(block_payload)

            if curr["hash"] != recomputed:
                return {
                    "valid": False,
                    "tampered_block_index": curr["index"],
                    "error": f"Cryptographic mismatch at block {curr['index']}: block hash altered"
                }

        return {
            "valid": True,
            "total_blocks": len(self.chain),
            "latest_block_hash": self.chain[-1]["hash"],
            "integrity_status": "CRYPTOGRAPHICALLY_VERIFIED_INTACT"
        }

    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns recent audit events in reverse chronological order."""
        return list(reversed(self.chain[-limit:]))


class ScreeningHistoryStore:
    """
    Minimal Screening Metadata Store for Academic Prototype.
    Stores ONLY high-level operational parameters:
    - screening_id, document_type, timestamp, processing_status, risk_status, field_count
    - ZERO raw image content or biometric vectors.
    """
    def __init__(self, filepath: Path = HISTORY_FILE):
        self.filepath = filepath
        self.records: List[Dict[str, Any]] = []
        self._load_or_initialize()

    def _load_or_initialize(self):
        if self.filepath.exists() and self.filepath.stat().st_size > 0:
            try:
                self.records = json.loads(self.filepath.read_text(encoding="utf-8"))
                return
            except Exception:
                self.records = []

        # Seed with initial synthetic demo records for realistic testing
        self.records = [
            {
                "screening_id": "SCR-20260901-081245",
                "document_type": "passport",
                "timestamp": "2026-09-01T08:12:45Z",
                "processing_status": "COMPLETED",
                "risk_status": "Low Concern",
                "risk_level": "LOW",
                "summary": "Standard tourist passport. Baseline fields and photo matched.",
                "station_id": "SSB-BOP-RAXAUL-01",
                "actor": "Sub-Inspector R. Kumar"
            },
            {
                "screening_id": "SCR-20260901-114522",
                "document_type": "visa",
                "timestamp": "2026-09-01T11:45:22Z",
                "processing_status": "COMPLETED",
                "risk_status": "Review Required",
                "risk_level": "MEDIUM",
                "summary": "Transit visa with non-standard stay duration. Officer visual check requested.",
                "station_id": "SSB-BOP-RAXAUL-01",
                "actor": "Sub-Inspector S. Singh"
            },
            {
                "screening_id": "SCR-20260902-142010",
                "document_type": "passport",
                "timestamp": "2026-09-02T14:20:10Z",
                "processing_status": "FLAGGED",
                "risk_status": "High Concern",
                "risk_level": "HIGH",
                "summary": "Document expired on 2020-01-01. Diverted to secondary inspection.",
                "station_id": "SSB-BOP-RAXAUL-01",
                "actor": "Sub-Inspector R. Kumar"
            }
        ]
        self._save()

    def _save(self):
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(json.dumps(self.records, indent=2), encoding="utf-8")

    def record_screening(
        self,
        document_type: str,
        risk_status: str,
        risk_level: str,
        summary_note: str,
        screening_id: Optional[str] = None,
        actor: str = "Sub-Inspector on Duty"
    ) -> Dict[str, Any]:
        """
        Creates and stores a minimal screening record.
        Strictly excludes any biometric images, full OCR texts, or raw files.
        """
        now = datetime.utcnow()
        sid = screening_id or f"SCR-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        record = {
            "screening_id": sid,
            "document_type": (document_type or "passport").lower(),
            "timestamp": now.isoformat() + "Z",
            "processing_status": "FLAGGED" if risk_status == "High Concern" else "COMPLETED",
            "risk_status": risk_status,
            "risk_level": risk_level,
            "summary": summary_note,
            "station_id": config.CHECKPOINT_ID,
            "actor": actor
        }

        self.records.insert(0, record)
        self._save()
        return record

    def search_and_filter(
        self,
        query: Optional[str] = None,
        document_type: Optional[str] = None,
        status: Optional[str] = None,
        date_str: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Filters screenings by keyword query, doc category, risk status, or date."""
        filtered = self.records

        if query:
            q = query.lower()
            filtered = [r for r in filtered if q in r["screening_id"].lower() or q in r["summary"].lower()]

        if document_type and document_type != "all":
            filtered = [r for r in filtered if r["document_type"] == document_type.lower()]

        if status and status != "all":
            filtered = [r for r in filtered if r["risk_status"].lower() == status.lower() or r["processing_status"].lower() == status.lower()]

        if date_str:
            filtered = [r for r in filtered if r["timestamp"].startswith(date_str)]

        return filtered

    def get_by_id(self, screening_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single screening record by ID."""
        for r in self.records:
            if r["screening_id"].upper() == screening_id.upper():
                return r
        return None


# Global Singletons
audit_ledger = AuditTrailLedger()
history_store = ScreeningHistoryStore()

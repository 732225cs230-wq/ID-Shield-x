"""
IDShield-X Core Configuration & Settings
"""
import os
from pathlib import Path

# Base Directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
AUDIT_DIR = DATA_DIR / "audit"
SYNTHETIC_DIR = DATA_DIR / "synthetic_samples"
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

# Ensure runtime directories exist
for directory in [UPLOAD_DIR, AUDIT_DIR, SYNTHETIC_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# System Settings
PROJECT_NAME = os.getenv("PROJECT_NAME", "IDShield-X")
VERSION = "1.0.0"
DESCRIPTION = "AI-Based Fake Identity & Document Screening System (SSB, Police II Div, MHA)"
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))
BASE_URL = os.getenv("BASE_URL", f"http://{HOST}:{PORT}")
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")

# Checkpoint Metadata (SSB MHA)
CHECKPOINT_ID = os.getenv("CHECKPOINT_ID", "SSB-BOP-RAXAUL-01")
CHECKPOINT_NAME = os.getenv("CHECKPOINT_NAME", "Raxaul Integrated Checkpost (India-Nepal Border)")
OFFICER_STATION = os.getenv("OFFICER_STATION", "SSB 47th Battalion, Frontier HQ Patna")

# Upload Security & Validation Settings (Step 2)
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "application/octet-stream"  # Fallback for some browsers
}

# Document Types Supported across 5 Categories (17 Profiles + legacy aliases)
DOCUMENT_CATEGORIES = {
    # 1. Identity Documents
    "aadhaar": "Aadhaar Card (UIDAI Masked Reference)",
    "pan_card": "PAN Card (Income Tax Department)",
    "voter_id": "Voter ID Card (Election Commission EPIC)",
    "passport": "Passport (ICAO Doc 9303 TD3)",
    "driving_license": "Driving Licence (State Transport / Sarathi)",
    # Legacy alias
    "national_id": "National Identity Card (Aadhaar / Voter ID)",

    # 2. Travel / Government Documents
    "visa": "Travel / Entry Visa",
    "permit": "Border Transit Permit / Local Pass",

    # 3. Civil Certificates
    "birth_certificate": "Birth Certificate (Civil Registration)",
    "death_certificate": "Death Certificate (Civil Registration)",

    # 4. Educational Documents
    "marksheet_10": "10th Marksheet (Secondary School / SSC)",
    "marksheet_11": "11th Marksheet (Higher Secondary First Year / HSC)",
    "marksheet_12": "12th Marksheet (Senior Secondary / HSC Class 12)",
    "marksheet_college": "College Marksheet (University Semester Grade Card)",
    "degree_certificate": "Degree Certificate (University Graduation Scroll)",
    "provisional_certificate": "Provisional Certificate (Interim University Degree)",

    # 5. Property Documents
    "property_deed": "Property / Sale Deed (Sub-Registrar Conveyance)",
    "land_document": "Land Document (Revenue Record / Khasra-Khatauni / Patta)"
}

# OCR Field Extraction Blueprint (Architecture for Step 5)
OCR_FIELD_BLUEPRINTS = {
    "passport": [
        {"field": "name", "label": "Full Name", "source": "VIZ / MRZ Line 1", "required": True},
        {"field": "passport_number", "label": "Passport Number", "source": "VIZ / MRZ Line 2 (Pos 1-9)", "required": True},
        {"field": "nationality", "label": "Nationality", "source": "VIZ / MRZ Line 2 (Pos 11-13)", "required": True},
        {"field": "dob", "label": "Date of Birth (YYMMDD)", "source": "VIZ / MRZ Line 2 (Pos 14-19)", "required": True},
        {"field": "expiry_date", "label": "Date of Expiry (YYMMDD)", "source": "VIZ / MRZ Line 2 (Pos 22-27)", "required": True},
        {"field": "gender", "label": "Gender (M/F/X)", "source": "VIZ / MRZ Line 2 (Pos 21)", "required": True}
    ],
    "visa": [
        {"field": "visa_number", "label": "Visa Number", "source": "Upper Right VIZ", "required": True},
        {"field": "visa_type", "label": "Visa Type (Transit/Tourist/Business)", "source": "Category Field", "required": True},
        {"field": "entry_validity", "label": "Entry Validity (Valid Until)", "source": "Validity Zone", "required": True},
        {"field": "stay_duration", "label": "Stay Duration (Days / Months)", "source": "Duration of Stay", "required": True}
    ],
    "national_id": [
        {"field": "name", "label": "Full Name", "source": "Primary Header", "required": True},
        {"field": "id_number", "label": "Identity Number", "source": "Central ID Zone", "required": True},
        {"field": "dob", "label": "Date of Birth / Year", "source": "DOB Label", "required": True},
        {"field": "gender", "label": "Gender", "source": "Demographic Field", "required": False}
    ],
    "driving_license": [
        {"field": "name", "label": "Driver Name", "source": "Licensee Field", "required": True},
        {"field": "license_number", "label": "DL Number", "source": "License Header", "required": True},
        {"field": "validity", "label": "Valid Till (Non-Transport)", "source": "Validity Block", "required": True},
        {"field": "dob", "label": "Date of Birth", "source": "Demographics", "required": True}
    ],
    "permit": [
        {"field": "permit_number", "label": "Border Pass ID", "source": "Header", "required": True},
        {"field": "holder_name", "label": "Holder Name", "source": "Subject Field", "required": True},
        {"field": "destination", "label": "Permitted Sector / Route", "source": "Transit Route", "required": True},
        {"field": "validity_window", "label": "Validity Window", "source": "Permit Duration", "required": True}
    ]
}

# Module Flags
OFFLINE_MODE = True
ENABLE_OCR = True
ENABLE_VALIDATION = True
ENABLE_TAMPERING = True
ENABLE_FACE_MATCH = True
ENABLE_AUDIT_LEDGER = True

"""
IDShield-X SIH Mandatory Forensic Modules:
- Module 1: OCR Extraction & MRZ Parsing (ocr_engine)
- Module 2: Document Rule Validation (field_validator)
- Module 3: Tampering & Authenticity Analysis (authenticity_analyzer)
- Module 4: Face Detection & Demo Verification (face_engine)
"""
from . import ocr_engine
from . import field_validator
from . import authenticity_analyzer
from . import face_engine
from . import risk_engine
from . import audit_ledger
from . import analytics_engine
from . import security_guard



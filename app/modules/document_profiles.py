"""
IDShield-X: Document Profile Schema Registry Module
Multi-Document Intelligent Screening Platform (SIH26188)

Defines master document profiles across 5 functional categories and 17 document types.
Each profile specifies:
- Display metadata and category
- Expected fields and data types
- Validation rules and constraints
- Whether face detection/verification applies
- Whether authenticity checks apply
- Description and human verification notice
"""

from typing import Dict, Any, List, Optional

# 5 Master Categories
CATEGORY_IDENTITY = "IDENTITY"
CATEGORY_TRAVEL_GOVT = "TRAVEL / GOVERNMENT"
CATEGORY_CIVIL = "CIVIL CERTIFICATES"
CATEGORY_EDUCATION = "EDUCATION"
CATEGORY_PROPERTY = "PROPERTY"

CATEGORIES = [
    CATEGORY_IDENTITY,
    CATEGORY_TRAVEL_GOVT,
    CATEGORY_CIVIL,
    CATEGORY_EDUCATION,
    CATEGORY_PROPERTY
]

# 17 Master Document Profiles
DOCUMENT_PROFILES: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # 1. IDENTITY DOCUMENTS
    # =========================================================================
    "aadhaar": {
        "id": "aadhaar",
        "name": "Aadhaar Card",
        "category": CATEGORY_IDENTITY,
        "icon": "🪪",
        "code": "AADHAAR-UID",
        "face_applicable": True,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (1.40, 1.70),  # Standard ID-1 card format
        "description": "Synthetic demographic identity reference (masked reference number only).",
        "fields": [
            {"key": "name", "label": "Full Name", "type": "string", "required": True},
            {"key": "masked_aadhaar", "label": "Masked Aadhaar Ref", "type": "masked_number", "required": True},
            {"key": "dob", "label": "Date / Year of Birth", "type": "date", "required": True},
            {"key": "gender", "label": "Gender", "type": "gender", "required": True},
            {"key": "address", "label": "Address / Pincode", "type": "address", "required": False}
        ]
    },

    "pan_card": {
        "id": "pan_card",
        "name": "PAN Card",
        "category": CATEGORY_IDENTITY,
        "icon": "💳",
        "code": "IN-ITD-PAN",
        "face_applicable": False,  # Live matching not applicable for standard tax token
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (1.45, 1.75),
        "description": "Permanent Account Number tax identification credential.",
        "fields": [
            {"key": "name", "label": "Cardholder Name", "type": "string", "required": True},
            {"key": "pan_number", "label": "PAN Number", "type": "pan_format", "required": True},
            {"key": "father_name", "label": "Father's Name", "type": "string", "required": False},
            {"key": "dob", "label": "Date of Birth", "type": "date", "required": True}
        ]
    },

    "voter_id": {
        "id": "voter_id",
        "name": "Voter ID (EPIC)",
        "category": CATEGORY_IDENTITY,
        "icon": "🗳️",
        "code": "ECI-EPIC-ID",
        "face_applicable": True,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (1.40, 1.75),
        "description": "Electoral Photo Identity Card issued by Election Commission.",
        "fields": [
            {"key": "name", "label": "Elector Name", "type": "string", "required": True},
            {"key": "epic_number", "label": "EPIC Reference Number", "type": "epic_format", "required": True},
            {"key": "dob_or_age", "label": "Date of Birth / Age", "type": "string", "required": True},
            {"key": "constituency", "label": "Constituency", "type": "string", "required": False},
            {"key": "address", "label": "Address", "type": "address", "required": False}
        ]
    },

    "passport": {
        "id": "passport",
        "name": "Passport",
        "category": CATEGORY_IDENTITY,
        "icon": "🛂",
        "code": "ICAO-DOC-9303-TD3",
        "face_applicable": True,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (1.15, 1.85),
        "description": "International travel identity document adhering to ICAO Doc 9303 TD3.",
        "fields": [
            {"key": "name", "label": "Full Name", "type": "string", "required": True},
            {"key": "passport_number", "label": "Passport Number", "type": "passport_format", "required": True},
            {"key": "nationality", "label": "Nationality", "type": "country_code", "required": True},
            {"key": "dob", "label": "Date of Birth", "type": "date", "required": True},
            {"key": "expiry_date", "label": "Date of Expiry", "type": "expiry_date", "required": True},
            {"key": "gender", "label": "Gender", "type": "gender", "required": True}
        ]
    },

    "driving_license": {
        "id": "driving_license",
        "name": "Driving Licence",
        "category": CATEGORY_IDENTITY,
        "icon": "🚗",
        "code": "STATE-DL-SARATHI",
        "face_applicable": True,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (1.40, 1.75),
        "description": "Motor vehicle driving licence issued by state transport authorities.",
        "fields": [
            {"key": "name", "label": "Licence Holder Name", "type": "string", "required": True},
            {"key": "license_number", "label": "Licence Number", "type": "dl_format", "required": True},
            {"key": "dob", "label": "Date of Birth", "type": "date", "required": True},
            {"key": "issue_date", "label": "Issue Date", "type": "date", "required": True},
            {"key": "expiry_date", "label": "Expiry Date (Non-Transport)", "type": "expiry_date", "required": True},
            {"key": "vehicle_class", "label": "Vehicle Class / COV", "type": "string", "required": False}
        ]
    },

    # =========================================================================
    # 2. TRAVEL / GOVERNMENT DOCUMENTS
    # =========================================================================
    "visa": {
        "id": "visa",
        "name": "Visa",
        "category": CATEGORY_TRAVEL_GOVT,
        "icon": "📄",
        "code": "VISA-ENTRY-AUTH",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.60, 1.95),
        "description": "State travel and consular entry authorization permit.",
        "fields": [
            {"key": "visa_number", "label": "Visa Number", "type": "string", "required": True},
            {"key": "visa_type", "label": "Visa Type / Category", "type": "string", "required": True},
            {"key": "entry_validity", "label": "Entry Validity / Valid Until", "type": "date", "required": True},
            {"key": "stay_duration", "label": "Stay Duration", "type": "duration", "required": True}
        ]
    },

    "permit": {
        "id": "permit",
        "name": "Border Transit Permit",
        "category": CATEGORY_TRAVEL_GOVT,
        "icon": "📑",
        "code": "BORDER-TRANSIT-PASS",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.85),
        "description": "Local border movement pass / transit route authorization permit.",
        "fields": [
            {"key": "permit_number", "label": "Permit ID", "type": "string", "required": True},
            {"key": "permit_type", "label": "Permit Classification", "type": "string", "required": True},
            {"key": "holder_name", "label": "Holder / Org Name", "type": "string", "required": True},
            {"key": "issue_date", "label": "Issue Date", "type": "date", "required": True},
            {"key": "expiry_date", "label": "Expiry Date", "type": "expiry_date", "required": True},
            {"key": "issuing_authority", "label": "Issuing Authority", "type": "string", "required": True}
        ]
    },

    # =========================================================================
    # 3. CIVIL CERTIFICATES
    # =========================================================================
    "birth_certificate": {
        "id": "birth_certificate",
        "name": "Birth Certificate",
        "category": CATEGORY_CIVIL,
        "icon": "👶",
        "code": "CIVIL-REG-BIRTH",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.55),  # A4 portrait or landscape certificate
        "description": "Official civil registration of birth record.",
        "fields": [
            {"key": "name", "label": "Full Name", "type": "string", "required": True},
            {"key": "dob", "label": "Date of Birth", "type": "date", "required": True},
            {"key": "place_of_birth", "label": "Place of Birth", "type": "string", "required": True},
            {"key": "parent_details", "label": "Parent / Guardian Details", "type": "string", "required": True},
            {"key": "registration_number", "label": "Registration Number", "type": "reg_format", "required": True},
            {"key": "registration_date", "label": "Registration Date", "type": "date", "required": True},
            {"key": "issuing_authority", "label": "Issuing Authority / Registrar", "type": "string", "required": True}
        ]
    },

    "death_certificate": {
        "id": "death_certificate",
        "name": "Death Certificate",
        "category": CATEGORY_CIVIL,
        "icon": "🕊️",
        "code": "CIVIL-REG-DEATH",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.55),
        "description": "Official civil registration of death record.",
        "fields": [
            {"key": "name", "label": "Deceased Full Name", "type": "string", "required": True},
            {"key": "date_of_death", "label": "Date of Death", "type": "date", "required": True},
            {"key": "place_of_death", "label": "Place of Death", "type": "string", "required": True},
            {"key": "registration_number", "label": "Registration Number", "type": "reg_format", "required": True},
            {"key": "registration_date", "label": "Registration Date", "type": "date", "required": True},
            {"key": "issuing_authority", "label": "Issuing Authority / Registrar", "type": "string", "required": True}
        ]
    },

    # =========================================================================
    # 4. EDUCATIONAL DOCUMENTS
    # =========================================================================
    "marksheet_10": {
        "id": "marksheet_10",
        "name": "10th Marksheet",
        "category": CATEGORY_EDUCATION,
        "icon": "📚",
        "code": "EDU-SSC-CLASS10",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.60),
        "description": "Secondary School Examination marks statement and academic grade record.",
        "fields": [
            {"key": "student_name", "label": "Student Name", "type": "string", "required": True},
            {"key": "roll_number", "label": "Roll / Register Number", "type": "string", "required": True},
            {"key": "school_name", "label": "School / Board Name", "type": "string", "required": True},
            {"key": "exam_year", "label": "Examination Year", "type": "year", "required": True},
            {"key": "subjects", "label": "Subjects Evaluated", "type": "string", "required": True},
            {"key": "marks", "label": "Marks Breakdown", "type": "string", "required": True},
            {"key": "total_marks", "label": "Total Marks", "type": "number", "required": True},
            {"key": "result", "label": "Final Result", "type": "result_status", "required": True}
        ]
    },

    "marksheet_11": {
        "id": "marksheet_11",
        "name": "11th Marksheet",
        "category": CATEGORY_EDUCATION,
        "icon": "📖",
        "code": "EDU-HSC-CLASS11",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.60),
        "description": "Higher Secondary First Year academic marks statement.",
        "fields": [
            {"key": "student_name", "label": "Student Name", "type": "string", "required": True},
            {"key": "roll_number", "label": "Roll / Register Number", "type": "string", "required": True},
            {"key": "school_name", "label": "School / Junior College", "type": "string", "required": True},
            {"key": "academic_year", "label": "Academic Year", "type": "year", "required": True},
            {"key": "subjects", "label": "Subjects Evaluated", "type": "string", "required": True},
            {"key": "marks", "label": "Marks Breakdown", "type": "string", "required": True},
            {"key": "total_marks", "label": "Total Marks", "type": "number", "required": True},
            {"key": "result", "label": "Final Result", "type": "result_status", "required": True}
        ]
    },

    "marksheet_12": {
        "id": "marksheet_12",
        "name": "12th Marksheet",
        "category": CATEGORY_EDUCATION,
        "icon": "🎓",
        "code": "EDU-HSC-CLASS12",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.60),
        "description": "Senior School Certificate Examination marks and percentage record.",
        "fields": [
            {"key": "student_name", "label": "Student Name", "type": "string", "required": True},
            {"key": "roll_number", "label": "Roll / Register Number", "type": "string", "required": True},
            {"key": "school_name", "label": "School / Senior College", "type": "string", "required": True},
            {"key": "exam_year", "label": "Examination Year", "type": "year", "required": True},
            {"key": "subjects", "label": "Subjects Evaluated", "type": "string", "required": True},
            {"key": "marks", "label": "Marks Breakdown", "type": "string", "required": True},
            {"key": "total_marks", "label": "Total Marks", "type": "number", "required": True},
            {"key": "percentage", "label": "Percentage (%)", "type": "percentage", "required": True},
            {"key": "result", "label": "Final Result", "type": "result_status", "required": True}
        ]
    },

    "marksheet_college": {
        "id": "marksheet_college",
        "name": "College Marksheet",
        "category": CATEGORY_EDUCATION,
        "icon": "🏛️",
        "code": "EDU-UNIV-SEMESTER",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.60),
        "description": "Undergraduate / Postgraduate semester grade report.",
        "fields": [
            {"key": "student_name", "label": "Student Name", "type": "string", "required": True},
            {"key": "register_number", "label": "University Register No", "type": "string", "required": True},
            {"key": "institution", "label": "College / University", "type": "string", "required": True},
            {"key": "course", "label": "Course / Program", "type": "string", "required": True},
            {"key": "semester", "label": "Semester / Trimester", "type": "string", "required": True},
            {"key": "subjects", "label": "Subject Papers", "type": "string", "required": True},
            {"key": "marks", "label": "Marks / CGPA / SGPA", "type": "string", "required": True},
            {"key": "result", "label": "Semester Result", "type": "result_status", "required": True}
        ]
    },

    "degree_certificate": {
        "id": "degree_certificate",
        "name": "Degree Certificate",
        "category": CATEGORY_EDUCATION,
        "icon": "📜",
        "code": "EDU-UNIV-DEGREE",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.55),
        "description": "Official graduation diploma degree scroll issued by university senate.",
        "fields": [
            {"key": "student_name", "label": "Candidate Name", "type": "string", "required": True},
            {"key": "register_number", "label": "University Enrollment No", "type": "string", "required": True},
            {"key": "institution", "label": "Awarding University", "type": "string", "required": True},
            {"key": "degree", "label": "Conferred Degree", "type": "string", "required": True},
            {"key": "course", "label": "Major / Discipline", "type": "string", "required": True},
            {"key": "award_year", "label": "Year of Award", "type": "year", "required": True},
            {"key": "certificate_number", "label": "Certificate Serial No", "type": "string", "required": True},
            {"key": "issuing_authority", "label": "Vice Chancellor / Registrar", "type": "string", "required": True}
        ]
    },

    "provisional_certificate": {
        "id": "provisional_certificate",
        "name": "Provisional Certificate",
        "category": CATEGORY_EDUCATION,
        "icon": "📋",
        "code": "EDU-UNIV-PROVISIONAL",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.55),
        "description": "Interim university degree completion certificate.",
        "fields": [
            {"key": "student_name", "label": "Student Name", "type": "string", "required": True},
            {"key": "register_number", "label": "Registration / Roll No", "type": "string", "required": True},
            {"key": "institution", "label": "College / University", "type": "string", "required": True},
            {"key": "degree_course", "label": "Degree & Discipline", "type": "string", "required": True},
            {"key": "year", "label": "Passing Year", "type": "year", "required": True},
            {"key": "certificate_number", "label": "Certificate Number", "type": "string", "required": True}
        ]
    },

    # =========================================================================
    # 5. PROPERTY DOCUMENTS
    # =========================================================================
    "property_deed": {
        "id": "property_deed",
        "name": "Property / Sale Deed",
        "category": CATEGORY_PROPERTY,
        "icon": "🏘️",
        "code": "PROP-REG-SALEDEED",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.65),
        "description": "Immovable property conveyance sale deed registered with sub-registrar.",
        "fields": [
            {"key": "document_number", "label": "Deed / Doc Number", "type": "string", "required": True},
            {"key": "registration_number", "label": "Registration Volume/No", "type": "string", "required": True},
            {"key": "deed_date", "label": "Execution / Reg Date", "type": "date", "required": True},
            {"key": "buyer_details", "label": "Purchaser / Buyer Name", "type": "string", "required": True},
            {"key": "seller_details", "label": "Vendor / Seller Name", "type": "string", "required": True},
            {"key": "property_reference", "label": "Property / Plot Schedule", "type": "string", "required": True},
            {"key": "registration_office", "label": "Sub-Registrar Office", "type": "string", "required": True},
            {"key": "area_location", "label": "Extent & Location", "type": "string", "required": False}
        ]
    },

    "land_document": {
        "id": "land_document",
        "name": "Land Document",
        "category": CATEGORY_PROPERTY,
        "icon": "🗺️",
        "code": "PROP-REV-LANDRECORD",
        "face_applicable": False,
        "authenticity_applicable": True,
        "structured_extraction_supported": True,
        "aspect_ratio_range": (0.65, 1.65),
        "description": "Agricultural / urban revenue survey record and mutation extract.",
        "fields": [
            {"key": "document_number", "label": "Record / Mutation ID", "type": "string", "required": True},
            {"key": "survey_reference", "label": "Khata / Survey / Khasra No", "type": "string", "required": True},
            {"key": "owner_name", "label": "Land Owner / Pattadar", "type": "string", "required": True},
            {"key": "location_details", "label": "Village / Taluk / District", "type": "string", "required": True},
            {"key": "land_area", "label": "Land Extent (Acres/SqFt)", "type": "string", "required": True},
            {"key": "issue_date", "label": "Date of Issuance", "type": "date", "required": True},
            {"key": "issuing_office", "label": "Tahsildar / Revenue Office", "type": "string", "required": True}
        ]
    }
}


def get_profile(document_type: str) -> Optional[Dict[str, Any]]:
    """Retrieves a document profile by ID (case-insensitive, default to passport)."""
    if not document_type:
        return DOCUMENT_PROFILES.get("passport")
    cleaned = document_type.strip().lower()
    return DOCUMENT_PROFILES.get(cleaned) or DOCUMENT_PROFILES.get("passport")


def get_profiles_by_category() -> Dict[str, List[Dict[str, Any]]]:
    """Returns profiles grouped by functional category."""
    grouped: Dict[str, List[Dict[str, Any]]] = {c: [] for c in CATEGORIES}
    for prof in DOCUMENT_PROFILES.values():
        cat = prof.get("category", CATEGORY_IDENTITY)
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append({
            "id": prof["id"],
            "name": prof["name"],
            "icon": prof["icon"],
            "code": prof["code"],
            "face_applicable": prof["face_applicable"],
            "field_count": len(prof["fields"])
        })
    return grouped


def is_face_applicable(document_type: str) -> bool:
    """Returns True only if the document type naturally includes a facial portrait."""
    prof = get_profile(document_type)
    return prof.get("face_applicable", False) if prof else False


def list_all_profile_ids() -> List[str]:
    """Returns list of all 17 supported document profile IDs."""
    return list(DOCUMENT_PROFILES.keys())

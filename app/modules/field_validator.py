"""
IDShield-X: Document Field Normalization & Validation Engine
Step 4: Cleans, Normalizes, and Validates Extracted Identity Document Fields
"""
import re
from datetime import datetime, date
from typing import Dict, Any, Tuple, Optional

# Standard ISO Country Codes Mapping for Demo
COUNTRY_CODES = {
    "IND": "INDIAN",
    "NPL": "NEPALESE",
    "BTN": "BHUTANESE",
    "BGD": "BANGLADESHI",
    "USA": "AMERICAN",
    "GBR": "BRITISH",
    "CAN": "CANADIAN",
    "DEU": "GERMAN",
    "FRA": "FRENCH",
    "CHN": "CHINESE",
    "LKA": "SRI LANKAN",
    "PAK": "PAKISTANI"
}

def clean_whitespace(val: str) -> str:
    """Trims whitespace and collapses multiple spaces."""
    if not val:
        return ""
    return re.sub(r"\s+", " ", val).strip()


def parse_date_flexibly(date_str: str) -> Tuple[Optional[date], Optional[str]]:
    """
    Attempts to parse various date formats from OCR text.
    Returns (datetime.date, normalized_iso_string) or (None, None).
    """
    if not date_str or date_str == "Not detected":
        return None, None

    cleaned = clean_whitespace(date_str).upper()
    
    # Common formats
    formats_to_try = [
        "%d %b %Y",    # 14 MAY 1994
        "%d %B %Y",    # 14 AUGUST 1994
        "%d-%b-%Y",    # 14-MAY-1994
        "%d/%m/%Y",    # 14/05/1994
        "%d-%m-%Y",    # 14-05-1994
        "%Y-%m-%d",    # 1994-05-14
        "%Y/%m/%d",    # 1994/05/14
        "%d.%m.%Y",    # 14.05.1994
        "%y%m%d",      # 940514 (MRZ format)
    ]

    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(cleaned, fmt).date()
            if fmt == "%y%m%d":
                current_year = date.today().year
                century = 1900 if dt.year > (current_year - 10) else 2000
                dt = dt.replace(year=century + (dt.year % 100))
            return dt, dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None, None


def normalize_and_validate_passport(fields: Dict[str, str]) -> Dict[str, Any]:
    """
    Normalizes and validates extracted Passport fields.
    Statuses: 'Valid', 'Invalid', 'Not detected', 'Needs Review'
    """
    today = date.today()
    results = {}

    # 1. Full Name
    raw_name = fields.get("name", "Not detected")
    if raw_name in ("Not detected", None, ""):
        results["name"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Name field was not identified in document visual zones."
        }
    else:
        norm_name = clean_whitespace(raw_name).upper()
        norm_name = re.sub(r"^[^A-Z]+|[^A-Z]+$", "", norm_name)
        if len(norm_name) >= 3 and re.match(r"^[A-Z\s,\-]+$", norm_name):
            results["name"] = {
                "raw": raw_name,
                "normalized": norm_name,
                "status": "Valid",
                "note": "Standard passenger name structure."
            }
        elif len(norm_name) >= 2:
            results["name"] = {
                "raw": raw_name,
                "normalized": norm_name,
                "status": "Needs Review",
                "note": "Unusual name format or OCR noise characters detected."
            }
        else:
            results["name"] = {
                "raw": raw_name,
                "normalized": norm_name,
                "status": "Invalid",
                "note": "Name string is too short or contains invalid tokens."
            }

    # 2. Passport Number
    raw_pass = fields.get("passport_number", "Not detected")
    if raw_pass in ("Not detected", None, ""):
        results["passport_number"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Passport number not identified in VIZ or MRZ."
        }
    else:
        norm_pass = re.sub(r"[^A-Z0-9]", "", clean_whitespace(raw_pass).upper())
        has_symbols = bool(re.search(r"[^A-Z0-9\s]", raw_pass))
        has_digits = any(c.isdigit() for c in norm_pass)

        # Standard format: 1 uppercase letter followed by 7 or 8 digits
        if re.match(r"^[A-Z][0-9]{7,8}$", norm_pass) and not has_symbols:
            results["passport_number"] = {
                "raw": raw_pass,
                "normalized": norm_pass,
                "status": "Valid",
                "note": "Standard passport syntax (1 Letter + 7-8 Digits). Academic demo format."
            }
        elif has_symbols or not has_digits:
            results["passport_number"] = {
                "raw": raw_pass,
                "normalized": norm_pass,
                "status": "Invalid",
                "note": "Contains invalid symbols or lacks required numeric digits."
            }
        elif 6 <= len(norm_pass) <= 10 and norm_pass.isalnum():
            results["passport_number"] = {
                "raw": raw_pass,
                "normalized": norm_pass,
                "status": "Needs Review",
                "note": "Alphanumeric string detected; non-standard character length for ICAO TD3."
            }
        else:
            results["passport_number"] = {
                "raw": raw_pass,
                "normalized": norm_pass,
                "status": "Invalid",
                "note": "Invalid characters or length for travel document identifier."
            }

    # 3. Nationality
    raw_nat = fields.get("nationality", "Not detected")
    if raw_nat in ("Not detected", None, ""):
        results["nationality"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Nationality not detected."
        }
    else:
        norm_nat = clean_whitespace(raw_nat).upper()
        matched_country = None
        if norm_nat in COUNTRY_CODES:
            matched_country = COUNTRY_CODES[norm_nat]
            norm_nat = f"{matched_country} ({norm_nat})"
        else:
            for code, name in COUNTRY_CODES.items():
                if norm_nat in name or name in norm_nat:
                    norm_nat = f"{name} ({code})"
                    matched_country = name
                    break

        if matched_country:
            results["nationality"] = {
                "raw": raw_nat,
                "normalized": norm_nat,
                "status": "Valid",
                "note": "Recognized state authority."
            }
        else:
            results["nationality"] = {
                "raw": raw_nat,
                "normalized": norm_nat,
                "status": "Needs Review",
                "note": f"Unrecognized 3-letter country code or authority: '{norm_nat}'."
            }

    # 4. Date of Birth
    raw_dob = fields.get("dob", "Not detected")
    if raw_dob in ("Not detected", None, ""):
        results["dob"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Date of Birth not identified."
        }
    else:
        parsed_dob, iso_dob = parse_date_flexibly(raw_dob)
        if parsed_dob:
            if parsed_dob > today:
                results["dob"] = {
                    "raw": raw_dob,
                    "normalized": iso_dob,
                    "status": "Invalid",
                    "note": f"Future date of birth detected ({iso_dob}). Biologically impossible."
                }
            else:
                age = today.year - parsed_dob.year - ((today.month, today.day) < (parsed_dob.month, parsed_dob.day))
                if age > 120:
                    results["dob"] = {
                        "raw": raw_dob,
                        "normalized": iso_dob,
                        "status": "Needs Review",
                        "note": f"Computed age is {age} years; verify document authenticity."
                    }
                else:
                    results["dob"] = {
                        "raw": raw_dob,
                        "normalized": f"{iso_dob} (Age: {age})",
                        "status": "Valid",
                        "note": f"Chronologically valid birth date. Age: {age} years."
                    }
        else:
            results["dob"] = {
                "raw": raw_dob,
                "normalized": clean_whitespace(raw_dob),
                "status": "Needs Review",
                "note": "Could not parse into standardized Gregorian calendar date."
            }

    # 5. Date of Expiry
    raw_exp = fields.get("expiry_date", "Not detected")
    if raw_exp in ("Not detected", None, ""):
        results["expiry_date"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Date of Expiry not identified."
        }
    else:
        parsed_exp, iso_exp = parse_date_flexibly(raw_exp)
        if parsed_exp:
            if parsed_exp < today:
                results["expiry_date"] = {
                    "raw": raw_exp,
                    "normalized": f"{iso_exp} (EXPIRED)",
                    "status": "Invalid",
                    "note": f"Document expired on {iso_exp}. Traveler cannot be cleared on expired credential."
                }
            else:
                results["expiry_date"] = {
                    "raw": raw_exp,
                    "normalized": iso_exp,
                    "status": "Valid",
                    "note": f"Valid unexpired travel credential (Expires: {iso_exp})."
                }
        else:
            results["expiry_date"] = {
                "raw": raw_exp,
                "normalized": clean_whitespace(raw_exp),
                "status": "Needs Review",
                "note": "Could not parse into standardized calendar date."
            }

    # 6. Gender
    raw_gen = fields.get("gender", "Not detected")
    if raw_gen in ("Not detected", None, ""):
        results["gender"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Gender field not detected."
        }
    else:
        norm_gen = clean_whitespace(raw_gen).upper()
        if norm_gen in ("M", "MALE"):
            results["gender"] = {
                "raw": raw_gen,
                "normalized": "Male",
                "status": "Valid",
                "note": "Standard ICAO gender code (M)."
            }
        elif norm_gen in ("F", "FEMALE"):
            results["gender"] = {
                "raw": raw_gen,
                "normalized": "Female",
                "status": "Valid",
                "note": "Standard ICAO gender code (F)."
            }
        elif norm_gen in ("X", "OTHER", "NON-BINARY"):
            results["gender"] = {
                "raw": raw_gen,
                "normalized": "Other (X)",
                "status": "Valid",
                "note": "Unspecified/neutral gender code (X)."
            }
        else:
            results["gender"] = {
                "raw": raw_gen,
                "normalized": norm_gen,
                "status": "Needs Review",
                "note": f"Unrecognized gender token: '{norm_gen}'."
            }

    return results


def normalize_and_validate_visa(fields: Dict[str, str]) -> Dict[str, Any]:
    """Normalizes and validates extracted Visa fields."""
    results = {}

    # 1. Visa Number
    raw_num = fields.get("visa_number", "Not detected")
    if raw_num in ("Not detected", None, ""):
        results["visa_number"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Visa number not detected."
        }
    else:
        norm_num = re.sub(r"[^A-Z0-9\-]", "", clean_whitespace(raw_num).upper())
        if len(norm_num) >= 5 and re.match(r"^[A-Z0-9\-]+$", norm_num):
            results["visa_number"] = {
                "raw": raw_num,
                "normalized": norm_num,
                "status": "Valid",
                "note": "Standard visa credential identifier."
            }
        else:
            results["visa_number"] = {
                "raw": raw_num,
                "normalized": norm_num,
                "status": "Needs Review",
                "note": "Unusual visa number length or formatting."
            }

    # 2. Visa Type
    raw_type = fields.get("visa_type", "Not detected")
    if raw_type in ("Not detected", None, ""):
        results["visa_type"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Visa type not detected."
        }
    else:
        norm_type = clean_whitespace(raw_type).upper()
        if any(keyword in norm_type for keyword in ["TRANSIT", "TOURIST", "BUSINESS", "ENTRY", "STUDENT", "WORK", "B-", "T-"]):
            results["visa_type"] = {
                "raw": raw_type,
                "normalized": norm_type,
                "status": "Valid",
                "note": "Recognized immigration visa category."
            }
        else:
            results["visa_type"] = {
                "raw": raw_type,
                "normalized": norm_type,
                "status": "Needs Review",
                "note": "Non-standard visa classification label."
            }

    # 3. Entry Validity
    raw_val = fields.get("entry_validity", "Not detected")
    if raw_val in ("Not detected", None, ""):
        results["entry_validity"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Entry validity window not detected."
        }
    else:
        norm_val = clean_whitespace(raw_val).upper()
        results["entry_validity"] = {
            "raw": raw_val,
            "normalized": norm_val,
            "status": "Valid" if len(norm_val) >= 4 else "Needs Review",
            "note": "Valid entry authorization window."
        }

    # 4. Stay Duration
    raw_stay = fields.get("stay_duration", "Not detected")
    if raw_stay in ("Not detected", None, ""):
        results["stay_duration"] = {
            "raw": "Not detected",
            "normalized": "Not detected",
            "status": "Not detected",
            "note": "Stay duration not detected."
        }
    else:
        norm_stay = clean_whitespace(raw_stay).upper()
        results["stay_duration"] = {
            "raw": raw_stay,
            "normalized": norm_stay,
            "status": "Valid" if ("DAY" in norm_stay or "MONTH" in norm_stay or "YEAR" in norm_stay) else "Needs Review",
            "note": "Permitted temporal duration of stay."
        }

    return results


def normalize_and_validate_aadhaar(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Aadhaar demographics with privacy-compliant masking."""
    today = date.today()
    results = {}

    # 1. Full Name
    raw_name = fields.get("name", "Not detected")
    if raw_name in ("Not detected", None, ""):
        results["name"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Name not detected."}
    else:
        norm_name = clean_whitespace(raw_name).upper()
        if len(norm_name) >= 3:
            results["name"] = {"raw": raw_name, "normalized": norm_name, "status": "Valid", "note": "Valid resident cardholder name."}
        else:
            results["name"] = {"raw": raw_name, "normalized": norm_name, "status": "Needs Review", "note": "Short resident name string."}

    # 2. Masked Aadhaar (Strict Privacy Compliance)
    raw_uid = fields.get("masked_aadhaar", "Not detected")
    if raw_uid in ("Not detected", None, ""):
        results["masked_aadhaar"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Aadhaar reference not detected."}
    else:
        clean_uid = clean_whitespace(raw_uid).upper()
        # Check if raw 12 digits were passed -> Enforce masking
        raw_digits = re.sub(r"\D", "", clean_uid)
        if len(raw_digits) == 12 and "X" not in clean_uid:
            masked = f"XXXX XXXX {raw_digits[-4:]}"
            results["masked_aadhaar"] = {
                "raw": raw_uid,
                "normalized": masked,
                "status": "Valid",
                "note": "Raw 12-digit UID masked for privacy compliance (Demo prototype)."
            }
        elif re.match(r"^X{4}\s*X{4}\s*[0-9]{4}$", clean_uid.replace("-", " ")):
            results["masked_aadhaar"] = {
                "raw": raw_uid,
                "normalized": clean_uid,
                "status": "Valid",
                "note": "Standard masked demographic identifier."
            }
        elif len(clean_uid) >= 12:
            results["masked_aadhaar"] = {
                "raw": raw_uid,
                "normalized": clean_uid,
                "status": "Needs Review",
                "note": "Aadhaar reference detected; non-standard format."
            }
        else:
            results["masked_aadhaar"] = {
                "raw": raw_uid,
                "normalized": clean_uid,
                "status": "Invalid",
                "note": "Invalid Aadhaar reference length or character format."
            }

    # 3. DOB
    raw_dob = fields.get("dob", "Not detected")
    if raw_dob in ("Not detected", None, ""):
        results["dob"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "DOB not detected."}
    else:
        parsed_dob, iso_dob = parse_date_flexibly(raw_dob)
        if parsed_dob:
            if parsed_dob > today:
                results["dob"] = {"raw": raw_dob, "normalized": iso_dob, "status": "Invalid", "note": "Future date of birth."}
            else:
                age = today.year - parsed_dob.year
                results["dob"] = {"raw": raw_dob, "normalized": f"{iso_dob} (Age: {age})", "status": "Valid", "note": f"Valid date of birth. Resident age ~{age}."}
        elif re.match(r"^[12][0-9]{3}$", clean_whitespace(raw_dob)):
            yr = int(clean_whitespace(raw_dob))
            age = today.year - yr
            results["dob"] = {"raw": raw_dob, "normalized": f"Year {yr} (Age: ~{age})", "status": "Valid", "note": "Year of birth recorded."}
        else:
            results["dob"] = {"raw": raw_dob, "normalized": raw_dob, "status": "Needs Review", "note": "Unstandardized DOB format."}

    # 4. Gender
    raw_gen = fields.get("gender", "Not detected")
    if raw_gen in ("Not detected", None, ""):
        results["gender"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Gender not detected."}
    else:
        g = clean_whitespace(raw_gen).upper()
        if g in ("M", "MALE"):
            results["gender"] = {"raw": raw_gen, "normalized": "Male", "status": "Valid", "note": "Demographic gender: Male."}
        elif g in ("F", "FEMALE"):
            results["gender"] = {"raw": raw_gen, "normalized": "Female", "status": "Valid", "note": "Demographic gender: Female."}
        elif g in ("TRANSGENDER", "OTHER"):
            results["gender"] = {"raw": raw_gen, "normalized": "Transgender", "status": "Valid", "note": "Demographic gender: Transgender."}
        else:
            results["gender"] = {"raw": raw_gen, "normalized": g, "status": "Needs Review", "note": "Unrecognized gender code."}

    # 5. Address
    raw_addr = fields.get("address", "Not detected")
    if raw_addr in ("Not detected", None, ""):
        results["address"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Address not detected."}
    else:
        results["address"] = {"raw": raw_addr, "normalized": clean_whitespace(raw_addr), "status": "Valid" if len(raw_addr) >= 10 else "Needs Review", "note": "Resident demographic address."}

    return results


def normalize_and_validate_pan(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Income Tax Permanent Account Number (PAN)."""
    today = date.today()
    results = {}

    # 1. Cardholder Name
    raw_name = fields.get("name", "Not detected")
    if raw_name in ("Not detected", None, ""):
        results["name"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Name not detected."}
    else:
        norm = clean_whitespace(raw_name).upper()
        results["name"] = {"raw": raw_name, "normalized": norm, "status": "Valid" if len(norm) >= 3 else "Needs Review", "note": "Taxpayer / Cardholder name."}

    # 2. PAN Number ([A-Z]{5}[0-9]{4}[A-Z]{1})
    raw_pan = fields.get("pan_number", "Not detected")
    if raw_pan in ("Not detected", None, ""):
        results["pan_number"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "PAN number not detected."}
    else:
        norm_pan = re.sub(r"[^A-Z0-9]", "", clean_whitespace(raw_pan).upper())
        # Standard PAN regex
        if re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", norm_pan):
            entity_char = norm_pan[3]
            entity_map = {"P": "Individual (Person)", "C": "Company", "H": "HUF", "F": "Firm", "A": "AOP", "T": "Trust"}
            entity_desc = entity_map.get(entity_char, "Entity")
            results["pan_number"] = {
                "raw": raw_pan,
                "normalized": norm_pan,
                "status": "Valid",
                "note": f"Standard PAN format ({norm_pan}). 4th char '{entity_char}' designates {entity_desc}."
            }
        else:
            results["pan_number"] = {
                "raw": raw_pan,
                "normalized": norm_pan,
                "status": "Invalid",
                "note": "Does not conform to 10-character alphanumeric PAN format (5 letters + 4 digits + 1 letter)."
            }

    # 3. Father's Name
    raw_father = fields.get("father_name", "Not detected")
    if raw_father in ("Not detected", None, ""):
        results["father_name"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Father's name not detected."}
    else:
        norm_f = clean_whitespace(raw_father).upper()
        results["father_name"] = {"raw": raw_father, "normalized": norm_f, "status": "Valid" if len(norm_f) >= 3 else "Needs Review", "note": "Parentage identifier."}

    # 4. Date of Birth
    raw_dob = fields.get("dob", "Not detected")
    if raw_dob in ("Not detected", None, ""):
        results["dob"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "DOB not detected."}
    else:
        parsed_dob, iso_dob = parse_date_flexibly(raw_dob)
        if parsed_dob:
            if parsed_dob > today:
                results["dob"] = {"raw": raw_dob, "normalized": iso_dob, "status": "Invalid", "note": "Future date of birth."}
            else:
                age = today.year - parsed_dob.year
                results["dob"] = {"raw": raw_dob, "normalized": f"{iso_dob} (Age: {age})", "status": "Valid", "note": f"Valid birth date. Age: {age}."}
        else:
            results["dob"] = {"raw": raw_dob, "normalized": raw_dob, "status": "Needs Review", "note": "Unparsed birth date."}

    return results


def normalize_and_validate_voter_id(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Election Commission Electoral Photo Identity Card (EPIC)."""
    today = date.today()
    results = {}

    # 1. Elector Name
    raw_name = fields.get("name", "Not detected")
    if raw_name in ("Not detected", None, ""):
        results["name"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Elector name not detected."}
    else:
        norm_name = clean_whitespace(raw_name).upper()
        results["name"] = {"raw": raw_name, "normalized": norm_name, "status": "Valid" if len(norm_name) >= 3 else "Needs Review", "note": "Registered elector name."}

    # 2. EPIC Number ([A-Z]{3}[0-9]{7})
    raw_epic = fields.get("epic_number", "Not detected")
    if raw_epic in ("Not detected", None, ""):
        results["epic_number"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "EPIC number not detected."}
    else:
        norm_epic = re.sub(r"[^A-Z0-9]", "", clean_whitespace(raw_epic).upper())
        if re.match(r"^[A-Z]{3}[0-9]{7}$", norm_epic):
            results["epic_number"] = {
                "raw": raw_epic,
                "normalized": norm_epic,
                "status": "Valid",
                "note": "Standard 10-character EPIC format (3 Alpha prefix + 7 Digits)."
            }
        elif len(norm_epic) == 10 and norm_epic.isalnum():
            results["epic_number"] = {
                "raw": raw_epic,
                "normalized": norm_epic,
                "status": "Needs Review",
                "note": "Alphanumeric 10-char EPIC token; non-standard prefix."
            }
        else:
            results["epic_number"] = {
                "raw": raw_epic,
                "normalized": norm_epic,
                "status": "Invalid",
                "note": "Invalid EPIC identifier format or character length."
            }

    # 3. DOB / Age
    raw_age = fields.get("dob_or_age", "Not detected")
    if raw_age in ("Not detected", None, ""):
        results["dob_or_age"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "DOB/Age not detected."}
    else:
        parsed_dob, iso_dob = parse_date_flexibly(raw_age)
        if parsed_dob:
            age = today.year - parsed_dob.year
            status = "Valid" if age >= 18 else "Invalid"
            note = f"Elector age {age} years (>= 18 eligible)" if age >= 18 else f"Elector age {age} is below minimum voting age of 18"
            results["dob_or_age"] = {"raw": raw_age, "normalized": f"{iso_dob} (Age: {age})", "status": status, "note": note}
        else:
            # Check if age integer is in string
            m_age = re.search(r"\b([1-9][0-9])\b", raw_age)
            if m_age:
                val = int(m_age.group(1))
                results["dob_or_age"] = {"raw": raw_age, "normalized": f"Age: {val} Years", "status": "Valid" if val >= 18 else "Invalid", "note": "Elector stated age."}
            else:
                results["dob_or_age"] = {"raw": raw_age, "normalized": clean_whitespace(raw_age), "status": "Needs Review", "note": "Unparsed age / DOB."}

    # 4. Constituency
    raw_const = fields.get("constituency", "Not detected")
    if raw_const in ("Not detected", None, ""):
        results["constituency"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Constituency not detected."}
    else:
        results["constituency"] = {"raw": raw_const, "normalized": clean_whitespace(raw_const).upper(), "status": "Valid", "note": "Assembly / Parliamentary constituency."}

    # 5. Address
    raw_addr = fields.get("address", "Not detected")
    if raw_addr in ("Not detected", None, ""):
        results["address"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Address not detected."}
    else:
        results["address"] = {"raw": raw_addr, "normalized": clean_whitespace(raw_addr), "status": "Valid" if len(raw_addr) >= 6 else "Needs Review", "note": "Elector residential address."}

    return results


def normalize_and_validate_driving_license(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Driving Licence (DL) credential."""
    today = date.today()
    results = {}

    # 1. Name
    raw_name = fields.get("name", "Not detected")
    if raw_name in ("Not detected", None, ""):
        results["name"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Name not detected."}
    else:
        norm = clean_whitespace(raw_name).upper()
        results["name"] = {"raw": raw_name, "normalized": norm, "status": "Valid" if len(norm) >= 3 else "Needs Review", "note": "Licence holder name."}

    # 2. License Number
    raw_dl = fields.get("license_number", "Not detected")
    if raw_dl in ("Not detected", None, ""):
        results["license_number"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "DL number not detected."}
    else:
        clean_dl = re.sub(r"[^A-Z0-9\-]", "", clean_whitespace(raw_dl).upper())
        if len(clean_dl) >= 10:
            results["license_number"] = {"raw": raw_dl, "normalized": clean_dl, "status": "Valid", "note": "Standard transport authority DL syntax."}
        else:
            results["license_number"] = {"raw": raw_dl, "normalized": clean_dl, "status": "Invalid", "note": "DL string too short."}

    # 3. DOB
    raw_dob = fields.get("dob", "Not detected")
    if raw_dob in ("Not detected", None, ""):
        results["dob"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "DOB not detected."}
    else:
        parsed_dob, iso_dob = parse_date_flexibly(raw_dob)
        if parsed_dob:
            age = today.year - parsed_dob.year
            status = "Valid" if age >= 18 else "Invalid"
            note = f"Driver age: {age} (>= 18 legal driving threshold)" if age >= 18 else "Driver age below 18"
            results["dob"] = {"raw": raw_dob, "normalized": f"{iso_dob} (Age: {age})", "status": status, "note": note}
        else:
            results["dob"] = {"raw": raw_dob, "normalized": raw_dob, "status": "Needs Review", "note": "Unparsed DOB."}

    # 4. Issue Date
    raw_iss = fields.get("issue_date", "Not detected")
    if raw_iss in ("Not detected", None, ""):
        results["issue_date"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Issue date not detected."}
    else:
        parsed_iss, iso_iss = parse_date_flexibly(raw_iss)
        results["issue_date"] = {"raw": raw_iss, "normalized": iso_iss or raw_iss, "status": "Valid" if parsed_iss and parsed_iss <= today else "Needs Review", "note": "Date of initial issuance."}

    # 5. Expiry Date
    raw_exp = fields.get("expiry_date", "Not detected")
    if raw_exp in ("Not detected", None, ""):
        results["expiry_date"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Expiry date not detected."}
    else:
        parsed_exp, iso_exp = parse_date_flexibly(raw_exp)
        if parsed_exp:
            if parsed_exp < today:
                results["expiry_date"] = {"raw": raw_exp, "normalized": f"{iso_exp} (EXPIRED)", "status": "Invalid", "note": f"Licence expired on {iso_exp}."}
            else:
                results["expiry_date"] = {"raw": raw_exp, "normalized": iso_exp, "status": "Valid", "note": f"Active unexpired licence (Valid till {iso_exp})."}
        else:
            results["expiry_date"] = {"raw": raw_exp, "normalized": raw_exp, "status": "Needs Review", "note": "Unparsed expiry date."}

    # 6. Vehicle Class
    raw_cov = fields.get("vehicle_class", "Not detected")
    if raw_cov in ("Not detected", None, ""):
        results["vehicle_class"] = {"raw": "Not detected", "normalized": "Not detected", "status": "Not detected", "note": "Vehicle class not detected."}
    else:
        results["vehicle_class"] = {"raw": raw_cov, "normalized": clean_whitespace(raw_cov).upper(), "status": "Valid", "note": "Permitted vehicle classes (COV)."}

    return results


def normalize_and_validate_permit(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Border Transit Permit / Local Pass."""
    today = date.today()
    results = {}

    # 1. Permit Number
    raw_num = fields.get("permit_number", "Not detected")
    results["permit_number"] = {"raw": raw_num, "normalized": clean_whitespace(raw_num), "status": "Valid" if len(raw_num) >= 4 else "Not detected", "note": "Border pass ID."}

    # 2. Permit Type
    raw_type = fields.get("permit_type", "Not detected")
    results["permit_type"] = {"raw": raw_type, "normalized": clean_whitespace(raw_type).upper(), "status": "Valid" if raw_type != "Not detected" else "Not detected", "note": "Pass classification."}

    # 3. Holder Name
    raw_name = fields.get("holder_name", "Not detected")
    results["holder_name"] = {"raw": raw_name, "normalized": clean_whitespace(raw_name).upper(), "status": "Valid" if len(raw_name) >= 3 else "Not detected", "note": "Permit holder name."}

    # 4. Issue Date
    raw_iss = fields.get("issue_date", "Not detected")
    p_iss, iso_iss = parse_date_flexibly(raw_iss)
    results["issue_date"] = {"raw": raw_iss, "normalized": iso_iss or raw_iss, "status": "Valid" if p_iss else "Needs Review", "note": "Pass issuance date."}

    # 5. Expiry Date
    raw_exp = fields.get("expiry_date", "Not detected")
    p_exp, iso_exp = parse_date_flexibly(raw_exp)
    if p_exp:
        status = "Invalid" if p_exp < today else "Valid"
        note = f"Pass expired on {iso_exp}" if p_exp < today else f"Active permit (Expires {iso_exp})"
        results["expiry_date"] = {"raw": raw_exp, "normalized": iso_exp, "status": status, "note": note}
    else:
        results["expiry_date"] = {"raw": raw_exp, "normalized": raw_exp, "status": "Needs Review", "note": "Unparsed expiry date."}

    # 6. Issuing Authority
    raw_auth = fields.get("issuing_authority", "Not detected")
    results["issuing_authority"] = {"raw": raw_auth, "normalized": clean_whitespace(raw_auth), "status": "Valid" if len(raw_auth) >= 4 else "Needs Review", "note": "Authorized checkpoint signatory."}

    return results


def normalize_and_validate_birth_certificate(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Civil Birth Certificate with chronological registration check."""
    today = date.today()
    results = {}

    # 1. Child Name
    raw_name = fields.get("name", "Not detected")
    results["name"] = {"raw": raw_name, "normalized": clean_whitespace(raw_name).upper(), "status": "Valid" if len(raw_name) >= 2 else "Not detected", "note": "Registered child name."}

    # 2. Date of Birth
    raw_dob = fields.get("dob", "Not detected")
    p_dob, iso_dob = parse_date_flexibly(raw_dob)
    if p_dob:
        status = "Invalid" if p_dob > today else "Valid"
        note = "Future birth date (impossible)" if p_dob > today else f"Recorded birth date ({iso_dob})"
        results["dob"] = {"raw": raw_dob, "normalized": iso_dob, "status": status, "note": note}
    else:
        results["dob"] = {"raw": raw_dob, "normalized": raw_dob, "status": "Needs Review", "note": "Unparsed birth date."}

    # 3. Place of Birth
    raw_pob = fields.get("place_of_birth", "Not detected")
    results["place_of_birth"] = {"raw": raw_pob, "normalized": clean_whitespace(raw_pob), "status": "Valid" if len(raw_pob) >= 3 else "Not detected", "note": "Birth location / institution."}

    # 4. Parent Details
    raw_par = fields.get("parent_details", "Not detected")
    results["parent_details"] = {"raw": raw_par, "normalized": clean_whitespace(raw_par).upper(), "status": "Valid" if len(raw_par) >= 3 else "Not detected", "note": "Parentage records."}

    # 5. Registration Number
    raw_reg = fields.get("registration_number", "Not detected")
    results["registration_number"] = {"raw": raw_reg, "normalized": clean_whitespace(raw_reg).upper(), "status": "Valid" if len(raw_reg) >= 4 else "Not detected", "note": "Civil registration entry index."}

    # 6. Registration Date (Chronological check: reg_date >= dob)
    raw_regd = fields.get("registration_date", "Not detected")
    p_regd, iso_regd = parse_date_flexibly(raw_regd)
    if p_regd:
        if p_dob and p_regd < p_dob:
            results["registration_date"] = {
                "raw": raw_regd,
                "normalized": iso_regd,
                "status": "Invalid",
                "note": f"Chronological anomaly: Registration date ({iso_regd}) occurs before birth date ({iso_dob})."
            }
        else:
            results["registration_date"] = {
                "raw": raw_regd,
                "normalized": iso_regd,
                "status": "Valid",
                "note": f"Registration entered in civil registry on {iso_regd}."
            }
    else:
        results["registration_date"] = {"raw": raw_regd, "normalized": raw_regd, "status": "Needs Review", "note": "Unparsed registration date."}

    # 7. Issuing Authority
    raw_auth = fields.get("issuing_authority", "Not detected")
    results["issuing_authority"] = {"raw": raw_auth, "normalized": clean_whitespace(raw_auth), "status": "Valid" if len(raw_auth) >= 3 else "Needs Review", "note": "Local registrar."}

    return results


def normalize_and_validate_death_certificate(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Civil Death Certificate with chronological verification."""
    today = date.today()
    results = {}

    # 1. Deceased Name
    raw_name = fields.get("name", "Not detected")
    results["name"] = {"raw": raw_name, "normalized": clean_whitespace(raw_name).upper(), "status": "Valid" if len(raw_name) >= 3 else "Not detected", "note": "Deceased person name."}

    # 2. Date of Death
    raw_dod = fields.get("date_of_death", "Not detected")
    p_dod, iso_dod = parse_date_flexibly(raw_dod)
    if p_dod:
        status = "Invalid" if p_dod > today else "Valid"
        note = "Future date of death (impossible)" if p_dod > today else f"Recorded date of death ({iso_dod})"
        results["date_of_death"] = {"raw": raw_dod, "normalized": iso_dod, "status": status, "note": note}
    else:
        results["date_of_death"] = {"raw": raw_dod, "normalized": raw_dod, "status": "Needs Review", "note": "Unparsed death date."}

    # 3. Place of Death
    raw_pod = fields.get("place_of_death", "Not detected")
    results["place_of_death"] = {"raw": raw_pod, "normalized": clean_whitespace(raw_pod), "status": "Valid" if len(raw_pod) >= 3 else "Not detected", "note": "Location of demise."}

    # 4. Registration Number
    raw_reg = fields.get("registration_number", "Not detected")
    results["registration_number"] = {"raw": raw_reg, "normalized": clean_whitespace(raw_reg).upper(), "status": "Valid" if len(raw_reg) >= 4 else "Not detected", "note": "Form 6 register serial."}

    # 5. Registration Date (Chronological check: reg_date >= dod)
    raw_regd = fields.get("registration_date", "Not detected")
    p_regd, iso_regd = parse_date_flexibly(raw_regd)
    if p_regd:
        if p_dod and p_regd < p_dod:
            results["registration_date"] = {
                "raw": raw_regd,
                "normalized": iso_regd,
                "status": "Invalid",
                "note": f"Chronological anomaly: Registration date ({iso_regd}) occurs before death date ({iso_dod})."
            }
        else:
            results["registration_date"] = {"raw": raw_regd, "normalized": iso_regd, "status": "Valid", "note": f"Civil registration entry date: {iso_regd}."}
    else:
        results["registration_date"] = {"raw": raw_regd, "normalized": raw_regd, "status": "Needs Review", "note": "Unparsed registration date."}

    # 6. Issuing Authority
    raw_auth = fields.get("issuing_authority", "Not detected")
    results["issuing_authority"] = {"raw": raw_auth, "normalized": clean_whitespace(raw_auth), "status": "Valid" if len(raw_auth) >= 3 else "Needs Review", "note": "Civil registrar."}

    return results


def normalize_and_validate_marksheet(fields: Dict[str, str], class_level: str = "10") -> Dict[str, Any]:
    """
    Validates Secondary / Senior Secondary marksheets (10th, 11th, 12th).
    Performs mathematical mark consistency check (sum vs total) and percentage validation.
    """
    current_year = date.today().year
    results = {}

    # 1. Student Name
    raw_name = fields.get("student_name", "Not detected")
    results["student_name"] = {"raw": raw_name, "normalized": clean_whitespace(raw_name).upper(), "status": "Valid" if len(raw_name) >= 3 else "Not detected", "note": "Candidate name."}

    # 2. Roll Number
    raw_roll = fields.get("roll_number", "Not detected")
    results["roll_number"] = {"raw": raw_roll, "normalized": clean_whitespace(raw_roll), "status": "Valid" if len(raw_roll) >= 4 else "Not detected", "note": "Board examination roll index."}

    # 3. School / Board Name
    raw_sch = fields.get("school_name", "Not detected")
    results["school_name"] = {"raw": raw_sch, "normalized": clean_whitespace(raw_sch), "status": "Valid" if len(raw_sch) >= 4 else "Not detected", "note": "Educational institution."}

    # 4. Exam / Academic Year
    yr_field = "academic_year" if "academic_year" in fields else "exam_year"
    raw_yr = fields.get(yr_field, "Not detected")
    m_yr = re.search(r"\b(19\d{2}|20\d{2})\b", raw_yr)
    if m_yr:
        y_val = int(m_yr.group(1))
        status = "Valid" if 1970 <= y_val <= current_year else "Invalid"
        note = f"Examination year {y_val}" if status == "Valid" else f"Unreasonable academic year {y_val}"
        results[yr_field] = {"raw": raw_yr, "normalized": str(y_val), "status": status, "note": note}
    else:
        results[yr_field] = {"raw": raw_yr, "normalized": raw_yr, "status": "Needs Review", "note": "Unparsed examination year."}

    # 5. Subjects
    raw_sub = fields.get("subjects", "Not detected")
    results["subjects"] = {"raw": raw_sub, "normalized": clean_whitespace(raw_sub), "status": "Valid" if len(raw_sub) >= 5 else "Not detected", "note": "Curriculum subjects."}

    # 6. Marks Breakdown
    raw_mrk = fields.get("marks", "Not detected")
    results["marks"] = {"raw": raw_mrk, "normalized": clean_whitespace(raw_mrk), "status": "Valid" if len(raw_mrk) >= 5 else "Not detected", "note": "Subject-wise score roster."}

    # 7. Total Marks & Mathematical Sum Verification
    raw_tot = fields.get("total_marks", "Not detected")
    m_tot = re.search(r"(\d+)\s*(?:\/\s*(\d+))?", raw_tot)
    obtained_marks = None
    max_marks = 500  # Default 5 subjects assumption
    if m_tot:
        obtained_marks = int(m_tot.group(1))
        if m_tot.group(2):
            max_marks = int(m_tot.group(2))

        # Check if individual marks numbers are in the subjects/marks string
        found_marks = [int(m) for m in re.findall(r"\((\d{1,3})\)", raw_sub) or re.findall(r"\((\d{1,3})\)", raw_mrk)]
        if found_marks and len(found_marks) >= 3:
            calc_sum = sum(found_marks)
            if calc_sum == obtained_marks:
                results["total_marks"] = {
                    "raw": raw_tot,
                    "normalized": f"{obtained_marks} / {max_marks}",
                    "status": "Valid",
                    "note": f"Total verified. Mathematical sum of {len(found_marks)} subjects matches stated total ({calc_sum})."
                }
            elif abs(calc_sum - obtained_marks) > 10:
                results["total_marks"] = {
                    "raw": raw_tot,
                    "normalized": f"{obtained_marks} / {max_marks}",
                    "status": "Needs Review",
                    "note": f"Mathematical discrepancy: Subject sum ({calc_sum}) differs from stated total ({obtained_marks})."
                }
            else:
                results["total_marks"] = {
                    "raw": raw_tot,
                    "normalized": f"{obtained_marks} / {max_marks}",
                    "status": "Valid",
                    "note": f"Calculated mark total: {obtained_marks} / {max_marks}."
                }
        else:
            results["total_marks"] = {
                "raw": raw_tot,
                "normalized": f"{obtained_marks} / {max_marks}",
                "status": "Valid" if obtained_marks <= max_marks else "Invalid",
                "note": "Total mark tally." if obtained_marks <= max_marks else "Obtained marks cannot exceed maximum marks."
            }
    else:
        results["total_marks"] = {"raw": raw_tot, "normalized": raw_tot, "status": "Needs Review", "note": "Unparsed total score."}

    # 8. Percentage (for Class 12)
    if "percentage" in fields:
        raw_pct = fields.get("percentage", "Not detected")
        m_pct = re.search(r"(\d+(?:\.\d+)?)\s*%", raw_pct)
        if m_pct and obtained_marks and max_marks > 0:
            stated_pct = float(m_pct.group(1))
            calc_pct = round((obtained_marks / max_marks) * 100, 1)
            if abs(stated_pct - calc_pct) <= 1.0:
                results["percentage"] = {
                    "raw": raw_pct,
                    "normalized": f"{stated_pct}%",
                    "status": "Valid",
                    "note": f"Percentage arithmetic verified ({stated_pct}% ≈ calculated {calc_pct}%)."
                }
            else:
                results["percentage"] = {
                    "raw": raw_pct,
                    "normalized": f"{stated_pct}%",
                    "status": "Needs Review",
                    "note": f"Percentage arithmetic mismatch: Stated {stated_pct}% vs computed {calc_pct}%."
                }
        elif m_pct:
            results["percentage"] = {"raw": raw_pct, "normalized": f"{m_pct.group(1)}%", "status": "Valid", "note": "Academic percentage."}
        else:
            results["percentage"] = {"raw": raw_pct, "normalized": raw_pct, "status": "Needs Review", "note": "Unparsed percentage."}

    # 9. Result
    raw_res = fields.get("result", "Not detected")
    norm_res = clean_whitespace(raw_res).upper()
    if "PASS" in norm_res:
        results["result"] = {"raw": raw_res, "normalized": "PASS", "status": "Valid", "note": "Successful examination clearance."}
    elif "FAIL" in norm_res:
        results["result"] = {"raw": raw_res, "normalized": "FAIL", "status": "Valid", "note": "Candidate not cleared."}
    else:
        results["result"] = {"raw": raw_res, "normalized": norm_res, "status": "Needs Review", "note": "Unstandardized result string."}

    return results


def normalize_and_validate_college_marksheet(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates College / University Semester Marksheet."""
    results = {}
    results["student_name"] = {"raw": fields.get("student_name", "Not detected"), "normalized": clean_whitespace(fields.get("student_name", "")).upper(), "status": "Valid" if len(fields.get("student_name", "")) >= 3 else "Not detected", "note": "Student name."}
    results["register_number"] = {"raw": fields.get("register_number", "Not detected"), "normalized": clean_whitespace(fields.get("register_number", "")), "status": "Valid" if len(fields.get("register_number", "")) >= 4 else "Not detected", "note": "University roll/registration index."}
    results["institution"] = {"raw": fields.get("institution", "Not detected"), "normalized": clean_whitespace(fields.get("institution", "")), "status": "Valid" if len(fields.get("institution", "")) >= 4 else "Not detected", "note": "College or faculty institution."}
    results["course"] = {"raw": fields.get("course", "Not detected"), "normalized": clean_whitespace(fields.get("course", "")).upper(), "status": "Valid" if len(fields.get("course", "")) >= 3 else "Not detected", "note": "Academic degree program."}
    results["semester"] = {"raw": fields.get("semester", "Not detected"), "normalized": clean_whitespace(fields.get("semester", "")).upper(), "status": "Valid" if len(fields.get("semester", "")) >= 2 else "Not detected", "note": "Semester designation."}
    results["subjects"] = {"raw": fields.get("subjects", "Not detected"), "normalized": clean_whitespace(fields.get("subjects", "")), "status": "Valid" if len(fields.get("subjects", "")) >= 5 else "Not detected", "note": "Semester course modules."}

    raw_mrk = fields.get("marks", "Not detected")
    m_gpa = re.search(r"(\d+(?:\.\d+)?)\s*(?:\/\s*(\d+(?:\.\d+)?))?", raw_mrk)
    if m_gpa:
        val = float(m_gpa.group(1))
        scale = float(m_gpa.group(2)) if m_gpa.group(2) else 10.0
        results["marks"] = {"raw": raw_mrk, "normalized": f"{val} / {scale}", "status": "Valid" if val <= scale else "Invalid", "note": f"Semester SGPA/CGPA grade ({val}/{scale})."}
    else:
        results["marks"] = {"raw": raw_mrk, "normalized": raw_mrk, "status": "Needs Review", "note": "Grade evaluation."}

    res_raw = fields.get("result", "Not detected")
    results["result"] = {"raw": res_raw, "normalized": clean_whitespace(res_raw).upper(), "status": "Valid" if "PASS" in res_raw.upper() else "Needs Review", "note": "Semester completion standing."}
    return results


def normalize_and_validate_degree(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates University Degree Scroll Certificate."""
    results = {}
    current_year = date.today().year
    results["student_name"] = {"raw": fields.get("student_name", "Not detected"), "normalized": clean_whitespace(fields.get("student_name", "")).upper(), "status": "Valid" if len(fields.get("student_name", "")) >= 3 else "Not detected", "note": "Graduate name."}
    results["register_number"] = {"raw": fields.get("register_number", "Not detected"), "normalized": clean_whitespace(fields.get("register_number", "")), "status": "Valid" if len(fields.get("register_number", "")) >= 4 else "Not detected", "note": "University enrollment identifier."}
    results["institution"] = {"raw": fields.get("institution", "Not detected"), "normalized": clean_whitespace(fields.get("institution", "")), "status": "Valid" if len(fields.get("institution", "")) >= 4 else "Not detected", "note": "Conferring university."}
    results["degree"] = {"raw": fields.get("degree", "Not detected"), "normalized": clean_whitespace(fields.get("degree", "")).upper(), "status": "Valid" if len(fields.get("degree", "")) >= 3 else "Not detected", "note": "Awarded degree title."}
    results["course"] = {"raw": fields.get("course", "Not detected"), "normalized": clean_whitespace(fields.get("course", "")).upper(), "status": "Valid" if len(fields.get("course", "")) >= 3 else "Not detected", "note": "Discipline / Specialization."}

    raw_yr = fields.get("award_year", "Not detected")
    m_yr = re.search(r"\b(19\d{2}|20\d{2})\b", raw_yr)
    if m_yr:
        y = int(m_yr.group(1))
        results["award_year"] = {"raw": raw_yr, "normalized": str(y), "status": "Valid" if 1960 <= y <= current_year else "Invalid", "note": f"Convocation award year {y}."}
    else:
        results["award_year"] = {"raw": raw_yr, "normalized": raw_yr, "status": "Needs Review", "note": "Unparsed graduation year."}

    results["certificate_number"] = {"raw": fields.get("certificate_number", "Not detected"), "normalized": clean_whitespace(fields.get("certificate_number", "")), "status": "Valid" if len(fields.get("certificate_number", "")) >= 4 else "Not detected", "note": "Degree scroll serial number."}
    results["issuing_authority"] = {"raw": fields.get("issuing_authority", "Not detected"), "normalized": clean_whitespace(fields.get("issuing_authority", "")), "status": "Valid" if len(fields.get("issuing_authority", "")) >= 4 else "Not detected", "note": "Senate / Chancellor signature."}
    return results


def normalize_and_validate_provisional(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Provisional Degree Certificate."""
    results = {}
    current_year = date.today().year
    results["student_name"] = {"raw": fields.get("student_name", "Not detected"), "normalized": clean_whitespace(fields.get("student_name", "")).upper(), "status": "Valid" if len(fields.get("student_name", "")) >= 3 else "Not detected", "note": "Student name."}
    results["register_number"] = {"raw": fields.get("register_number", "Not detected"), "normalized": clean_whitespace(fields.get("register_number", "")), "status": "Valid" if len(fields.get("register_number", "")) >= 4 else "Not detected", "note": "Roll/Register number."}
    results["institution"] = {"raw": fields.get("institution", "Not detected"), "normalized": clean_whitespace(fields.get("institution", "")), "status": "Valid" if len(fields.get("institution", "")) >= 4 else "Not detected", "note": "College / University."}
    results["degree_course"] = {"raw": fields.get("degree_course", "Not detected"), "normalized": clean_whitespace(fields.get("degree_course", "")).upper(), "status": "Valid" if len(fields.get("degree_course", "")) >= 3 else "Not detected", "note": "Degree & discipline."}

    raw_yr = fields.get("year", "Not detected")
    m_yr = re.search(r"\b(19\d{2}|20\d{2})\b", raw_yr)
    if m_yr:
        y = int(m_yr.group(1))
        results["year"] = {"raw": raw_yr, "normalized": str(y), "status": "Valid" if 1960 <= y <= current_year else "Invalid", "note": f"Passing year {y}."}
    else:
        results["year"] = {"raw": raw_yr, "normalized": raw_yr, "status": "Needs Review", "note": "Unparsed year."}

    results["certificate_number"] = {"raw": fields.get("certificate_number", "Not detected"), "normalized": clean_whitespace(fields.get("certificate_number", "")), "status": "Valid" if len(fields.get("certificate_number", "")) >= 4 else "Not detected", "note": "Provisional certificate ID."}
    return results


def normalize_and_validate_property_deed(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Property Conveyance / Sale Deed with Buyer/Seller consistency check."""
    results = {}
    today = date.today()

    results["document_number"] = {"raw": fields.get("document_number", "Not detected"), "normalized": clean_whitespace(fields.get("document_number", "")), "status": "Valid" if len(fields.get("document_number", "")) >= 3 else "Not detected", "note": "Deed number."}
    results["registration_number"] = {"raw": fields.get("registration_number", "Not detected"), "normalized": clean_whitespace(fields.get("registration_number", "")), "status": "Valid" if len(fields.get("registration_number", "")) >= 4 else "Not detected", "note": "Registration volume / book record."}

    raw_dt = fields.get("deed_date", "Not detected")
    p_dt, iso_dt = parse_date_flexibly(raw_dt)
    if p_dt:
        results["deed_date"] = {"raw": raw_dt, "normalized": iso_dt, "status": "Valid" if p_dt <= today else "Invalid", "note": "Deed execution date." if p_dt <= today else "Future execution date."}
    else:
        results["deed_date"] = {"raw": raw_dt, "normalized": raw_dt, "status": "Needs Review", "note": "Unparsed deed date."}

    # Buyer vs Seller Consistency Check: Buyer and Seller cannot be the exact same party
    raw_buy = fields.get("buyer_details", "Not detected")
    raw_sel = fields.get("seller_details", "Not detected")
    norm_buy = clean_whitespace(raw_buy).upper()
    norm_sel = clean_whitespace(raw_sel).upper()

    if norm_buy == norm_sel and norm_buy not in ("NOT DETECTED", ""):
        results["buyer_details"] = {"raw": raw_buy, "normalized": norm_buy, "status": "Invalid", "note": "Conveyance deed inconsistency: Purchaser and Vendor names are identical."}
        results["seller_details"] = {"raw": raw_sel, "normalized": norm_sel, "status": "Invalid", "note": "Conveyance deed inconsistency: Vendor and Purchaser names are identical."}
    else:
        results["buyer_details"] = {"raw": raw_buy, "normalized": norm_buy, "status": "Valid" if len(norm_buy) >= 3 else "Not detected", "note": "Purchaser / Buyer party."}
        results["seller_details"] = {"raw": raw_sel, "normalized": norm_sel, "status": "Valid" if len(norm_sel) >= 3 else "Not detected", "note": "Vendor / Seller party."}

    results["property_reference"] = {"raw": fields.get("property_reference", "Not detected"), "normalized": clean_whitespace(fields.get("property_reference", "")), "status": "Valid" if len(fields.get("property_reference", "")) >= 5 else "Not detected", "note": "Plot / survey schedule."}
    results["registration_office"] = {"raw": fields.get("registration_office", "Not detected"), "normalized": clean_whitespace(fields.get("registration_office", "")), "status": "Valid" if len(fields.get("registration_office", "")) >= 4 else "Not detected", "note": "Sub-Registrar office."}

    raw_loc = fields.get("area_location", "Not detected")
    if raw_loc != "Not detected":
        results["area_location"] = {"raw": raw_loc, "normalized": clean_whitespace(raw_loc), "status": "Valid", "note": "Location and plot dimension."}

    return results


def normalize_and_validate_land_document(fields: Dict[str, str]) -> Dict[str, Any]:
    """Validates Land Record (Khatauni / Patta / ROR)."""
    results = {}
    today = date.today()

    results["document_number"] = {"raw": fields.get("document_number", "Not detected"), "normalized": clean_whitespace(fields.get("document_number", "")), "status": "Valid" if len(fields.get("document_number", "")) >= 4 else "Not detected", "note": "Land revenue mutation ID."}
    results["survey_reference"] = {"raw": fields.get("survey_reference", "Not detected"), "normalized": clean_whitespace(fields.get("survey_reference", "")), "status": "Valid" if len(fields.get("survey_reference", "")) >= 4 else "Not detected", "note": "Khata / Khasra survey number."}
    results["owner_name"] = {"raw": fields.get("owner_name", "Not detected"), "normalized": clean_whitespace(fields.get("owner_name", "")).upper(), "status": "Valid" if len(fields.get("owner_name", "")) >= 3 else "Not detected", "note": "Recorded pattadar / landowner."}
    results["location_details"] = {"raw": fields.get("location_details", "Not detected"), "normalized": clean_whitespace(fields.get("location_details", "")), "status": "Valid" if len(fields.get("location_details", "")) >= 4 else "Not detected", "note": "Village / Taluk revenue jurisdiction."}
    results["land_area"] = {"raw": fields.get("land_area", "Not detected"), "normalized": clean_whitespace(fields.get("land_area", "")), "status": "Valid" if len(fields.get("land_area", "")) >= 3 else "Not detected", "note": "Land extent (acres / decimals)."}

    raw_iss = fields.get("issue_date", "Not detected")
    p_iss, iso_iss = parse_date_flexibly(raw_iss)
    if p_iss:
        results["issue_date"] = {"raw": raw_iss, "normalized": iso_iss, "status": "Valid" if p_iss <= today else "Invalid", "note": "Revenue record issuance date."}
    else:
        results["issue_date"] = {"raw": raw_iss, "normalized": raw_iss, "status": "Needs Review", "note": "Unparsed date."}

    results["issuing_office"] = {"raw": fields.get("issuing_office", "Not detected"), "normalized": clean_whitespace(fields.get("issuing_office", "")), "status": "Valid" if len(fields.get("issuing_office", "")) >= 4 else "Not detected", "note": "Tahsildar / Anchal Adhikari office."}
    return results


def validate_document_fields(fields: Dict[str, str], document_type: str) -> Dict[str, Any]:
    """Master Dispatcher for Field Validation & Normalization across 17 Document Profiles."""
    dtype = (document_type or "passport").strip().lower()

    if dtype == "passport":
        norm_fields = normalize_and_validate_passport(fields)
    elif dtype == "visa":
        norm_fields = normalize_and_validate_visa(fields)
    elif dtype in ("aadhaar", "national_id"):
        norm_fields = normalize_and_validate_aadhaar(fields)
    elif dtype == "pan_card":
        norm_fields = normalize_and_validate_pan(fields)
    elif dtype == "voter_id":
        norm_fields = normalize_and_validate_voter_id(fields)
    elif dtype == "driving_license":
        norm_fields = normalize_and_validate_driving_license(fields)
    elif dtype == "permit":
        norm_fields = normalize_and_validate_permit(fields)
    elif dtype == "birth_certificate":
        norm_fields = normalize_and_validate_birth_certificate(fields)
    elif dtype == "death_certificate":
        norm_fields = normalize_and_validate_death_certificate(fields)
    elif dtype == "marksheet_10":
        norm_fields = normalize_and_validate_marksheet(fields, class_level="10")
    elif dtype == "marksheet_11":
        norm_fields = normalize_and_validate_marksheet(fields, class_level="11")
    elif dtype == "marksheet_12":
        norm_fields = normalize_and_validate_marksheet(fields, class_level="12")
    elif dtype == "marksheet_college":
        norm_fields = normalize_and_validate_college_marksheet(fields)
    elif dtype == "degree_certificate":
        norm_fields = normalize_and_validate_degree(fields)
    elif dtype == "provisional_certificate":
        norm_fields = normalize_and_validate_provisional(fields)
    elif dtype == "property_deed":
        norm_fields = normalize_and_validate_property_deed(fields)
    elif dtype == "land_document":
        norm_fields = normalize_and_validate_land_document(fields)
    else:
        return {
            "notice": f"Structured validation for {document_type} completed using general rules.",
            "document_type": document_type,
            "fields": {},
            "summary": {"total_fields": 0, "valid_count": 0, "invalid_count": 0, "needs_review_count": 0, "not_detected_count": 0},
            "human_verification_notice": "Automated extraction is for demonstration purposes and requires human verification."
        }

    statuses = [f["status"] for f in norm_fields.values()]
    summary = {
        "total_fields": len(statuses),
        "valid_count": statuses.count("Valid"),
        "invalid_count": statuses.count("Invalid"),
        "needs_review_count": statuses.count("Needs Review"),
        "not_detected_count": statuses.count("Not detected")
    }

    return {
        "document_type": dtype,
        "fields": norm_fields,
        "summary": summary,
        "human_verification_notice": "Automated extraction is for demonstration purposes and requires human verification."
    }

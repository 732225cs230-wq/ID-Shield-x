"""
IDShield-X: OCR Document Text Extraction Module
Step 3: OCR Processing and Structured Field Extraction
"""
import re
import os
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional

# Check if pytesseract and Pillow are available
TESSERACT_AVAILABLE = False
PIL_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    pass

try:
    import pytesseract
    # Check if tesseract binary is configured or in PATH
    windows_tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
    ]
    for p in windows_tesseract_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            TESSERACT_AVAILABLE = True
            break
    
    if not TESSERACT_AVAILABLE:
        try:
            pytesseract.get_tesseract_version()
            TESSERACT_AVAILABLE = True
        except Exception:
            TESSERACT_AVAILABLE = False
except ImportError:
    TESSERACT_AVAILABLE = False


def is_tesseract_available() -> bool:
    """Returns True if local Tesseract OCR engine is installed and ready."""
    return TESSERACT_AVAILABLE and PIL_AVAILABLE


def extract_text_from_image(filepath: Path, file_type: str, document_type: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
    """
    Extracts raw text from the uploaded image using Tesseract when available.
    It never invents document fields when OCR is unavailable.

    Returns:
        (extracted_text, engine_used, warning_message)
    """
    if not filepath.exists():
        return "", "None", f"File not found: {filepath.name}"

    # Handle PDF limitations gracefully
    if filepath.suffix.lower() == ".pdf" or file_type == "application/pdf":
        return (
            "[PDF DOCUMENT DETECTED]\n"
            "Notice: Direct PDF image rasterization requires the 'pdf2image' and 'poppler' libraries.\n"
            "For full optical screening, please upload a high-resolution PNG or JPG scan of the credential.",
            "PDF Handler (Notice)",
            "Direct PDF OCR requires Poppler. Please use PNG or JPG for optical evaluation."
        )

    # 1. Primary Engine: Tesseract OCR (if installed)
    if is_tesseract_available():
        try:
            img = Image.open(filepath)
            raw_text = pytesseract.image_to_string(img)
            if raw_text.strip():
                return raw_text.strip(), "Tesseract OCR Engine (Local)", None
        except Exception:
            pass

    return "", "OCR unavailable", (
        "No readable text could be extracted because the local Tesseract OCR engine is unavailable "
        "or the uploaded image could not be read. No document data has been inferred."
    )


def parse_structured_fields(raw_text: str, document_type: str) -> Dict[str, Any]:
    """
    Parses raw OCR text into structured fields based on the document profile.
    Strictly outputs 'Not detected' if a field cannot be identified.
    Supports all 17 document profiles across 5 categories.
    """
    if not raw_text:
        return {}

    lines = raw_text.splitlines()
    dtype = (document_type or "passport").strip().lower()

    if dtype == "passport":
        return extract_passport_fields(raw_text, lines)
    elif dtype == "visa":
        return extract_visa_fields(raw_text, lines)
    elif dtype in ("aadhaar", "national_id"):
        return extract_aadhaar_fields(raw_text, lines)
    elif dtype == "pan_card":
        return extract_pan_fields(raw_text, lines)
    elif dtype == "voter_id":
        return extract_voter_id_fields(raw_text, lines)
    elif dtype == "driving_license":
        return extract_driving_license_fields(raw_text, lines)
    elif dtype == "permit":
        return extract_permit_fields(raw_text, lines)
    elif dtype == "birth_certificate":
        return extract_birth_certificate_fields(raw_text, lines)
    elif dtype == "death_certificate":
        return extract_death_certificate_fields(raw_text, lines)
    elif dtype == "marksheet_10":
        return extract_marksheet_10_fields(raw_text, lines)
    elif dtype == "marksheet_11":
        return extract_marksheet_11_fields(raw_text, lines)
    elif dtype == "marksheet_12":
        return extract_marksheet_12_fields(raw_text, lines)
    elif dtype == "marksheet_college":
        return extract_marksheet_college_fields(raw_text, lines)
    elif dtype == "degree_certificate":
        return extract_degree_fields(raw_text, lines)
    elif dtype == "provisional_certificate":
        return extract_provisional_fields(raw_text, lines)
    elif dtype == "property_deed":
        return extract_property_deed_fields(raw_text, lines)
    elif dtype == "land_document":
        return extract_land_document_fields(raw_text, lines)
    else:
        # Fallback to general extraction
        return {
            "raw_text_length": len(raw_text),
            "notice": f"Generic extraction profile applied for {document_type}."
        }


def extract_passport_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts mandatory passport fields from VIZ and MRZ lines."""
    fields = {
        "name": "Not detected",
        "passport_number": "Not detected",
        "nationality": "Not detected",
        "dob": "Not detected",
        "expiry_date": "Not detected",
        "gender": "Not detected"
    }

    # 1. Search in Visual Inspection Zone (VIZ) via Specific Regex
    for line in lines:
        line_clean = line.strip()
        
        # Name: NAME: or SURNAME:
        m_name = re.search(r"(?:NAME|SURNAME|GIVEN NAMES?)[\.:\s]+([A-Z\s,]+)", line_clean, re.I)
        if m_name and fields["name"] == "Not detected":
            val = m_name.group(1).strip()
            if val and len(val) >= 2:
                fields["name"] = val

        # Passport Number: PASSPORT NO: or PASSPORT NUMBER:
        m_pass = re.search(r"PASSPORT\s*(?:NO|NUMBER|#|NUM)?[\.:\s]+([A-Z0-9]{7,9})\b", line_clean, re.I)
        if m_pass and fields["passport_number"] == "Not detected":
            fields["passport_number"] = m_pass.group(1).strip()

        # Nationality: NATIONALITY:
        m_nat = re.search(r"NATIONALITY[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_nat and fields["nationality"] == "Not detected":
            fields["nationality"] = m_nat.group(1).strip()

        # Date of Birth: DOB: or DATE OF BIRTH:
        m_dob = re.search(r"(?:DATE\s+OF\s+BIRTH|BIRTH\s+DATE|DOB)[\.:\s]+([0-9A-Z\s\/\.\-]+)", line_clean, re.I)
        if m_dob and fields["dob"] == "Not detected":
            fields["dob"] = m_dob.group(1).strip()

        # Expiry Date: EXPIRY DATE: or DATE OF EXPIRY: or EXPIRY:
        m_exp = re.search(r"(?:DATE\s+OF\s+EXPIRY|EXPIRY\s+DATE|EXPIRY)[\.:\s]+([0-9A-Z\s\/\.\-]+)", line_clean, re.I)
        if m_exp and fields["expiry_date"] == "Not detected":
            fields["expiry_date"] = m_exp.group(1).strip()

        # Gender / Sex: GENDER: M or SEX: M
        m_sex = re.search(r"(?:SEX|GENDER)[\.:\s]+([MFX])\b", line_clean, re.I)
        if m_sex and fields["gender"] == "Not detected":
            fields["gender"] = m_sex.group(1).upper()

    # 2. Check Machine Readable Zone (MRZ) (ICAO Doc 9303 TD3 standard fallback)
    mrz_lines = [l.strip() for l in lines if ("<" in l and len(l.strip()) >= 30)]
    
    if len(mrz_lines) >= 2:
        l1 = mrz_lines[-2]
        l2 = mrz_lines[-1]

        # Extract Name from MRZ Line 1 if not detected
        if fields["name"] == "Not detected" and l1.startswith("P<"):
            name_part = l1[5:].replace("<", " ").strip()
            name_part = re.sub(r"\s+", " ", name_part)
            if name_part:
                fields["name"] = name_part

        # Passport Number: pos 0-8
        if fields["passport_number"] == "Not detected" and len(l2) >= 9:
            p_num = l2[0:9].replace("<", "").strip()
            if p_num:
                fields["passport_number"] = p_num

        # Nationality: pos 10-12
        if fields["nationality"] == "Not detected" and len(l2) >= 13:
            nat_code = l2[10:13].replace("<", "").strip()
            if nat_code:
                fields["nationality"] = nat_code

        # DOB: pos 13-18 (YYMMDD)
        if fields["dob"] == "Not detected" and len(l2) >= 19:
            dob_raw = l2[13:19]
            if dob_raw.isdigit():
                fields["dob"] = f"{dob_raw[4:6]}-{dob_raw[2:4]}-19{dob_raw[0:2]}"

        # Gender: pos 20
        if fields["gender"] == "Not detected" and len(l2) >= 21:
            g = l2[20].upper()
            if g in ("M", "F", "X"):
                fields["gender"] = g

        # Expiry Date: pos 21-26 (YYMMDD)
        if fields["expiry_date"] == "Not detected" and len(l2) >= 27:
            exp_raw = l2[21:27]
            if exp_raw.isdigit():
                fields["expiry_date"] = f"{exp_raw[4:6]}-{exp_raw[2:4]}-20{exp_raw[0:2]}"

    return fields


def extract_visa_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts mandatory visa fields from VIZ text."""
    fields = {
        "visa_number": "Not detected",
        "visa_type": "Not detected",
        "entry_validity": "Not detected",
        "stay_duration": "Not detected"
    }

    for line in lines:
        line_clean = line.strip()

        # Visa Number: VISA NO: or VISA NUMBER: (strictly require NO/NUMBER so VISA TYPE does not match!)
        m_num = re.search(r"VISA\s*(?:NO|NUMBER|#|NUM)[\.:\s]+([A-Z0-9\-]+)\b", line_clean, re.I)
        if m_num and fields["visa_number"] == "Not detected":
            fields["visa_number"] = m_num.group(1).strip()

        # Visa Type: VISA TYPE: or CATEGORY:
        m_type = re.search(r"(?:VISA\s*TYPE|CATEGORY)[\.:\s]+([A-Z0-9\s\(\)\-]+)", line_clean, re.I)
        if m_type and fields["visa_type"] == "Not detected":
            fields["visa_type"] = m_type.group(1).strip()

        # Entry Validity: ENTRY VALIDITY: or VALID UNTIL:
        m_val = re.search(r"(?:ENTRY\s*VALIDITY|VALID\s*UNTIL|VALID\s*TILL)[\.:\s]+([0-9A-Z\s\/\.\-]+)", line_clean, re.I)
        if m_val and fields["entry_validity"] == "Not detected":
            fields["entry_validity"] = m_val.group(1).strip()

        # Stay Duration: STAY DURATION: or DURATION OF STAY:
        m_stay = re.search(r"(?:STAY\s*DURATION|DURATION\s*OF\s*STAY)[\.:\s]+([0-9A-Z\s]+)", line_clean, re.I)
        if m_stay and fields["stay_duration"] == "Not detected":
            fields["stay_duration"] = m_stay.group(1).strip()

    return fields


def extract_aadhaar_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts demographic fields from Aadhaar Card scans."""
    fields = {
        "name": "Not detected",
        "masked_aadhaar": "Not detected",
        "dob": "Not detected",
        "gender": "Not detected",
        "address": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_name = re.search(r"(?:NAME|ELECTOR|HOLDER)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["name"] == "Not detected" and "GOVERNMENT" not in line_clean.upper():
            fields["name"] = m_name.group(1).strip()

        m_uid = re.search(r"(?:AADHAAR\s*(?:NO|NUMBER)?|UID)[\.:\s]*([X0-9\s]{12,16})", line_clean, re.I)
        if m_uid and fields["masked_aadhaar"] == "Not detected":
            fields["masked_aadhaar"] = m_uid.group(1).strip()
        elif fields["masked_aadhaar"] == "Not detected":
            m_uid_raw = re.search(r"\b([X0-9]{4}\s+[X0-9]{4}\s+[0-9]{4})\b", line_clean)
            if m_uid_raw:
                fields["masked_aadhaar"] = m_uid_raw.group(1).strip()

        m_dob = re.search(r"(?:DOB|DATE\s+OF\s+BIRTH|YEAR\s+OF\s+BIRTH)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_dob and fields["dob"] == "Not detected":
            fields["dob"] = m_dob.group(1).strip()

        m_gen = re.search(r"(?:GENDER|SEX)[\.:\s]+(MALE|FEMALE|TRANSGENDER|M|F)\b", line_clean, re.I)
        if m_gen and fields["gender"] == "Not detected":
            fields["gender"] = m_gen.group(1).strip()

        m_addr = re.search(r"ADDRESS[\.:\s]+(.+)", line_clean, re.I)
        if m_addr and fields["address"] == "Not detected":
            fields["address"] = m_addr.group(1).strip()

    return fields


def extract_pan_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from PAN card scans."""
    fields = {
        "name": "Not detected",
        "pan_number": "Not detected",
        "father_name": "Not detected",
        "dob": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_pan = re.search(r"(?:PAN\s*(?:NO|NUMBER)?[\.:\s]+)?\b([A-Z]{5}[0-9]{4}[A-Z])\b", line_clean)
        if m_pan and fields["pan_number"] == "Not detected":
            fields["pan_number"] = m_pan.group(1).strip()

        m_name = re.search(r"(?:NAME|CARDHOLDER\s+NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["name"] == "Not detected" and "FATHER" not in line_clean.upper() and "DEPARTMENT" not in line_clean.upper():
            fields["name"] = m_name.group(1).strip()

        m_father = re.search(r"(?:FATHER(?:'S)?\s+NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_father and fields["father_name"] == "Not detected":
            fields["father_name"] = m_father.group(1).strip()

        m_dob = re.search(r"(?:DOB|DATE\s+OF\s+BIRTH)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_dob and fields["dob"] == "Not detected":
            fields["dob"] = m_dob.group(1).strip()

    return fields


def extract_voter_id_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from Voter ID (EPIC) card scans."""
    fields = {
        "name": "Not detected",
        "epic_number": "Not detected",
        "dob_or_age": "Not detected",
        "constituency": "Not detected",
        "address": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_epic = re.search(r"(?:EPIC\s*(?:NO|NUMBER)?[\.:\s]+)?\b([A-Z]{3}[0-9]{7})\b", line_clean, re.I)
        if m_epic and fields["epic_number"] == "Not detected":
            fields["epic_number"] = m_epic.group(1).strip()

        m_name = re.search(r"(?:ELECTOR\s+NAME|NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["name"] == "Not detected" and "COMMISSION" not in line_clean.upper():
            fields["name"] = m_name.group(1).strip()

        m_dob = re.search(r"(?:DOB\s*\/?\s*AGE|AGE|DATE\s+OF\s+BIRTH)[\.:\s]+([0-9A-Z\s\/\.\-\(\)]+)", line_clean, re.I)
        if m_dob and fields["dob_or_age"] == "Not detected":
            fields["dob_or_age"] = m_dob.group(1).strip()

        m_const = re.search(r"CONSTITUENCY[\.:\s]+([0-9A-Z\s\-]+)", line_clean, re.I)
        if m_const and fields["constituency"] == "Not detected":
            fields["constituency"] = m_const.group(1).strip()

        m_addr = re.search(r"ADDRESS[\.:\s]+(.+)", line_clean, re.I)
        if m_addr and fields["address"] == "Not detected":
            fields["address"] = m_addr.group(1).strip()

    return fields


def extract_driving_license_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from Driving Licence scans."""
    fields = {
        "name": "Not detected",
        "license_number": "Not detected",
        "dob": "Not detected",
        "issue_date": "Not detected",
        "expiry_date": "Not detected",
        "vehicle_class": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_dl = re.search(r"(?:DL\s*(?:NO|NUMBER)?|LICENCE\s*(?:NO|NUMBER)?)[\.:\s]+([A-Z0-9\-\s]{8,20})", line_clean, re.I)
        if m_dl and fields["license_number"] == "Not detected":
            fields["license_number"] = m_dl.group(1).strip()

        m_name = re.search(r"(?:HOLDER\s+NAME|NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["name"] == "Not detected" and "DEPARTMENT" not in line_clean.upper():
            fields["name"] = m_name.group(1).strip()

        m_dob = re.search(r"(?:DOB|DATE\s+OF\s+BIRTH)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_dob and fields["dob"] == "Not detected":
            fields["dob"] = m_dob.group(1).strip()

        m_iss = re.search(r"(?:ISSUE\s+DATE|DOI|DATE\s+OF\s+ISSUE)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_iss and fields["issue_date"] == "Not detected":
            fields["issue_date"] = m_iss.group(1).strip()

        m_exp = re.search(r"(?:EXPIRY\s+DATE|VALID\s+TILL|VALID\s+UPTO|DOE)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_exp and fields["expiry_date"] == "Not detected":
            fields["expiry_date"] = m_exp.group(1).strip()

        m_cov = re.search(r"(?:VEHICLE\s+CLASS|COV)[\.:\s]+([A-Z0-9\s\/\,\-]+)", line_clean, re.I)
        if m_cov and fields["vehicle_class"] == "Not detected":
            fields["vehicle_class"] = m_cov.group(1).strip()

    return fields


def extract_permit_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from Border Transit Permit scans."""
    fields = {
        "permit_number": "Not detected",
        "permit_type": "Not detected",
        "holder_name": "Not detected",
        "issue_date": "Not detected",
        "expiry_date": "Not detected",
        "issuing_authority": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_pnum = re.search(r"(?:PERMIT\s*(?:NO|NUMBER|ID)|PASS\s*NO)[\.:\s]+([A-Z0-9\-]+)", line_clean, re.I)
        if m_pnum and fields["permit_number"] == "Not detected":
            fields["permit_number"] = m_pnum.group(1).strip()

        m_ptype = re.search(r"(?:PERMIT\s*TYPE|CLASSIFICATION)[\.:\s]+([A-Z0-9\s\-]+)", line_clean, re.I)
        if m_ptype and fields["permit_type"] == "Not detected":
            fields["permit_type"] = m_ptype.group(1).strip()

        m_hname = re.search(r"(?:HOLDER\s*(?:NAME)?|ORGANIZATION)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_hname and fields["holder_name"] == "Not detected":
            fields["holder_name"] = m_hname.group(1).strip()

        m_iss = re.search(r"(?:ISSUE\s+DATE|VALID\s+FROM)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_iss and fields["issue_date"] == "Not detected":
            fields["issue_date"] = m_iss.group(1).strip()

        m_exp = re.search(r"(?:EXPIRY\s+DATE|VALID\s+UNTIL|VALID\s+TILL)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_exp and fields["expiry_date"] == "Not detected":
            fields["expiry_date"] = m_exp.group(1).strip()

        m_auth = re.search(r"(?:ISSUING\s+AUTHORITY|AUTHORITY)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_auth and fields["issuing_authority"] == "Not detected":
            fields["issuing_authority"] = m_auth.group(1).strip()

    return fields


def extract_birth_certificate_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from Birth Certificate scans."""
    fields = {
        "name": "Not detected",
        "dob": "Not detected",
        "place_of_birth": "Not detected",
        "parent_details": "Not detected",
        "registration_number": "Not detected",
        "registration_date": "Not detected",
        "issuing_authority": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_name = re.search(r"(?:NAME|CHILD\s+NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["name"] == "Not detected" and "DEPARTMENT" not in line_clean.upper() and "GOVERNMENT" not in line_clean.upper():
            fields["name"] = m_name.group(1).strip()

        m_dob = re.search(r"(?:DATE\s+OF\s+BIRTH|DOB)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_dob and fields["dob"] == "Not detected":
            fields["dob"] = m_dob.group(1).strip()

        m_pob = re.search(r"(?:PLACE\s+OF\s+BIRTH)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_pob and fields["place_of_birth"] == "Not detected":
            fields["place_of_birth"] = m_pob.group(1).strip()

        m_par = re.search(r"(?:PARENTS|FATHER\s*(?:&|AND)?\s*MOTHER)[\.:\s]+([A-Z\s&,]+)", line_clean, re.I)
        if m_par and fields["parent_details"] == "Not detected":
            fields["parent_details"] = m_par.group(1).strip()

        m_reg = re.search(r"(?:REGISTRATION\s*(?:NO|NUMBER)?|REG\s*NO)[\.:\s]+([A-Z0-9\-\/]+)", line_clean, re.I)
        if m_reg and fields["registration_number"] == "Not detected":
            fields["registration_number"] = m_reg.group(1).strip()

        m_regd = re.search(r"(?:REGISTRATION\s+DATE)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_regd and fields["registration_date"] == "Not detected":
            fields["registration_date"] = m_regd.group(1).strip()

        m_auth = re.search(r"(?:ISSUING\s+AUTHORITY|REGISTRAR)[\.:\s]+([A-Z0-9\s\(\),]+)", line_clean, re.I)
        if m_auth and fields["issuing_authority"] == "Not detected":
            fields["issuing_authority"] = m_auth.group(1).strip()

    return fields


def extract_death_certificate_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from Death Certificate scans."""
    fields = {
        "name": "Not detected",
        "date_of_death": "Not detected",
        "place_of_death": "Not detected",
        "registration_number": "Not detected",
        "registration_date": "Not detected",
        "issuing_authority": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_name = re.search(r"(?:NAME|DECEASED\s+NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["name"] == "Not detected" and "GOVERNMENT" not in line_clean.upper():
            fields["name"] = m_name.group(1).strip()

        m_dod = re.search(r"(?:DATE\s+OF\s+DEATH|DOD)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_dod and fields["date_of_death"] == "Not detected":
            fields["date_of_death"] = m_dod.group(1).strip()

        m_pod = re.search(r"(?:PLACE\s+OF\s+DEATH)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_pod and fields["place_of_death"] == "Not detected":
            fields["place_of_death"] = m_pod.group(1).strip()

        m_reg = re.search(r"(?:REGISTRATION\s*(?:NO|NUMBER)?|REG\s*NO)[\.:\s]+([A-Z0-9\-\/]+)", line_clean, re.I)
        if m_reg and fields["registration_number"] == "Not detected":
            fields["registration_number"] = m_reg.group(1).strip()

        m_regd = re.search(r"(?:REGISTRATION\s+DATE)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_regd and fields["registration_date"] == "Not detected":
            fields["registration_date"] = m_regd.group(1).strip()

        m_auth = re.search(r"(?:ISSUING\s+AUTHORITY|REGISTRAR)[\.:\s]+([A-Z0-9\s\(\),]+)", line_clean, re.I)
        if m_auth and fields["issuing_authority"] == "Not detected":
            fields["issuing_authority"] = m_auth.group(1).strip()

    return fields


def extract_marksheet_10_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from 10th Class Marksheet scans."""
    fields = {
        "student_name": "Not detected",
        "roll_number": "Not detected",
        "school_name": "Not detected",
        "exam_year": "Not detected",
        "subjects": "Not detected",
        "marks": "Not detected",
        "total_marks": "Not detected",
        "result": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_name = re.search(r"(?:STUDENT\s+NAME|CANDIDATE\s+NAME|NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["student_name"] == "Not detected" and "CENTRAL" not in line_clean.upper() and "BOARD" not in line_clean.upper():
            fields["student_name"] = m_name.group(1).strip()

        m_roll = re.search(r"(?:ROLL\s*(?:NUMBER|NO)?)[\.:\s]+([A-Z0-9]+)", line_clean, re.I)
        if m_roll and fields["roll_number"] == "Not detected":
            fields["roll_number"] = m_roll.group(1).strip()

        m_sch = re.search(r"(?:SCHOOL\s+NAME|SCHOOL|INSTITUTION)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_sch and fields["school_name"] == "Not detected":
            fields["school_name"] = m_sch.group(1).strip()

        m_yr = re.search(r"(?:EXAMINATION\s+YEAR|YEAR)[\.:\s]+([0-9]{4})", line_clean, re.I)
        if m_yr and fields["exam_year"] == "Not detected":
            fields["exam_year"] = m_yr.group(1).strip()

        m_sub = re.search(r"(?:SUBJECTS)[\.:\s]+(.+)", line_clean, re.I)
        if m_sub and fields["subjects"] == "Not detected":
            fields["subjects"] = m_sub.group(1).strip()

        m_tot = re.search(r"(?:TOTAL\s*MARKS|TOTAL)[\.:\s]+([0-9\s\/]+)", line_clean, re.I)
        if m_tot and fields["total_marks"] == "Not detected":
            fields["total_marks"] = m_tot.group(1).strip()

        m_res = re.search(r"(?:RESULT|FINAL\s+RESULT)[\.:\s]+(PASS|FAIL|COMPARTMENT)", line_clean, re.I)
        if m_res and fields["result"] == "Not detected":
            fields["result"] = m_res.group(1).upper().strip()

    if fields["marks"] == "Not detected" and fields["subjects"] != "Not detected":
        fields["marks"] = fields["subjects"]

    return fields


def extract_marksheet_11_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from 11th Class Marksheet scans."""
    fields = {
        "student_name": "Not detected",
        "roll_number": "Not detected",
        "school_name": "Not detected",
        "academic_year": "Not detected",
        "subjects": "Not detected",
        "marks": "Not detected",
        "total_marks": "Not detected",
        "result": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_name = re.search(r"(?:STUDENT\s+NAME|NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["student_name"] == "Not detected" and "SCHOOL" not in line_clean.upper():
            fields["student_name"] = m_name.group(1).strip()

        m_roll = re.search(r"(?:ROLL\s*(?:NUMBER|NO)?)[\.:\s]+([A-Z0-9]+)", line_clean, re.I)
        if m_roll and fields["roll_number"] == "Not detected":
            fields["roll_number"] = m_roll.group(1).strip()

        m_sch = re.search(r"(?:SCHOOL\s+NAME|SCHOOL)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_sch and fields["school_name"] == "Not detected":
            fields["school_name"] = m_sch.group(1).strip()

        m_yr = re.search(r"(?:ACADEMIC\s+YEAR|YEAR)[\.:\s]+([0-9]{4}(?:-[0-9]{2,4})?)", line_clean, re.I)
        if m_yr and fields["academic_year"] == "Not detected":
            fields["academic_year"] = m_yr.group(1).strip()

        m_sub = re.search(r"(?:SUBJECTS)[\.:\s]+(.+)", line_clean, re.I)
        if m_sub and fields["subjects"] == "Not detected":
            fields["subjects"] = m_sub.group(1).strip()

        m_tot = re.search(r"(?:TOTAL\s*MARKS|TOTAL)[\.:\s]+([0-9\s\/]+)", line_clean, re.I)
        if m_tot and fields["total_marks"] == "Not detected":
            fields["total_marks"] = m_tot.group(1).strip()

        m_res = re.search(r"(?:RESULT)[\.:\s]+(PASS|FAIL|PROMOTED)", line_clean, re.I)
        if m_res and fields["result"] == "Not detected":
            fields["result"] = m_res.group(1).upper().strip()

    if fields["marks"] == "Not detected" and fields["subjects"] != "Not detected":
        fields["marks"] = fields["subjects"]

    return fields


def extract_marksheet_12_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from 12th Class Marksheet scans."""
    fields = {
        "student_name": "Not detected",
        "roll_number": "Not detected",
        "school_name": "Not detected",
        "exam_year": "Not detected",
        "subjects": "Not detected",
        "marks": "Not detected",
        "total_marks": "Not detected",
        "percentage": "Not detected",
        "result": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_name = re.search(r"(?:STUDENT\s+NAME|NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["student_name"] == "Not detected" and "BOARD" not in line_clean.upper():
            fields["student_name"] = m_name.group(1).strip()

        m_roll = re.search(r"(?:ROLL\s*(?:NUMBER|NO)?)[\.:\s]+([A-Z0-9]+)", line_clean, re.I)
        if m_roll and fields["roll_number"] == "Not detected":
            fields["roll_number"] = m_roll.group(1).strip()

        m_sch = re.search(r"(?:SCHOOL\s+NAME|SCHOOL)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_sch and fields["school_name"] == "Not detected":
            fields["school_name"] = m_sch.group(1).strip()

        m_yr = re.search(r"(?:EXAMINATION\s+YEAR|YEAR)[\.:\s]+([0-9]{4})", line_clean, re.I)
        if m_yr and fields["exam_year"] == "Not detected":
            fields["exam_year"] = m_yr.group(1).strip()

        m_sub = re.search(r"(?:SUBJECTS)[\.:\s]+(.+)", line_clean, re.I)
        if m_sub and fields["subjects"] == "Not detected":
            fields["subjects"] = m_sub.group(1).strip()

        m_tot = re.search(r"(?:TOTAL\s*MARKS|TOTAL)[\.:\s]+([0-9\s\/]+)", line_clean, re.I)
        if m_tot and fields["total_marks"] == "Not detected":
            fields["total_marks"] = m_tot.group(1).strip()

        m_pct = re.search(r"(?:PERCENTAGE|PERCENT)[\.:\s]+([0-9\.]+\s*%)", line_clean, re.I)
        if m_pct and fields["percentage"] == "Not detected":
            fields["percentage"] = m_pct.group(1).strip()

        m_res = re.search(r"(?:RESULT)[\.:\s]+(PASS|FAIL|COMPARTMENT)", line_clean, re.I)
        if m_res and fields["result"] == "Not detected":
            fields["result"] = m_res.group(1).upper().strip()

    if fields["marks"] == "Not detected" and fields["subjects"] != "Not detected":
        fields["marks"] = fields["subjects"]

    return fields


def extract_marksheet_college_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from College / University Semester Marksheet scans."""
    fields = {
        "student_name": "Not detected",
        "register_number": "Not detected",
        "institution": "Not detected",
        "course": "Not detected",
        "semester": "Not detected",
        "subjects": "Not detected",
        "marks": "Not detected",
        "result": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_name = re.search(r"(?:STUDENT\s+NAME|NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["student_name"] == "Not detected" and "UNIVERSITY" not in line_clean.upper() and "FACULTY" not in line_clean.upper():
            fields["student_name"] = m_name.group(1).strip()

        m_reg = re.search(r"(?:REGISTER\s*(?:NUMBER|NO)?|ENROLLMENT\s*NO)[\.:\s]+([A-Z0-9\-]+)", line_clean, re.I)
        if m_reg and fields["register_number"] == "Not detected":
            fields["register_number"] = m_reg.group(1).strip()

        m_inst = re.search(r"(?:INSTITUTION|COLLEGE|UNIVERSITY)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_inst and fields["institution"] == "Not detected":
            fields["institution"] = m_inst.group(1).strip()

        m_crs = re.search(r"(?:COURSE|PROGRAM)[\.:\s]+([A-Z0-9\s&,]+)", line_clean, re.I)
        if m_crs and fields["course"] == "Not detected":
            fields["course"] = m_crs.group(1).strip()

        m_sem = re.search(r"(?:SEMESTER)[\.:\s]+([A-Z0-9\s\(\),]+)", line_clean, re.I)
        if m_sem and fields["semester"] == "Not detected":
            fields["semester"] = m_sem.group(1).strip()

        m_sub = re.search(r"(?:SUBJECTS)[\.:\s]+(.+)", line_clean, re.I)
        if m_sub and fields["subjects"] == "Not detected":
            fields["subjects"] = m_sub.group(1).strip()

        m_mrk = re.search(r"(?:MARKS\s*\/?\s*SGPA|CGPA|SGPA|MARKS)[\.:\s]+([0-9\.\s\/]+)", line_clean, re.I)
        if m_mrk and fields["marks"] == "Not detected":
            fields["marks"] = m_mrk.group(1).strip()

        m_res = re.search(r"(?:RESULT|SEMESTER\s+RESULT)[\.:\s]+(PASS|FAIL|PROMOTED)", line_clean, re.I)
        if m_res and fields["result"] == "Not detected":
            fields["result"] = m_res.group(1).upper().strip()

    return fields


def extract_degree_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from Degree Certificate scans."""
    fields = {
        "student_name": "Not detected",
        "register_number": "Not detected",
        "institution": "Not detected",
        "degree": "Not detected",
        "course": "Not detected",
        "award_year": "Not detected",
        "certificate_number": "Not detected",
        "issuing_authority": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_name = re.search(r"(?:CANDIDATE\s+NAME|NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["student_name"] == "Not detected" and "SENATE" not in line_clean.upper() and "CONVOCATION" not in line_clean.upper():
            fields["student_name"] = m_name.group(1).strip()

        m_reg = re.search(r"(?:ENROLLMENT\s*NO|REGISTER\s*NO|ROLL\s*NO)[\.:\s]+([A-Z0-9\-]+)", line_clean, re.I)
        if m_reg and fields["register_number"] == "Not detected":
            fields["register_number"] = m_reg.group(1).strip()

        m_inst = re.search(r"(?:INSTITUTION|UNIVERSITY)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_inst and fields["institution"] == "Not detected":
            fields["institution"] = m_inst.group(1).strip()

        m_deg = re.search(r"(?:DEGREE)[\.:\s]+([A-Z0-9\s&]+)", line_clean, re.I)
        if m_deg and fields["degree"] == "Not detected":
            fields["degree"] = m_deg.group(1).strip()

        m_crs = re.search(r"(?:COURSE|DISCIPLINE)[\.:\s]+([A-Z0-9\s&,]+)", line_clean, re.I)
        if m_crs and fields["course"] == "Not detected":
            fields["course"] = m_crs.group(1).strip()

        m_yr = re.search(r"(?:AWARD\s+YEAR|YEAR)[\.:\s]+([0-9]{4})", line_clean, re.I)
        if m_yr and fields["award_year"] == "Not detected":
            fields["award_year"] = m_yr.group(1).strip()

        m_sno = re.search(r"(?:CERTIFICATE\s*(?:SERIAL\s*)?NO|SERIAL\s*NO)[\.:\s]+([A-Z0-9\-]+)", line_clean, re.I)
        if m_sno and fields["certificate_number"] == "Not detected":
            fields["certificate_number"] = m_sno.group(1).strip()

        m_auth = re.search(r"(?:ISSUING\s+AUTHORITY|AUTHORITY)[\.:\s]+([A-Z0-9\s&,]+)", line_clean, re.I)
        if m_auth and fields["issuing_authority"] == "Not detected":
            fields["issuing_authority"] = m_auth.group(1).strip()

    return fields


def extract_provisional_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from Provisional Certificate scans."""
    fields = {
        "student_name": "Not detected",
        "register_number": "Not detected",
        "institution": "Not detected",
        "degree_course": "Not detected",
        "year": "Not detected",
        "certificate_number": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_name = re.search(r"(?:STUDENT\s+NAME|NAME)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_name and fields["student_name"] == "Not detected" and "OFFICE" not in line_clean.upper() and "EXAMINATIONS" not in line_clean.upper():
            fields["student_name"] = m_name.group(1).strip()

        m_reg = re.search(r"(?:REGISTER\s*(?:NUMBER|NO)?|ENROLLMENT\s*NO)[\.:\s]+([A-Z0-9\-]+)", line_clean, re.I)
        if m_reg and fields["register_number"] == "Not detected":
            fields["register_number"] = m_reg.group(1).strip()

        m_inst = re.search(r"(?:INSTITUTION|COLLEGE|UNIVERSITY)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_inst and fields["institution"] == "Not detected":
            fields["institution"] = m_inst.group(1).strip()

        m_deg = re.search(r"(?:DEGREE\s*(?:&|AND)?\s*COURSE|DEGREE)[\.:\s]+([A-Z0-9\s\(\)&,]+)", line_clean, re.I)
        if m_deg and fields["degree_course"] == "Not detected":
            fields["degree_course"] = m_deg.group(1).strip()

        m_yr = re.search(r"(?:PASSING\s+YEAR|YEAR)[\.:\s]+([0-9]{4})", line_clean, re.I)
        if m_yr and fields["year"] == "Not detected":
            fields["year"] = m_yr.group(1).strip()

        m_cert = re.search(r"(?:CERTIFICATE\s*NUMBER|CERTIFICATE\s*NO)[\.:\s]+([A-Z0-9\-]+)", line_clean, re.I)
        if m_cert and fields["certificate_number"] == "Not detected":
            fields["certificate_number"] = m_cert.group(1).strip()

    return fields


def extract_property_deed_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from Property / Sale Deed scans."""
    fields = {
        "document_number": "Not detected",
        "registration_number": "Not detected",
        "deed_date": "Not detected",
        "buyer_details": "Not detected",
        "seller_details": "Not detected",
        "property_reference": "Not detected",
        "registration_office": "Not detected",
        "area_location": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_doc = re.search(r"(?:DOCUMENT\s*NUMBER|DOC\s*NO)[\.:\s]+([A-Z0-9\-\/]+)", line_clean, re.I)
        if m_doc and fields["document_number"] == "Not detected":
            fields["document_number"] = m_doc.group(1).strip()

        m_reg = re.search(r"(?:REGISTRATION\s*NUMBER|REG\s*NO)[\.:\s]+([A-Z0-9\-\/]+)", line_clean, re.I)
        if m_reg and fields["registration_number"] == "Not detected":
            fields["registration_number"] = m_reg.group(1).strip()

        m_dt = re.search(r"(?:DEED\s*DATE|EXECUTION\s*DATE)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_dt and fields["deed_date"] == "Not detected":
            fields["deed_date"] = m_dt.group(1).strip()

        m_buy = re.search(r"(?:BUYER|PURCHASER)[\.:\s]+([A-Z\s,]+)", line_clean, re.I)
        if m_buy and fields["buyer_details"] == "Not detected":
            fields["buyer_details"] = m_buy.group(1).strip()

        m_sel = re.search(r"(?:SELLER|VENDOR)[\.:\s]+([A-Z\s,]+)", line_clean, re.I)
        if m_sel and fields["seller_details"] == "Not detected":
            fields["seller_details"] = m_sel.group(1).strip()

        m_prop = re.search(r"(?:PROPERTY|SCHEDULE|PLOT)[\.:\s]+(.+)", line_clean, re.I)
        if m_prop and fields["property_reference"] == "Not detected":
            fields["property_reference"] = m_prop.group(1).strip()

        m_off = re.search(r"(?:REGISTRATION\s*OFFICE|OFFICE)[\.:\s]+([A-Z0-9\s,]+)", line_clean, re.I)
        if m_off and fields["registration_office"] == "Not detected":
            fields["registration_office"] = m_off.group(1).strip()

        m_loc = re.search(r"(?:LOCATION|AREA)[\.:\s]+(.+)", line_clean, re.I)
        if m_loc and fields["area_location"] == "Not detected":
            fields["area_location"] = m_loc.group(1).strip()

    return fields


def extract_land_document_fields(raw_text: str, lines: List[str]) -> Dict[str, str]:
    """Extracts fields from Land Records (Khatauni / Patta / ROR)."""
    fields = {
        "document_number": "Not detected",
        "survey_reference": "Not detected",
        "owner_name": "Not detected",
        "location_details": "Not detected",
        "land_area": "Not detected",
        "issue_date": "Not detected",
        "issuing_office": "Not detected"
    }
    for line in lines:
        line_clean = line.strip()
        m_rec = re.search(r"(?:RECORD\s*NUMBER|MUTATION\s*ID|RECORD\s*NO)[\.:\s]+([A-Z0-9\-\/]+)", line_clean, re.I)
        if m_rec and fields["document_number"] == "Not detected":
            fields["document_number"] = m_rec.group(1).strip()

        m_sur = re.search(r"(?:SURVEY\s*(?:\/|\s*&)?\s*KHASRA\s*NO|KHASRA|KHATA)[\.:\s]+(.+)", line_clean, re.I)
        if m_sur and fields["survey_reference"] == "Not detected":
            fields["survey_reference"] = m_sur.group(1).strip()

        m_own = re.search(r"(?:OWNER\s*NAME|PATTADAR|OWNER)[\.:\s]+([A-Z\s]+)", line_clean, re.I)
        if m_own and fields["owner_name"] == "Not detected" and "DEPARTMENT" not in line_clean.upper():
            fields["owner_name"] = m_own.group(1).strip()

        m_loc = re.search(r"(?:LOCATION|VILLAGE)[\.:\s]+(.+)", line_clean, re.I)
        if m_loc and fields["location_details"] == "Not detected":
            fields["location_details"] = m_loc.group(1).strip()

        m_area = re.search(r"(?:LAND\s*EXTENT|EXTENT|AREA)[\.:\s]+(.+)", line_clean, re.I)
        if m_area and fields["land_area"] == "Not detected":
            fields["land_area"] = m_area.group(1).strip()

        m_dt = re.search(r"(?:ISSUE\s*DATE|DATE)[\.:\s]+([0-9\/\.\-]+)", line_clean, re.I)
        if m_dt and fields["issue_date"] == "Not detected":
            fields["issue_date"] = m_dt.group(1).strip()

        m_off = re.search(r"(?:ISSUING\s*OFFICE|OFFICE)[\.:\s]+([A-Z0-9\s,\/]+)", line_clean, re.I)
        if m_off and fields["issuing_office"] == "Not detected":
            fields["issuing_office"] = m_off.group(1).strip()

    return fields

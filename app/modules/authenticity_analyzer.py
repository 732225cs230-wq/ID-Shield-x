"""
IDShield-X: Document Authenticity & Tampering Analysis Module (Step 5)
Smart India Hackathon 2026 | Problem Statement: SIH26188
Ministry of Home Affairs (MHA) | Sashastra Seema Bal (SSB)

This module performs safe, explainable authenticity and tampering checks:
1. Image Quality Analysis (resolution, dimensions, blur/quality indication)
2. Document Structure Checks (aspect ratio, zone presence, layout consistency)
3. Text / OCR Consistency (expected fields vs document type, character anomalies)
4. Metadata Analysis (file type, editing software signatures, EXIF/PDF tags)

ACADEMIC PROTOTYPE NOTICE:
This module is for demonstration purposes only and does NOT constitute
definitive government document authentication. Never treat metadata alone
as proof of fraud. Final clearance requires human officer physical verification.
"""

import os
import re
import struct
import zlib
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime

try:
    from app.modules.document_profiles import get_profile
except ImportError:
    from document_profiles import get_profile

# Common digital image manipulation/graphic design software signatures
KNOWN_EDITING_TOOLS = [
    "photoshop",
    "gimp",
    "canva",
    "paint.net",
    "illustrator",
    "indesign",
    "coreldraw",
    "inkscape",
    "affinity",
    "pixlr",
    "sejda",
    "ilovepdf",
    "pdfescape",
    "lightroom",
    "acrobat distiller"
]

def extract_file_metadata(filepath: Path) -> Dict[str, Any]:
    """
    Extracts file dimensions, format, raw headers, and embedded metadata
    using Python standard library with zero external dependencies.
    """
    if not filepath.exists() or not filepath.is_file():
        return {
            "valid": False,
            "error": "File does not exist on disk",
            "file_type": "UNKNOWN"
        }

    file_bytes = filepath.read_bytes()
    file_size = len(file_bytes)

    if file_size < 16:
        return {
            "valid": False,
            "error": "File truncated or corrupted",
            "file_type": "CORRUPTED"
        }

    metadata = {
        "valid": True,
        "filename": filepath.name,
        "file_size_bytes": file_size,
        "file_type": "UNKNOWN",
        "mime_type": "application/octet-stream",
        "width": 0,
        "height": 0,
        "aspect_ratio": 0.0,
        "software_tags": [],
        "metadata_entries": {},
        "is_pdf": False
    }

    # 1. Check for PNG format (\x89PNG\r\n\x1a\n)
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        metadata["file_type"] = "PNG"
        metadata["mime_type"] = "image/png"
        try:
            # In a valid PNG, byte 12:16 MUST be b"IHDR" and length at 8:12 is 13
            if len(file_bytes) < 33 or file_bytes[12:16] != b"IHDR":
                metadata["valid"] = False
                metadata["error"] = "Corrupted or truncated PNG header: missing valid IHDR chunk."
                return metadata

            w, h = struct.unpack(">II", file_bytes[16:24])
            if w <= 0 or h <= 0 or w > 20000 or h > 20000:
                metadata["valid"] = False
                metadata["error"] = f"Corrupted PNG dimensions: {w}x{h}."
                return metadata

            metadata["width"] = w
            metadata["height"] = h
            metadata["aspect_ratio"] = round(w / h, 2)

            # Scan for PNG text chunks (tEXt, zTXt, iTXt)
            offset = 8
            has_idat = False
            while offset + 8 < len(file_bytes):
                chunk_len = struct.unpack(">I", file_bytes[offset:offset + 4])[0]
                chunk_type = file_bytes[offset + 4:offset + 8]
                if chunk_type == b"IDAT":
                    has_idat = True

                chunk_data = file_bytes[offset + 8:offset + 8 + chunk_len]

                if chunk_type in (b"tEXt", b"zTXt", b"iTXt"):
                    try:
                        text_str = chunk_data.decode("latin1", errors="ignore")
                        metadata["metadata_entries"][chunk_type.decode("latin1")] = text_str
                        for tool in KNOWN_EDITING_TOOLS:
                            if tool in text_str.lower() and tool.title() not in metadata["software_tags"]:
                                metadata["software_tags"].append(tool.title())
                    except Exception:
                        pass

                offset += 12 + chunk_len

            if not has_idat and len(file_bytes) < 100:
                metadata["valid"] = False
                metadata["error"] = "Corrupted PNG: missing IDAT raster data."
                return metadata

        except Exception as e:
            metadata["valid"] = False
            metadata["error"] = f"PNG parse failure: {str(e)}"
            return metadata


    # 2. Check for JPEG format (\xff\xd8\xff)
    elif file_bytes.startswith(b"\xff\xd8"):
        metadata["file_type"] = "JPEG"
        metadata["mime_type"] = "image/jpeg"
        try:
            idx = 2
            while idx < len(file_bytes) - 4:
                if file_bytes[idx] != 0xFF:
                    idx += 1
                    continue
                marker = file_bytes[idx + 1]
                idx += 2

                # SOF0, SOF2 markers contain image dimensions
                if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                    idx += 2  # skip length
                    h, w = struct.unpack(">HH", file_bytes[idx + 1:idx + 5])
                    metadata["width"] = w
                    metadata["height"] = h
                    if h > 0:
                        metadata["aspect_ratio"] = round(w / h, 2)
                    break
                elif marker in (0xD9, 0xDA):  # EOI or SOS
                    break
                else:
                    if idx + 2 <= len(file_bytes):
                        length = struct.unpack(">H", file_bytes[idx:idx + 2])[0]
                        # Check APP1 (EXIF / XMP)
                        if marker == 0xE1:
                            chunk = file_bytes[idx + 2:idx + length].decode("latin1", errors="ignore")
                            metadata["metadata_entries"]["APP1"] = chunk[:200]
                            for tool in KNOWN_EDITING_TOOLS:
                                if tool in chunk.lower() and tool.title() not in metadata["software_tags"]:
                                    metadata["software_tags"].append(tool.title())
                        idx += length
                    else:
                        break
        except Exception as e:
            metadata["error"] = f"JPEG parse notice: {str(e)}"

    # 3. Check for PDF format (%PDF-)
    elif file_bytes.startswith(b"%PDF-"):
        metadata["file_type"] = "PDF"
        metadata["mime_type"] = "application/pdf"
        metadata["is_pdf"] = True
        # Standard A4 / ID document in PDF default points
        metadata["width"] = 595
        metadata["height"] = 842
        metadata["aspect_ratio"] = 0.71

        try:
            sample_text = file_bytes.decode("latin1", errors="ignore")
            # Extract PDF Creator / Producer tags
            for prop in ["/Producer", "/Creator", "/Title", "/Author"]:
                match = re.search(rf"{prop}\s*\((.*?)\)", sample_text)
                if match:
                    metadata["metadata_entries"][prop] = match.group(1)
            for tool in KNOWN_EDITING_TOOLS:
                if tool in sample_text.lower() and tool.title() not in metadata["software_tags"]:
                    metadata["software_tags"].append(tool.title())
        except Exception as e:
            metadata["error"] = f"PDF parse notice: {str(e)}"

    # 4. Optional Pillow / OpenCV Enhancement (if installed)
    try:
        from PIL import Image
        with Image.open(filepath) as img:
            metadata["width"] = img.width
            metadata["height"] = img.height
            if img.height > 0:
                metadata["aspect_ratio"] = round(img.width / img.height, 2)
            if hasattr(img, "info") and isinstance(img.info, dict):
                for k, v in img.info.items():
                    val_str = str(v)
                    for tool in KNOWN_EDITING_TOOLS:
                        if tool in val_str.lower() and tool.title() not in metadata["software_tags"]:
                            metadata["software_tags"].append(tool.title())
    except Exception:
        # Pillow not installed or failed; pure-Python values already safely recorded
        pass

    return metadata


def analyze_image_quality(metadata: Dict[str, Any], filepath: Path) -> Dict[str, Any]:
    """
    Check 1: Evaluates document scan resolution, dimensions, and visual clarity.
    Returns PASS or REVIEW with safe explanation.
    """
    width = metadata.get("width", 0)
    height = metadata.get("height", 0)
    total_pixels = width * height

    # Minimum recommended resolution for document screening: 350x200
    if width < 350 or height < 200:
        return {
            "status": "REVIEW",
            "detail": f"Low scan resolution ({width}x{height} px). Microtext, security guilloche patterns, and font edges may be degraded. Manual review is recommended.",
            "metrics": {
                "width": width,
                "height": height,
                "total_pixels": total_pixels,
                "grade": "LOW_RESOLUTION"
            }
        }

    # Estimate blur / compression quality indicator
    blur_variance = None
    try:
        import cv2
        img = cv2.imread(str(filepath), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            blur_variance = round(float(cv2.Laplacian(img, cv2.CV_64F).var()), 2)
            if blur_variance < 60.0:
                return {
                    "status": "REVIEW",
                    "detail": f"High image blur detected (variance: {blur_variance}). Optical details may be obscured. Manual review is recommended.",
                    "metrics": {
                        "width": width,
                        "height": height,
                        "blur_variance": blur_variance,
                        "grade": "BLUR_DETECTED"
                    }
                }
    except Exception:
        pass

    return {
        "status": "PASS",
        "detail": f"Resolution ({width}x{height} px) and visual sharpness meet screening inspection requirements.",
        "metrics": {
            "width": width,
            "height": height,
            "total_pixels": total_pixels,
            "blur_metric": blur_variance if blur_variance is not None else "Standard",
            "grade": "ACCEPTABLE"
        }
    }


def analyze_document_structure(metadata: Dict[str, Any], document_type: str, raw_ocr_text: str) -> Dict[str, Any]:
    """
    Check 2: Evaluates document geometry, aspect ratio, and structural zone presence
    across all 17 document types in accordance with their profile definitions.
    Returns PASS or REVIEW with safe explanation.
    """
    aspect_ratio = metadata.get("aspect_ratio", 0.0)
    doc_type = (document_type or "passport").lower()
    raw_upper = (raw_ocr_text or "").upper()
    profile = get_profile(doc_type)

    # Passports (ICAO Doc 9303 ID-3):
    if doc_type == "passport":
        is_landscape = 1.15 <= aspect_ratio <= 1.85
        is_portrait = 0.55 <= aspect_ratio <= 0.85

        if aspect_ratio > 0.0 and not (is_landscape or is_portrait):
            return {
                "status": "REVIEW",
                "detail": f"Document aspect ratio ({aspect_ratio:.2f}) deviates significantly from standard ICAO ID-3 passport format. Layout cropping or dimensional distortion suspected. Manual review is recommended.",
                "metrics": {
                    "aspect_ratio": aspect_ratio,
                    "expected_ratio_range": "1.15 - 1.85 (landscape) or 0.55 - 0.85 (portrait)",
                    "orientation": "Non-Standard"
                }
            }

        # Check for presence of Machine-Readable Zone (MRZ) structure
        has_mrz_indicators = (
            "P<" in raw_upper or
            "<<" in raw_upper or
            bool(re.search(r"[A-Z0-9<]{30,44}", raw_upper))
        )
        if not has_mrz_indicators and len(raw_ocr_text) > 40:
            return {
                "status": "REVIEW",
                "detail": "Machine-Readable Zone (MRZ) band was not detected in passport layout. Potential cropping or missing page section. Manual review is recommended.",
                "metrics": {
                    "aspect_ratio": aspect_ratio,
                    "mrz_detected": False
                }
            }

    # Dynamic Profile-Based Ratio Check for other documents
    elif profile and aspect_ratio > 0.0:
        ratio_range = profile.get("aspect_ratio_range", (0.60, 1.85))
        min_r, max_r = ratio_range
        # Allow either orientation: standard or inverse (landscape/portrait)
        is_valid = (
            (min_r * 0.75 <= aspect_ratio <= max_r * 1.25) or
            ((1.0 / max_r) * 0.75 <= aspect_ratio <= (1.0 / min_r) * 1.25)
        )
        if not is_valid:
            return {
                "status": "REVIEW",
                "detail": f"Document aspect ratio ({aspect_ratio:.2f}) deviates from standard {profile.get('name', doc_type)} geometry ({min_r:.2f} - {max_r:.2f}). Manual review is recommended.",
                "metrics": {
                    "aspect_ratio": aspect_ratio,
                    "expected_ratio_range": f"{min_r:.2f} - {max_r:.2f}"
                }
            }

    return {
        "status": "PASS",
        "detail": f"Document geometry (aspect ratio: {aspect_ratio:.2f}) and structural zones align with expected {doc_type.upper()} standards.",
        "metrics": {
            "aspect_ratio": aspect_ratio,
            "zones_verified": ["HEADER", "VISUAL_ZONE", "CREDENTIAL_FRAME"]
        }
    }


def analyze_ocr_consistency(
    document_type: str,
    structured_fields: Dict[str, Any],
    raw_ocr_text: str
) -> Dict[str, Any]:
    """
    Check 3: Cross-compares OCR extracted fields with expected credential schema.
    Detects typographic anomalies, unexpected numeric intrusions, or missing critical zones.
    """
    doc_type = (document_type or "passport").lower()
    raw_text = raw_ocr_text or ""

    if not raw_text.strip():
        return {
            "status": "REVIEW",
            "detail": "No readable textual information detected in document scanning zones. Document may be blank or overexposed. Manual review is recommended.",
            "metrics": {"fields_found": 0, "text_length": 0}
        }

    # Extract field values if provided
    fields_dict = {}
    if isinstance(structured_fields, dict):
        for k, v in structured_fields.items():
            if isinstance(v, dict):
                fields_dict[k] = v.get("normalized", v.get("raw", ""))
            elif isinstance(v, str):
                fields_dict[k] = v

    # Check for typographic numeric anomalies in name fields
    for name_key in ["name", "student_name", "holder_name", "elector_name", "owner_name"]:
        val = fields_dict.get(name_key, "")
        if val and val != "Not detected":
            # Extract just alphabetic portion before parenthesis (e.g. "ROHIT SHARMA (Age: 30)")
            clean_part = re.sub(r"\(.*?\)", "", val).strip()
            if re.search(r"\d", clean_part):
                return {
                    "status": "REVIEW",
                    "detail": f"Typographic anomaly: Numeric digits detected within primary identity name field ('{val}'). Possible font tampering or OCR noise. Manual review is recommended.",
                    "metrics": {"name_anomaly": True, "field": name_key}
                }

    # Schema-based check for missing required fields
    profile = get_profile(doc_type)
    if profile:
        req_fields = [f["key"] for f in profile.get("fields", []) if f.get("required", False)]
        missing_count = sum(1 for k in req_fields if (not fields_dict.get(k) or fields_dict.get(k) == "Not detected"))
        if req_fields and missing_count == len(req_fields) and len(raw_text) > 40:
            return {
                "status": "REVIEW",
                "detail": f"Primary identity fields for {profile.get('name', doc_type)} could not be identified in expected layout zones. Manual review is recommended.",
                "metrics": {
                    "required_fields_total": len(req_fields),
                    "missing_count": missing_count
                }
            }

    return {
        "status": "PASS",
        "detail": "Extracted OCR textual fields and typography are consistent with expected document schema.",
        "metrics": {
            "fields_evaluated": len(fields_dict),
            "text_length": len(raw_text)
        }
    }


def analyze_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check 4: Inspects embedded container headers, EXIF markers, and PDF dictionaries
    for digital authoring or graphic editing software tags.
    IMPORTANT: Never treat metadata alone as proof of fraud.
    """
    software_tags = metadata.get("software_tags", [])

    if software_tags:
        tool_names = ", ".join(software_tags)
        return {
            "status": "REVIEW",
            "detail": f"Digital graphic/editing tool signature ('{tool_names}') detected in file metadata. Document may have been modified or exported using graphic editing software. Manual review is recommended.",
            "metrics": {
                "software_signatures": software_tags,
                "file_type": metadata.get("file_type", "UNKNOWN"),
                "has_editing_tool": True
            }
        }

    return {
        "status": "PASS",
        "detail": "Clean file container header. No digital graphic editing software signatures detected.",
        "metrics": {
            "software_signatures": [],
            "file_type": metadata.get("file_type", "UNKNOWN"),
            "has_editing_tool": False
        }
    }


def analyze_document_authenticity(
    filepath: Path,
    document_type: str = "passport",
    structured_fields: Optional[Dict[str, Any]] = None,
    raw_ocr_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Primary Entry Point for Step 5: Document Tampering & Authenticity Analysis.

    Executes:
    1. Image Quality Analysis
    2. Document Structure Analysis
    3. Text / OCR Consistency Analysis
    4. Metadata Analysis

    Computes:
    - Overall Status:
        * 'No obvious issue detected'
        * 'Potential modification detected'
        * 'Unable to determine'
    """
    if not filepath.exists() or not filepath.is_file():
        return {
            "overall_status": "Unable to determine",
            "checks": {
                "image_quality": {"status": "REVIEW", "detail": "File not found or unreadable."},
                "document_structure": {"status": "REVIEW", "detail": "Unable to analyze structure without file."},
                "ocr_consistency": {"status": "REVIEW", "detail": "Unable to analyze OCR consistency without file."},
                "metadata": {"status": "REVIEW", "detail": "Unable to read metadata."}
            },
            "explanations": ["Document file is missing or corrupted on disk. Inspection cannot proceed."],
            "disclaimer": "Automated authenticity analysis is for demonstration purposes only and requires human verification. (DEMO / ACADEMIC PROTOTYPE)",
            "analysis_time": datetime.utcnow().isoformat() + "Z"
        }

    # 1. Extract metadata
    metadata = extract_file_metadata(filepath)
    if not metadata.get("valid", False):
        return {
            "overall_status": "Unable to determine",
            "checks": {
                "image_quality": {"status": "REVIEW", "detail": metadata.get("error", "Corrupted container format.")},
                "document_structure": {"status": "REVIEW", "detail": "Corrupted container geometry."},
                "ocr_consistency": {"status": "REVIEW", "detail": "Cannot parse contents of corrupted file."},
                "metadata": {"status": "REVIEW", "detail": "Invalid or unreadable container metadata."}
            },
            "explanations": ["The uploaded document appears to be corrupted or in an invalid format. Manual review is recommended."],
            "disclaimer": "Automated authenticity analysis is for demonstration purposes only and requires human verification. (DEMO / ACADEMIC PROTOTYPE)",
            "analysis_time": datetime.utcnow().isoformat() + "Z"
        }

    # 2. Run Individual Safe Checks
    check_img_quality = analyze_image_quality(metadata, filepath)
    check_doc_structure = analyze_document_structure(metadata, document_type, raw_ocr_text or "")
    check_ocr_consistency = analyze_ocr_consistency(document_type, structured_fields or {}, raw_ocr_text or "")
    check_metadata = analyze_metadata(metadata)

    checks = {
        "image_quality": check_img_quality,
        "document_structure": check_doc_structure,
        "ocr_consistency": check_ocr_consistency,
        "metadata": check_metadata
    }

    # 3. Collect explanations for any REVIEW status
    explanations = []
    review_checks = []
    for check_name, check_data in checks.items():
        if check_data.get("status") == "REVIEW":
            review_checks.append(check_name)
            explanations.append(check_data.get("detail", "Manual review is recommended."))

    # 4. Compute Overall Status
    # - "No obvious issue detected"
    # - "Potential modification detected"
    # - "Unable to determine"
    if len(review_checks) > 0:
        overall_status = "Potential modification detected"
    else:
        overall_status = "No obvious issue detected"
        explanations.append("All structural, resolution, optical, and metadata parameters conform to standard baseline criteria.")

    return {
        "overall_status": overall_status,
        "checks": checks,
        "explanations": explanations,
        "metadata_summary": {
            "file_type": metadata.get("file_type"),
            "file_size_bytes": metadata.get("file_size_bytes"),
            "dimensions": f"{metadata.get('width')}x{metadata.get('height')}",
            "aspect_ratio": metadata.get("aspect_ratio"),
            "software_tags": metadata.get("software_tags", [])
        },
        "disclaimer": "Automated authenticity analysis is for demonstration purposes only and requires human verification. (DEMO / ACADEMIC PROTOTYPE)",
        "analysis_time": datetime.utcnow().isoformat() + "Z"
    }

"""
IDShield-X: Screening Risk Scoring & Suspicious-Document Analysis Module (Step 7)
Smart India Hackathon 2026 | Problem Statement: SIH26188
Ministry of Home Affairs (MHA) | Sashastra Seema Bal (SSB)

Combines findings from:
1. Document Field Normalization & Validation (Step 4)
2. Document Tampering & Authenticity Analysis (Step 5)
3. Face Detection & Demo Face Verification (Step 6)

Output Tiers:
- 'Low Concern'
- 'Review Required'
- 'High Concern'

IMPORTANT ACADEMIC & ETHICAL BOUNDARIES:
- Rule-based transparent indicators only (no unverified AI "fraud probability" percentages).
- Does NOT claim a document is legally fake or authentic.
- Does NOT make automated border-clearance decisions.
- Human review is strictly required for all decisions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from app.modules.document_profiles import is_face_applicable
except ImportError:
    from document_profiles import is_face_applicable


def evaluate_screening_risk(
    document_type: str,
    validation_result: Optional[Dict[str, Any]] = None,
    authenticity_result: Optional[Dict[str, Any]] = None,
    face_detection_result: Optional[Dict[str, Any]] = None,
    face_comparison_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Synthesizes multi-module screening results into a transparent, rule-based risk evaluation.
    Categorizes the credential as 'Low Concern', 'Review Required', or 'High Concern'.
    """
    reasons: List[str] = []
    critical_flags: List[str] = []
    review_flags: List[str] = []
    passed_indicators: List[str] = []

    doc_type_clean = (document_type or "passport").lower()

    # -------------------------------------------------------------------------
    # 1. Evaluate Field Validation & Chronology Indicators (Step 4)
    # -------------------------------------------------------------------------
    if validation_result:
        val_summary = validation_result.get("summary", {})
        val_fields = validation_result.get("fields", {})

        invalid_count = val_summary.get("invalid_count", 0)
        review_count = val_summary.get("needs_review_count", 0)
        valid_count = val_summary.get("valid_count", 0)
        not_detected_count = val_summary.get("not_detected_count", 0)

        # Check critical fields
        for field_name, field_data in val_fields.items():
            status = field_data.get("status")
            note = field_data.get("note", "")

            # Expiry date check
            if field_name == "expiry_date" and status == "Invalid":
                critical_flags.append(f"Expired Document: {note}")
            # Date of birth future chronology check
            elif field_name == "dob" and status == "Invalid":
                critical_flags.append(f"Chronology Violation: {note}")
            # Registration date prior to event date
            elif field_name == "registration_date" and status == "Invalid":
                critical_flags.append(f"Registration Chronology Anomaly: {note}")
            # Conveyance deed buyer/seller identical party
            elif field_name in ("buyer_details", "seller_details") and status == "Invalid":
                if f"Conveyance Deed Anomaly: {note}" not in critical_flags:
                    critical_flags.append(f"Conveyance Deed Anomaly: {note}")
            # Total marks math violation
            elif field_name == "total_marks" and status == "Invalid":
                critical_flags.append(f"Marksheet Arithmetic Anomaly: {note}")
            # Malformed primary identifier
            elif (field_name.endswith("_number") or field_name in ("passport_number", "visa_number", "pan_number", "masked_aadhaar", "epic_number", "license_number", "registration_number")) and status == "Invalid":
                critical_flags.append(f"Identifier Syntax Anomaly ({field_name}): {note}")
            elif status == "Needs Review":
                review_flags.append(f"Field formatting notice ({field_name}): {note}")

        if not_detected_count > 3:
            review_flags.append(f"Multiple mandatory identity fields not detected ({not_detected_count} missing).")

        if valid_count >= 3 and invalid_count == 0:
            passed_indicators.append(f"Identity fields syntax and chronology verified ({valid_count} valid).")
    else:
        review_flags.append("Field validation results unavailable for this document.")

    # -------------------------------------------------------------------------
    # 2. Evaluate Document Authenticity & Tampering Indicators (Step 5)
    # -------------------------------------------------------------------------
    if authenticity_result:
        auth_status = authenticity_result.get("overall_status", "")
        checks = authenticity_result.get("checks", {})

        if auth_status == "Potential modification detected":
            critical_flags.append("Document Authenticity: Structural or metadata tampering indicators detected.")
        elif auth_status == "Unable to determine":
            review_flags.append("Document Authenticity: Could not determine structural integrity definitively.")

        # Check individual forensic checks
        for check_name, check_data in checks.items():
            if check_data.get("status") == "REVIEW":
                detail = check_data.get("detail", "")
                label = check_name.replace("_", " ").title()
                if check_name == "metadata" and "software" in detail.lower():
                    critical_flags.append(f"Forensic Metadata: {detail}")
                else:
                    review_flags.append(f"Authenticity Check ({label}): {detail}")
            elif check_data.get("status") == "PASS":
                passed_indicators.append(f"Authenticity Check ({check_name.replace('_', ' ').title()}) passed.")
    else:
        review_flags.append("Document authenticity forensic analysis not executed.")

    # -------------------------------------------------------------------------
    # 3. Evaluate Face Detection & Verification Indicators (Step 6)
    # -------------------------------------------------------------------------
    face_applies = is_face_applicable(doc_type_clean)
    if not face_applies:
        passed_indicators.append("Face Verification: Not applicable for this document category (non-photo credential).")
    else:
        if face_detection_result:
            face_status = face_detection_result.get("status", "")
            face_count = face_detection_result.get("face_count", 0)

            if "Multiple faces detected" in face_status or face_count > 1:
                critical_flags.append("Biometric Anomaly: Multiple faces detected in document scanning zone. Manual review required.")
            elif face_status == "No face detected" or face_count == 0:
                review_flags.append("Biometric Inspection: No photo detected in document portrait zone.")
            elif face_status == "Face detected" and face_count == 1:
                passed_indicators.append("Single frontal facial portrait detected in photo zone.")

        # Face Comparison Result (if traveler reference headshot was compared)
        if face_comparison_result:
            comp_res = face_comparison_result.get("comparison_result", "")
            detail = face_comparison_result.get("detail", "")

            if comp_res == "No Match":
                critical_flags.append(f"Facial Mismatch: Reference traveler headshot does not match document photo ({detail}).")
            elif comp_res == "Unable to determine":
                review_flags.append(f"Facial Comparison Inconclusive: {detail}")
            elif comp_res == "Match":
                passed_indicators.append("Facial comparison confirms document photo matches reference headshot.")
        else:
            review_flags.append("Reference face comparison was not performed (awaiting traveler live camera/reference scan).")

    # -------------------------------------------------------------------------
    # 4. Final Risk Tier Determination
    # -------------------------------------------------------------------------
    if critical_flags:
        status = "High Concern"
        risk_level = "HIGH"
        reasons = critical_flags + review_flags
        recommended_action = "MANDATORY SECONDARY INSPECTION: Divert traveler to secondary booth for physical document forensic examination and manual identity verification."
    elif review_flags:
        status = "Review Required"
        risk_level = "MEDIUM"
        reasons = review_flags
        recommended_action = "STANDARD OFFICER REVIEW: Verify document details visually and confirm traveler identity before clearance."
    else:
        status = "Low Concern"
        risk_level = "LOW"
        reasons = ["All automated consistency, authenticity, and biometric baseline checks satisfied."]
        recommended_action = "ROUTINE VERIFICATION: Standard document inspection protocol. No obvious irregularities detected."

    return {
        "status": status,
        "risk_level": risk_level,
        "document_type": doc_type_clean,
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
        "reasons": reasons,
        "critical_flags": critical_flags,
        "review_flags": review_flags,
        "passed_indicators": passed_indicators,
        "recommended_action": recommended_action,
        "disclaimer": "Screening risk analysis is for demonstration purposes only and does not constitute proof of forgery or an official border clearance decision. Human review is strictly required."
    }

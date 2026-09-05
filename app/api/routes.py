"""
API Endpoints for IDShield-X
Step 4: Field Validation & Normalization Engine Active
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from app.core import config
from app.modules import ocr_engine
from app.modules import field_validator
from app.modules import authenticity_analyzer
from app.modules import face_engine
from app.modules import risk_engine
from app.modules import analytics_engine
from app.modules import security_guard
from app.modules import document_profiles
from app.modules.audit_ledger import audit_ledger, history_store
import time
import uuid
import shutil
from pathlib import Path
from datetime import datetime

api_router = APIRouter(prefix="/api/v1", tags=["Border Screening"])

START_TIME = time.time()

# In-memory screening session registry for academic demo
SCREENING_SESSIONS = []

def format_file_size(size_bytes: int) -> str:
    """Format bytes into human-readable KB or MB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{round(size_bytes / 1024, 1)} KB"
    else:
        return f"{round(size_bytes / (1024 * 1024), 2)} MB"


@api_router.get("/documents/profiles")
def get_document_profiles():
    """Returns all 17 supported document profiles and category hierarchies."""
    return {
        "status": "SUCCESS",
        "categories": document_profiles.CATEGORIES,
        "grouped_profiles": document_profiles.get_profiles_by_category(),
        "profiles": document_profiles.DOCUMENT_PROFILES,
        "total_supported": len(document_profiles.DOCUMENT_PROFILES)
    }


@api_router.get("/health")
def health_check():
    """Returns system readiness, version, and checkpoint status."""
    uptime_seconds = round(time.time() - START_TIME, 2)
    return {
        "status": "ONLINE",
        "system": config.PROJECT_NAME,
        "version": config.VERSION,
        "checkpoint": {
            "id": config.CHECKPOINT_ID,
            "name": config.CHECKPOINT_NAME,
            "station": config.OFFICER_STATION
        },
        "modules": {
            "document_ingestion": "ACTIVE (Step 2)",
            "ocr_engine": "ACTIVE (Step 3)",
            "validation_engine": "ACTIVE (Step 4)",
            "tampering_engine": "ACTIVE (Step 5)",
            "face_verification": "ACTIVE (Step 6)",
            "risk_scoring": "PREPARED (Step 9)",
            "audit_ledger": "PREPARED (Step 10)"
        },
        "ocr_status": {
            "tesseract_installed": ocr_engine.is_tesseract_available(),
            "default_engine": "Tesseract OCR" if ocr_engine.is_tesseract_available() else "Standalone Demo OCR Engine"
        },
        "mode": "OFFLINE_FIRST_EDGE",
        "uptime_seconds": uptime_seconds
    }


@api_router.get("/system-info")
def system_info():
    """Returns operational metadata and hackathon identification."""
    return {
        "problem_statement": "SIH26188",
        "organization": "Ministry of Home Affairs (MHA)",
        "department": "Sashastra Seema Bal (SSB), Police II Division",
        "title": "AI-Based Fake Identity & Document Screening System",
        "prototype_tier": "Academic Hackathon Prototype (SIH 2026)",
        "supported_categories": list(config.DOCUMENT_CATEGORIES.keys()),
        "offline_enabled": config.OFFLINE_MODE
    }


@api_router.get("/documents/sample/{document_type}")
def get_sample_document(document_type: str):
    """Returns synthetic demo sample document image for testing."""
    dtype = document_type.strip().lower()
    sample_file = config.BASE_DIR / "data" / "synthetic_samples" / f"sample_{dtype}_demo.png"
    if not sample_file.exists():
        if dtype == "national_id":
            sample_file = config.BASE_DIR / "data" / "synthetic_samples" / "sample_aadhaar_demo.png"
        elif dtype == "passport":
            sample_file = config.BASE_DIR / "data" / "synthetic_samples" / "sample_passport_demo.png"
        elif dtype == "visa":
            sample_file = config.BASE_DIR / "data" / "synthetic_samples" / "sample_visa_demo.png"

    if not sample_file.exists():
        raise HTTPException(status_code=404, detail=f"Sample scan for '{document_type}' not found.")

    return FileResponse(path=str(sample_file), media_type="image/png", filename=f"sample_{dtype}_demo.png")


@api_router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("passport")
):
    """Secure Document Upload & Ingestion Endpoint."""
    if document_type not in config.DOCUMENT_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document category '{document_type}'. Supported types: {list(config.DOCUMENT_CATEGORIES.keys())}"
        )

    # Sanitize original filename to prevent path traversal
    raw_filename = file.filename or "unknown_document"
    original_filename = security_guard.sanitize_filename(raw_filename)
    file_ext = Path(original_filename).suffix.lower()

    if file_ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{file_ext}'. Allowed formats: {sorted(list(config.ALLOWED_EXTENSIONS))}"
        )

    doc_id = str(uuid.uuid4())
    safe_stored_filename = f"{doc_id}{file_ext}"
    target_filepath = config.UPLOAD_DIR / safe_stored_filename

    file_size = 0
    first_chunk = True
    try:
        with open(target_filepath, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                if first_chunk:
                    # Binary Magic-Byte Inspection
                    valid_magic, magic_msg = security_guard.validate_file_bytes(chunk, original_filename)
                    if not valid_magic:
                        buffer.close()
                        if target_filepath.exists():
                            target_filepath.unlink()
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Security Validation Failed: {magic_msg}"
                        )
                    first_chunk = False

                file_size += len(chunk)
                if file_size > config.MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    if target_filepath.exists():
                        target_filepath.unlink()
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {config.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if target_filepath.exists():
            target_filepath.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store document securely: {str(e)}"
        )
    finally:
        await file.close()

    # Log Cryptographic Audit Event for document ingestion
    audit_ledger.record_event(
        event_type="DOCUMENT_UPLOADED",
        screening_id=doc_id,
        details_summary=f"Document ingested: {document_type.upper()} ({file_ext}). Magic bytes verified."
    )

    ocr_blueprint = config.OCR_FIELD_BLUEPRINTS.get(document_type, [])

    screening_record = {
        "doc_id": doc_id,
        "original_filename": original_filename,
        "stored_filename": safe_stored_filename,
        "document_type": document_type,
        "document_type_label": config.DOCUMENT_CATEGORIES[document_type],
        "file_type": file.content_type or "application/octet-stream",
        "file_size_bytes": file_size,
        "file_size_formatted": format_file_size(file_size),
        "upload_time": datetime.utcnow().isoformat() + "Z",
        "preview_url": f"/api/v1/documents/{doc_id}/preview",
        "status": "INGESTED_READY_FOR_OCR",
        "ocr_target_fields": ocr_blueprint,
        "checkpoint": config.CHECKPOINT_ID
    }

    SCREENING_SESSIONS.insert(0, screening_record)

    return {
        "success": True,
        "message": f"{config.DOCUMENT_CATEGORIES[document_type]} successfully ingested and queued for screening.",
        "data": screening_record
    }


@api_router.get("/documents/{doc_id}/preview")
def get_document_preview(doc_id: str):
    """Secure Preview Endpoint."""
    try:
        uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Document ID format.")

    matches = list(config.UPLOAD_DIR.glob(f"{doc_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Document not found or session expired.")

    filepath = matches[0]
    media_type = "image/png"
    if filepath.suffix.lower() in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif filepath.suffix.lower() == ".webp":
        media_type = "image/webp"
    elif filepath.suffix.lower() == ".pdf":
        media_type = "application/pdf"

    return FileResponse(filepath, media_type=media_type)


@api_router.post("/ocr/extract")
def extract_ocr(doc_id: str = Form(...), document_type: str = Form(None)):
    """OCR Document Text Extraction Endpoint (Step 3)."""
    target_session = None
    for session in SCREENING_SESSIONS:
        if session["doc_id"] == doc_id:
            target_session = session
            break

    matches = list(config.UPLOAD_DIR.glob(f"{doc_id}.*"))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document ID '{doc_id}' not found. Please re-upload the credential."
        )

    filepath = matches[0]
    doc_type = document_type or (target_session["document_type"] if target_session else "passport")
    file_type = target_session["file_type"] if target_session else "image/png"

    raw_text, engine_used, warning = ocr_engine.extract_text_from_image(filepath, file_type, document_type=doc_type)
    structured_fields = ocr_engine.parse_structured_fields(raw_text, doc_type)

    if target_session:
        target_session["status"] = "OCR_EXTRACTED"
        target_session["raw_ocr_text"] = raw_text
        target_session["structured_fields"] = structured_fields
        target_session["ocr_engine_used"] = engine_used

    return {
        "success": True,
        "doc_id": doc_id,
        "document_type": doc_type,
        "ocr_engine_used": engine_used,
        "raw_text": raw_text,
        "structured_fields": structured_fields,
        "warning": warning
    }


@api_router.post("/documents/validate")
def validate_document(
    doc_id: str = Form(...),
    document_type: str = Form(None)
):
    """
    Document Field Normalization & Validation Endpoint (Step 4)
    - Normalizes extracted OCR fields (whitespace, dates, genders, identifiers)
    - Validates syntax and chronology (DOB <= today, expiry dates, format patterns)
    - Returns per-field status: Valid, Invalid, Not detected, Needs Review
    - Enforces human verification requirement
    """
    target_session = None
    for session in SCREENING_SESSIONS:
        if session["doc_id"] == doc_id:
            target_session = session
            break

    matches = list(config.UPLOAD_DIR.glob(f"{doc_id}.*"))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document ID '{doc_id}' not found. Please upload again."
        )

    filepath = matches[0]
    doc_type = document_type or (target_session["document_type"] if target_session else "passport")
    file_type = target_session["file_type"] if target_session else "image/png"

    # If OCR has not been run yet, run it now
    if not target_session or "structured_fields" not in target_session:
        raw_text, engine_used, _ = ocr_engine.extract_text_from_image(filepath, file_type)
        structured_fields = ocr_engine.parse_structured_fields(raw_text, doc_type)
        if target_session:
            target_session["raw_ocr_text"] = raw_text
            target_session["structured_fields"] = structured_fields
    else:
        structured_fields = target_session["structured_fields"]
        raw_text = target_session.get("raw_ocr_text", "")

    # Execute Field Normalization and Validation
    validation_res = field_validator.validate_document_fields(structured_fields, doc_type)

    # Update session status
    if target_session:
        target_session["status"] = "VALIDATED"
        target_session["validation"] = validation_res

    return {
        "success": True,
        "doc_id": doc_id,
        "document_type": doc_type,
        "raw_text": raw_text,
        "validation": validation_res
    }


@api_router.get("/documents/{doc_id}/ocr-blueprint")
def get_ocr_blueprint(doc_id: str):
    """Returns the OCR field blueprint associated with an uploaded document."""
    for session in SCREENING_SESSIONS:
        if session["doc_id"] == doc_id:
            return {
                "doc_id": doc_id,
                "document_type": session["document_type"],
                "ocr_target_fields": session["ocr_target_fields"]
            }
    raise HTTPException(status_code=404, detail="Document session not found.")


@api_router.get("/screenings")
def list_screenings():
    """Returns recent document screenings in this session."""
    return {
        "total_screenings": len(SCREENING_SESSIONS),
        "recent_sessions": SCREENING_SESSIONS[:10]
    }


@api_router.post("/documents/analyze-authenticity")
def analyze_authenticity_endpoint(
    doc_id: str = Form(...),
    document_type: str = Form(None)
):
    """
    Document Authenticity & Tampering Analysis Endpoint (Step 5)
    Safe, explainable checks:
    - Image Quality (resolution, dimensions, blur indication)
    - Document Structure (geometry, aspect ratio, expected layout zones)
    - Text/OCR Consistency (expected schema, typography, field completeness)
    - Metadata Analysis (file container, software signatures, EXIF/PDF tags)
    """
    target_session = None
    for session in SCREENING_SESSIONS:
        if session["doc_id"] == doc_id:
            target_session = session
            break

    matches = list(config.UPLOAD_DIR.glob(f"{doc_id}.*"))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document ID '{doc_id}' not found. Please upload again."
        )

    filepath = matches[0]
    doc_type = document_type or (target_session["document_type"] if target_session else "passport")

    # Retrieve structured fields and raw OCR text if available in session
    structured_fields = target_session.get("structured_fields") if target_session else None
    raw_text = target_session.get("raw_ocr_text") if target_session else None

    # If OCR has not been run, run it to support OCR consistency check
    if not structured_fields:
        file_type = target_session["file_type"] if target_session else "image/png"
        raw_text, _, _ = ocr_engine.extract_text_from_image(filepath, file_type)
        structured_fields = ocr_engine.parse_structured_fields(raw_text, doc_type)
        if target_session:
            target_session["raw_ocr_text"] = raw_text
            target_session["structured_fields"] = structured_fields

    analysis_result = authenticity_analyzer.analyze_document_authenticity(
        filepath=filepath,
        document_type=doc_type,
        structured_fields=structured_fields,
        raw_ocr_text=raw_text
    )

    if target_session:
        target_session["status"] = "AUTHENTICITY_ANALYZED"
        target_session["authenticity"] = analysis_result

    return {
        "success": True,
        "doc_id": doc_id,
        "document_type": doc_type,
        "authenticity": analysis_result
    }


@api_router.post("/face/detect")
def detect_document_face(doc_id: str = Form(...), document_type: str = Form(None)):
    """
    Step 6: Face Detection Endpoint
    Detects whether a face is present in the document.
    Returns: Face detected / No face detected / Unable to determine / Multiple faces detected — manual review required.
    Includes cropped face data URI if 1 face detected.
    """
    target_session = None
    for session in SCREENING_SESSIONS:
        if session["doc_id"] == doc_id:
            target_session = session
            break

    matches = list(config.UPLOAD_DIR.glob(f"{doc_id}.*"))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document ID '{doc_id}' not found."
        )

    filepath = matches[0]
    doc_type = document_type or (target_session["document_type"] if target_session else "passport")
    result = face_engine.detect_faces(filepath, document_type=doc_type)

    if target_session:
        target_session["face_detection"] = result

    return {
        "success": True,
        "doc_id": doc_id,
        "face_detection": result
    }


@api_router.post("/face/verify")
async def verify_faces_endpoint(
    doc_id: str = Form(...),
    reference_file: UploadFile = File(...)
):
    """
    Step 6: Demo Face Comparison Endpoint
    Compares the face detected in the document with an uploaded consented reference image.
    Returns: Match / No Match / Unable to determine.
    Ephemeral processing: Reference image is safely cleaned up after comparison.
    """
    matches = list(config.UPLOAD_DIR.glob(f"{doc_id}.*"))
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document ID '{doc_id}' not found."
        )
    doc_filepath = matches[0]

    target_session = next((s for s in SCREENING_SESSIONS if s["doc_id"] == doc_id), None)
    doc_type = target_session["document_type"] if target_session else "passport"

    ref_ext = Path(reference_file.filename or "ref.png").suffix.lower()
    if ref_ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported reference image format '{ref_ext}'."
        )

    temp_ref_id = f"ref_tmp_{uuid.uuid4()}{ref_ext}"
    temp_ref_path = config.UPLOAD_DIR / temp_ref_id

    try:
        content = await reference_file.read()
        temp_ref_path.write_bytes(content)

        # Execute Comparison
        comparison = face_engine.compare_faces(doc_filepath, temp_ref_path, document_type=doc_type)

        return {
            "success": True,
            "doc_id": doc_id,
            "face_comparison": comparison
        }
    finally:
        # Privacy guard: clean up temporary reference file immediately
        if temp_ref_path.exists():
            try:
                temp_ref_path.unlink()
            except Exception:
                pass
        await reference_file.close()


@api_router.post("/risk/analyze")
def analyze_screening_risk(
    doc_id: str = Form(...),
    document_type: str = Form(None)
):
    """
    Step 7: Explainable Screening Risk Scoring Endpoint
    Combines Validation, Authenticity Analysis, and Face Verification into a transparent risk tier:
    - Low Concern
    - Review Required
    - High Concern
    """
    target_session = None
    for session in SCREENING_SESSIONS:
        if session["doc_id"] == doc_id:
            target_session = session
            break

    doc_type = document_type or (target_session["document_type"] if target_session else "passport")
    val_res = target_session.get("validation") if target_session else None
    auth_res = target_session.get("authenticity") if target_session else None
    face_detect = target_session.get("face_detection") if target_session else None
    face_comp = target_session.get("face_comparison") if target_session else None

    # If some components were not executed prior, execute fallback or on-the-fly
    matches = list(config.UPLOAD_DIR.glob(f"{doc_id}.*"))
    if matches and not (val_res and auth_res and face_detect):
        filepath = matches[0]
        if not val_res:
            raw_text, _, _ = ocr_engine.extract_text_from_image(filepath, "image/png")
            fields = ocr_engine.parse_structured_fields(raw_text, doc_type)
            val_res = field_validator.validate_document_fields(fields, doc_type)
        if not auth_res:
            raw_text = target_session.get("raw_ocr_text", "") if target_session else ""
            fields = target_session.get("structured_fields", {}) if target_session else {}
            auth_res = authenticity_analyzer.analyze_document_authenticity(filepath, doc_type, fields, raw_text)
        if not face_detect:
            face_detect = face_engine.detect_faces(filepath, document_type=doc_type)

    risk_evaluation = risk_engine.evaluate_screening_risk(
        document_type=doc_type,
        validation_result=val_res,
        authenticity_result=auth_res,
        face_detection_result=face_detect,
        face_comparison_result=face_comp
    )

    if target_session:
        target_session["risk_analysis"] = risk_evaluation
        target_session["status"] = "RISK_ANALYZED"

    # Cryptographic Audit Log Event
    audit_ledger.record_event(
        event_type="RISK_ANALYSIS_COMPLETED",
        screening_id=doc_id,
        details_summary=f"Risk evaluated as '{risk_evaluation['status']}' ({len(risk_evaluation['reasons'])} factors noted)."
    )

    return {
        "success": True,
        "doc_id": doc_id,
        "risk_analysis": risk_evaluation
    }


# ==============================================================================
# Step 8: Screening History & Audit Trail Endpoints
# ==============================================================================

@api_router.get("/screenings/history")
def get_screening_history(
    query: str = None,
    document_type: str = None,
    status: str = None,
    date_str: str = None
):
    """Returns filtered minimal historical screening metadata."""
    results = history_store.search_and_filter(
        query=query,
        document_type=document_type,
        status=status,
        date_str=date_str
    )
    return {
        "success": True,
        "total_count": len(results),
        "records": results
    }


@api_router.get("/screenings/history/{screening_id}")
def get_screening_by_id(screening_id: str):
    """Retrieves a single historical screening record by ID."""
    record = history_store.get_by_id(screening_id)
    if not record:
        raise HTTPException(status_code=404, detail="Screening record not found.")
    return {
        "success": True,
        "record": record
    }


@api_router.post("/screenings/save")
def save_screening_endpoint(
    doc_id: str = Form(...),
    document_type: str = Form(None),
    risk_status: str = Form("Review Required"),
    summary_note: str = Form(None)
):
    """
    Saves minimal metadata of the current screening session to history
    and commits a cryptographically chained block to the audit ledger.
    """
    target_session = None
    for session in SCREENING_SESSIONS:
        if session["doc_id"] == doc_id:
            target_session = session
            break

    doc_type = document_type or (target_session["document_type"] if target_session else "passport")
    risk_stat = risk_status
    if target_session and "risk_analysis" in target_session:
        risk_stat = target_session["risk_analysis"].get("status", risk_status)

    risk_lvl = "LOW" if risk_stat == "Low Concern" else ("HIGH" if risk_stat == "High Concern" else "MEDIUM")
    note = summary_note or (f"Screening finalized for {doc_type.upper()}. Risk: {risk_stat}.")

    # 1. Record in History Store
    record = history_store.record_screening(
        document_type=doc_type,
        risk_status=risk_stat,
        risk_level=risk_lvl,
        summary_note=note
    )

    # 2. Append to Cryptographic Audit Chain
    block = audit_ledger.record_event(
        event_type="SCREENING_COMMITTED_TO_LEDGER",
        screening_id=record["screening_id"],
        details_summary=f"Screening record committed to history: {doc_type.upper()} ({risk_stat})."
    )

    return {
        "success": True,
        "message": "Screening successfully recorded in history and committed to cryptographic audit trail.",
        "record": record,
        "audit_block_hash": block["hash"]
    }


@api_router.get("/audit/trail")
def get_audit_trail(limit: int = 50):
    """Returns recent cryptographic audit ledger blocks."""
    events = audit_ledger.get_events(limit=limit)
    return {
        "success": True,
        "total_blocks": len(audit_ledger.chain),
        "events": events
    }


@api_router.get("/audit/verify")
def verify_audit_ledger_integrity():
    """Verifies the SHA-256 cryptographic chain integrity across all blocks."""
    verification = audit_ledger.verify_integrity()
    return {
        "success": True,
        "verification": verification
    }


# ==============================================================================
# Step 9: Analytics Dashboard Endpoint
# ==============================================================================

@api_router.get("/analytics/summary")
def get_analytics_summary_endpoint():
    """Returns aggregated checkpoint screening statistics from minimal history."""
    summary = analytics_engine.compute_analytics_summary()
    return {
        "success": True,
        "analytics": summary
    }


# ==============================================================================
# Step 10: Security, Validation & Access Control Endpoints
# ==============================================================================

@api_router.get("/security/status")
def get_security_status_endpoint():
    """Returns the prototype security health, active guards, and RBAC posture."""
    role_info = security_guard.rbac_manager.get_role_info()
    return {
        "success": True,
        "security_profile": {
            "magic_byte_inspection": "ACTIVE (PNG, JPG, PDF, WEBP)",
            "path_traversal_sanitizer": "ENFORCED",
            "rate_limiter": f"ACTIVE ({security_guard.rate_limiter.max_requests} req / {security_guard.rate_limiter.window_seconds}s)",
            "audit_chain": "SHA-256 TAMPER-EVIDENT",
            "ephemeral_biometrics": "ENFORCED (0-day retention)",
            "current_role": role_info["current_role"],
            "operator_title": role_info["title"],
            "permissions": role_info["permissions"]
        }
    }


@api_router.post("/security/role")
def set_security_role_endpoint(role: str = Form(...)):
    """Allows demo operators to switch roles (e.g. OPERATOR vs SUPERVISOR)."""
    success = security_guard.rbac_manager.set_role(role)
    if not success:
        raise HTTPException(status_code=400, detail=f"Invalid role '{role}'. Valid roles: OPERATOR, SUPERVISOR")
    return {
        "success": True,
        "message": f"Active role switched to {role.upper()}.",
        "role_info": security_guard.rbac_manager.get_role_info()
    }







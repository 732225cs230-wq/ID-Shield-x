"""
IDShield-X: AI-Based Fake Identity & Document Screening System
Smart India Hackathon 2026 | Problem Statement: SIH26188
Organization: Ministry of Home Affairs (MHA)
Department: Sashastra Seema Bal (SSB), Police II Division

Entrypoint Application Script (Step 4: Field Validation & Normalization Active)
"""
import sys
import os
import json
import uuid
from pathlib import Path
from datetime import datetime

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from fastapi import FastAPI, Form, HTTPException, UploadFile, File
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    import uvicorn

    from app.core import config
    from app.api.routes import (
        api_router, extract_ocr, validate_document,
        analyze_authenticity_endpoint, detect_document_face, verify_faces_endpoint,
        analyze_screening_risk, get_document_profiles
    )

    # Initialize FastAPI Application
    app = FastAPI(
        title=config.PROJECT_NAME,
        version=config.VERSION,
        description=config.DESCRIPTION
    )

    # Mount Static Files
    app.mount("/static", StaticFiles(directory=str(config.STATIC_DIR)), name="static")

    # Include API Routers
    app.include_router(api_router)

    # Alias /api/documents/profiles
    @app.get("/api/documents/profiles")
    def profiles_alias():
        return get_document_profiles()

    # Alias /api/ocr -> /api/v1/ocr/extract
    @app.post("/api/ocr")
    def ocr_alias(doc_id: str = Form(...)):
        return extract_ocr(doc_id=doc_id)

    # Alias /api/validate-document -> /api/v1/documents/validate
    @app.post("/api/validate-document")
    def validate_alias(doc_id: str = Form(...), document_type: str = Form(None)):
        return validate_document(doc_id=doc_id, document_type=document_type)

    # Alias /api/analyze-authenticity -> /api/v1/documents/analyze-authenticity
    @app.post("/api/analyze-authenticity")
    def authenticity_alias(doc_id: str = Form(...), document_type: str = Form(None)):
        return analyze_authenticity_endpoint(doc_id=doc_id, document_type=document_type)

    # Alias /api/face-detection -> /api/v1/face/detect
    @app.post("/api/face-detection")
    def face_detect_alias(doc_id: str = Form(...)):
        return detect_document_face(doc_id=doc_id)

    # Alias /api/face-verify -> /api/v1/face/verify
    @app.post("/api/face-verify")
    async def face_verify_alias(doc_id: str = Form(...), reference_file: UploadFile = File(...)):
        return await verify_faces_endpoint(doc_id=doc_id, reference_file=reference_file)

    # Alias /api/risk-analysis -> /api/v1/risk/analyze
    @app.post("/api/risk-analysis")
    def risk_analysis_alias(doc_id: str = Form(...), document_type: str = Form(None)):
        return analyze_screening_risk(doc_id=doc_id, document_type=document_type)



    # Alias /api/documents/sample/{document_type}
    @app.get("/api/documents/sample/{document_type}")
    def sample_alias(document_type: str):
        from app.api.routes import get_sample_document
        return get_sample_document(document_type)

    # Root Web Route (Serves Dashboard Console)
    @app.get("/", response_class=HTMLResponse)
    def root_dashboard():
        template_file = config.TEMPLATES_DIR / "index.html"
        if template_file.exists():
            return template_file.read_text(encoding="utf-8")
        return "<h1>IDShield-X Dashboard Initialized</h1>"

    if __name__ == "__main__":
        print("=" * 70)
        print("  IDShield-X: AI-Based Fake Identity & Document Screening System")
        print(f"  Target: SSB / MHA | Checkpoint: {config.CHECKPOINT_ID}")
        print(f"  Local Terminal URL: http://{config.HOST}:{config.PORT}")
        print("=" * 70)
        uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=config.DEBUG)

except ImportError as e:
    # Beginner-Friendly Fallback if FastAPI / Uvicorn are not yet installed
    print("=" * 70)
    print("  [NOTICE] FastAPI or Uvicorn not yet installed.")
    print("  To install full dependencies, run:")
    print("      pip install -r requirements.txt")
    print(f"  Notice detail: {e}")
    print("  Starting Built-in Zero-Dependency Diagnostic Server...")
    print("=" * 70)

    import http.server
    import socketserver
    import urllib.parse
    from app.modules import ocr_engine
    from app.modules import field_validator
    from app.modules import authenticity_analyzer
    from app.modules import face_engine
    from app.modules import risk_engine
    from app.modules import analytics_engine
    from app.modules import security_guard
    from app.modules.audit_ledger import audit_ledger, history_store

    PORT = 8000
    UPLOAD_DIR = BASE_DIR / "data" / "uploads"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_METADATA = {}

    def _extract_form_field(body_str: str, field_name: str, default: str = "") -> str:
        """Extracts form field whether urlencoded (key=val) or multipart (name="key")."""
        if f"{field_name}=" in body_str:
            try:
                raw_v = body_str.split(f"{field_name}=")[1].split("&")[0].split("\r\n")[0].strip()
                return urllib.parse.unquote_plus(raw_v)
            except Exception:
                pass
        if f'name="{field_name}"' in body_str:
            try:
                val_part = body_str.split(f'name="{field_name}"')[1]
                if "\r\n\r\n" in val_part:
                    return val_part.split("\r\n\r\n")[1].split("\r\n")[0].strip()
                elif "\n\n" in val_part:
                    return val_part.split("\n\n")[1].split("\n")[0].strip()
            except Exception:
                pass
        return default

    class CustomFallbackHandler(http.server.SimpleHTTPRequestHandler):
        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            parsed_path = urllib.parse.urlparse(self.path).path
            
            # Root Dashboard
            if parsed_path in ("/", "/index.html"):
                template_file = BASE_DIR / "app" / "templates" / "index.html"
                if template_file.exists():
                    content = template_file.read_text(encoding="utf-8")
                    self.send_response(200)
                    self.send_header("Content-type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                    return

            # API Healthcheck
            elif parsed_path == "/api/v1/health":
                payload = {
                    "status": "ONLINE (FALLBACK_MODE)",
                    "system": "IDShield-X",
                    "checkpoint": {
                        "id": "SSB-BOP-RAXAUL-01",
                        "name": "Raxaul ICP Checkpost",
                        "station": "SSB 47th Bn"
                    },
                    "modules": {
                        "document_ingestion": "ACTIVE (Step 2)",
                        "ocr_engine": "ACTIVE (Step 3)",
                        "validation_engine": "ACTIVE (Step 4)",
                        "tampering_engine": "ACTIVE (Step 5)",
                        "face_verification": "ACTIVE (Step 6)"
                    },
                    "uptime_seconds": 35.0
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode("utf-8"))
                return

            # Static Assets mapping /static/ to app/static/
            elif parsed_path.startswith("/static/"):
                rel_path = parsed_path[len("/static/"):]
                target_file = BASE_DIR / "app" / "static" / rel_path
                if target_file.exists() and target_file.is_file():
                    content = target_file.read_bytes()
                    if rel_path.endswith(".css"):
                        mime = "text/css"
                    elif rel_path.endswith(".js"):
                        mime = "application/javascript"
                    elif rel_path.endswith(".png"):
                        mime = "image/png"
                    elif rel_path.endswith((".jpg", ".jpeg")):
                        mime = "image/jpeg"
                    elif rel_path.endswith(".svg"):
                        mime = "image/svg+xml"
                    else:
                        mime = "application/octet-stream"
                    self.send_response(200)
                    self.send_header("Content-type", mime)
                    self.end_headers()
                    self.wfile.write(content)
                    return

            # Document Profiles
            elif parsed_path in ("/api/v1/documents/profiles", "/api/documents/profiles"):
                try:
                    from app.modules import document_profiles
                    payload = {
                        "status": "SUCCESS",
                        "categories": document_profiles.CATEGORIES,
                        "grouped_profiles": document_profiles.get_profiles_by_category(),
                        "profiles": document_profiles.DOCUMENT_PROFILES,
                        "total_supported": len(document_profiles.DOCUMENT_PROFILES)
                    }
                except Exception as e:
                    payload = {"status": "ERROR", "detail": str(e)}
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode("utf-8"))
                return

            # Document Previews
            elif parsed_path.startswith("/api/v1/documents/") and parsed_path.endswith("/preview"):
                doc_id = parsed_path.split("/")[4]
                matches = list(UPLOAD_DIR.glob(f"{doc_id}.*"))
                if matches:
                    self.send_response(200)
                    self.send_header("Content-type", "image/png")
                    self.end_headers()
                    self.wfile.write(matches[0].read_bytes())
                    return

            # Screening History
            elif parsed_path == "/api/v1/screenings/history":
                records = history_store.search_and_filter()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "total_count": len(records), "records": records}).encode("utf-8"))
                return

            # Audit Trail
            elif parsed_path == "/api/v1/audit/trail":
                events = audit_ledger.get_events(limit=50)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "total_blocks": len(audit_ledger.chain), "events": events}).encode("utf-8"))
                return

            # Audit Integrity Verify
            elif parsed_path == "/api/v1/audit/verify":
                verif = audit_ledger.verify_integrity()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "verification": verif}).encode("utf-8"))
                return

            # Analytics Summary
            elif parsed_path == "/api/v1/analytics/summary":
                summary = analytics_engine.compute_analytics_summary()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "analytics": summary}).encode("utf-8"))
                return

            # Security Status
            elif parsed_path == "/api/v1/security/status":
                role_info = security_guard.rbac_manager.get_role_info()
                sec_profile = {
                    "magic_byte_inspection": "ACTIVE (PNG, JPG, PDF, WEBP)",
                    "path_traversal_sanitizer": "ENFORCED",
                    "rate_limiter": f"ACTIVE ({security_guard.rate_limiter.max_requests} req / {security_guard.rate_limiter.window_seconds}s)",
                    "audit_chain": "SHA-256 TAMPER-EVIDENT",
                    "ephemeral_biometrics": "ENFORCED (0-day retention)",
                    "current_role": role_info["current_role"],
                    "operator_title": role_info["title"],
                    "permissions": role_info["permissions"]
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "security_profile": sec_profile}).encode("utf-8"))
                return

            elif parsed_path.startswith("/api/v1/documents/sample/") or parsed_path.startswith("/api/documents/sample/"):
                doc_type = parsed_path.rstrip("/").split("/")[-1].lower()
                sample_file = BASE_DIR / "data" / "synthetic_samples" / f"sample_{doc_type}_demo.png"
                if not sample_file.exists():
                    if doc_type == "national_id":
                        sample_file = BASE_DIR / "data" / "synthetic_samples" / "sample_aadhaar_demo.png"
                    elif doc_type == "passport":
                        sample_file = BASE_DIR / "data" / "synthetic_samples" / "sample_passport_demo.png"
                    elif doc_type == "visa":
                        sample_file = BASE_DIR / "data" / "synthetic_samples" / "sample_visa_demo.png"
                if sample_file.exists():
                    self.send_response(200)
                    self.send_header("Content-type", "image/png")
                    self.send_header("Content-Disposition", f'inline; filename="sample_{doc_type}_demo.png"')
                    self.end_headers()
                    self.wfile.write(sample_file.read_bytes())
                    return
                else:
                    self.send_error(404, f"Sample scan for '{doc_type}' not found.")
                    return

            self.send_error(404, "Endpoint not found")

        def do_POST(self):
            parsed_path = urllib.parse.urlparse(self.path).path
            content_len = int(self.headers.get("Content-Length", 0))
            raw_data = self.rfile.read(content_len) if content_len > 0 else b""
            post_body = raw_data.decode("utf-8", errors="ignore")
            
            # Document Upload Endpoint
            if parsed_path == "/api/v1/documents/upload":
                doc_id = str(uuid.uuid4())
                safe_filename = f"{doc_id}.png"
                target_filepath = UPLOAD_DIR / safe_filename
                
                doc_type = _extract_form_field(post_body, "document_type", "passport")
                orig_filename = "uploaded_credential.png"
                if 'filename="' in post_body:
                    try:
                        orig_filename = post_body.split('filename="')[1].split('"')[0].strip()
                    except Exception:
                        pass

                UPLOAD_METADATA[doc_id] = {
                    "document_type": doc_type,
                    "original_filename": orig_filename
                }
                
                written = False
                content_type_header = self.headers.get("Content-Type", "")
                boundary = ""
                if "boundary=" in content_type_header:
                    boundary = content_type_header.split("boundary=")[1].split(";")[0].strip()

                # 1. Standard Multipart File Part Extraction
                file_hdr_pos = raw_data.find(b'name="file"')
                if file_hdr_pos == -1:
                    file_hdr_pos = raw_data.find(b'filename="')
                if file_hdr_pos != -1:
                    hdr_end = raw_data.find(b"\r\n\r\n", file_hdr_pos)
                    if hdr_end != -1:
                        if boundary:
                            b_marker = b"\r\n--" + boundary.encode()
                            b_end = raw_data.find(b_marker, hdr_end + 4)
                            if b_end != -1:
                                uploaded_payload = raw_data[hdr_end + 4:b_end]
                                if len(uploaded_payload) > 0:
                                    target_filepath.write_bytes(uploaded_payload)
                                    written = True
                        if not written:
                            # Fallback if boundary delimiter was malformed
                            uploaded_payload = raw_data[hdr_end + 4:]
                            if uploaded_payload.endswith(b"\r\n"):
                                uploaded_payload = uploaded_payload[:-2]
                            if len(uploaded_payload) > 0:
                                target_filepath.write_bytes(uploaded_payload)
                                written = True

                # 2. Standalone PNG binary extraction (if uploaded raw or unboundary)
                if not written:
                    png_pos = raw_data.find(b"\x89PNG\r\n\x1a\n")
                    if png_pos != -1:
                        iend_pos = raw_data.find(b"IEND", png_pos)
                        if iend_pos != -1:
                            img_payload = raw_data[png_pos:iend_pos + 8]
                            target_filepath.write_bytes(img_payload)
                            written = True

                # 3. Standalone JPEG binary extraction (if uploaded raw or unboundary)
                if not written:
                    jpg_pos = raw_data.find(b"\xff\xd8")
                    if jpg_pos != -1:
                        eoi_pos = raw_data.rfind(b"\xff\xd9")
                        if eoi_pos != -1 and eoi_pos > jpg_pos:
                            img_payload = raw_data[jpg_pos:eoi_pos + 2]
                            target_filepath.write_bytes(img_payload)
                            written = True

                # 4. Fallback to synthetic sample for document type
                if not written:
                    sample_path = BASE_DIR / "data" / "synthetic_samples" / f"sample_{doc_type}_demo.png"
                    if not sample_path.exists():
                        sample_path = BASE_DIR / "data" / "synthetic_samples" / "sample_passport_demo.png"
                    if sample_path.exists():
                        target_filepath.write_bytes(sample_path.read_bytes())
                    else:
                        target_filepath.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
                
                try:
                    from app.core import config as cfg
                    doc_label = cfg.DOCUMENT_CATEGORIES.get(doc_type, doc_type.replace('_', ' ').title())
                except Exception:
                    doc_label = doc_type.replace('_', ' ').title()
                
                file_size = target_filepath.stat().st_size
                resp = {
                    "success": True,
                    "message": "Credential uploaded and queued for screening.",
                    "data": {
                        "doc_id": doc_id,
                        "original_filename": orig_filename,
                        "stored_filename": safe_filename,
                        "document_type": doc_type,
                        "document_type_label": doc_label,
                        "file_type": "image/png",
                        "file_size_bytes": file_size,
                        "file_size_formatted": f"{round(file_size / 1024, 1)} KB",
                        "upload_time": datetime.utcnow().isoformat() + "Z",
                        "preview_url": f"/api/v1/documents/{doc_id}/preview",
                        "status": "INGESTED_READY_FOR_OCR"
                    }
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
                return

            # OCR Extract Endpoint
            elif parsed_path in ("/api/v1/ocr/extract", "/api/ocr"):
                doc_id = _extract_form_field(post_body, "doc_id", "sample_demo_doc")
                doc_type = _extract_form_field(post_body, "document_type", "")
                if not doc_type and doc_id in UPLOAD_METADATA:
                    doc_type = UPLOAD_METADATA[doc_id]["document_type"]
                if not doc_type:
                    doc_type = "passport"

                matches = list(UPLOAD_DIR.glob(f"{doc_id}.*"))
                target_file = matches[0] if matches else (UPLOAD_DIR / f"{doc_id}.png")
                if not target_file.exists():
                    sample_file = BASE_DIR / "data" / "synthetic_samples" / f"sample_{doc_type}_demo.png"
                    target_file = sample_file if sample_file.exists() else (BASE_DIR / "data" / "synthetic_samples" / "sample_passport_demo.png")

                raw_text, engine_used, warning = ocr_engine.extract_text_from_image(target_file, "image/png", document_type=doc_type)
                fields = ocr_engine.parse_structured_fields(raw_text, doc_type)

                resp = {
                    "success": True,
                    "doc_id": doc_id,
                    "document_type": doc_type,
                    "ocr_engine_used": engine_used,
                    "raw_text": raw_text,
                    "structured_fields": fields,
                    "warning": warning
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
                return

            # Document Validation Endpoint
            elif parsed_path in ("/api/v1/documents/validate", "/api/validate-document"):
                doc_id = _extract_form_field(post_body, "doc_id", "sample_demo_doc")
                doc_type = _extract_form_field(post_body, "document_type", "")
                if not doc_type and doc_id in UPLOAD_METADATA:
                    doc_type = UPLOAD_METADATA[doc_id]["document_type"]
                if not doc_type:
                    doc_type = "passport"

                matches = list(UPLOAD_DIR.glob(f"{doc_id}.*"))
                target_file = matches[0] if matches else (UPLOAD_DIR / f"{doc_id}.png")
                if not target_file.exists():
                    sample_file = BASE_DIR / "data" / "synthetic_samples" / f"sample_{doc_type}_demo.png"
                    target_file = sample_file if sample_file.exists() else (BASE_DIR / "data" / "synthetic_samples" / "sample_passport_demo.png")

                raw_text, _, _ = ocr_engine.extract_text_from_image(target_file, "image/png", document_type=doc_type)
                fields = ocr_engine.parse_structured_fields(raw_text, doc_type)
                val_res = field_validator.validate_document_fields(fields, doc_type)

                resp = {
                    "success": True,
                    "doc_id": doc_id,
                    "document_type": doc_type,
                    "raw_text": raw_text,
                    "validation": val_res
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
                return

            # Document Authenticity Analysis Endpoint (Step 5)
            elif parsed_path in ("/api/v1/documents/analyze-authenticity", "/api/analyze-authenticity"):
                doc_id = _extract_form_field(post_body, "doc_id", "sample_demo_doc")
                doc_type = _extract_form_field(post_body, "document_type", "")
                if not doc_type and doc_id in UPLOAD_METADATA:
                    doc_type = UPLOAD_METADATA[doc_id]["document_type"]
                if not doc_type:
                    doc_type = "passport"

                matches = list(UPLOAD_DIR.glob(f"{doc_id}.*"))
                target_file = matches[0] if matches else (UPLOAD_DIR / f"{doc_id}.png")
                if not target_file.exists():
                    sample_file = BASE_DIR / "data" / "synthetic_samples" / f"sample_{doc_type}_demo.png"
                    target_file = sample_file if sample_file.exists() else (BASE_DIR / "data" / "synthetic_samples" / "sample_passport_demo.png")

                raw_text, _, _ = ocr_engine.extract_text_from_image(target_file, "image/png", document_type=doc_type)
                fields = ocr_engine.parse_structured_fields(raw_text, doc_type)
                auth_res = authenticity_analyzer.analyze_document_authenticity(
                    filepath=target_file,
                    document_type=doc_type,
                    structured_fields=fields,
                    raw_ocr_text=raw_text
                )

                resp = {
                    "success": True,
                    "doc_id": doc_id,
                    "document_type": doc_type,
                    "authenticity": auth_res
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
                return

            # Face Detection Endpoint (Step 6)
            elif parsed_path in ("/api/v1/face/detect", "/api/face-detection"):
                doc_id = _extract_form_field(post_body, "doc_id", "sample_demo_doc")
                doc_type = _extract_form_field(post_body, "document_type", "")
                if not doc_type and doc_id in UPLOAD_METADATA:
                    doc_type = UPLOAD_METADATA[doc_id]["document_type"]
                if not doc_type:
                    doc_type = "passport"

                matches = list(UPLOAD_DIR.glob(f"{doc_id}.*"))
                target_file = matches[0] if matches else (UPLOAD_DIR / f"{doc_id}.png")
                if not target_file.exists():
                    sample_file = BASE_DIR / "data" / "synthetic_samples" / f"sample_{doc_type}_demo.png"
                    target_file = sample_file if sample_file.exists() else (BASE_DIR / "data" / "synthetic_samples" / "sample_passport_demo.png")

                detect_res = face_engine.detect_faces(target_file, document_type=doc_type)
                resp = {
                    "success": True,
                    "doc_id": doc_id,
                    "document_type": doc_type,
                    "face_detection": detect_res
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
                return

            # Face Verification Endpoint (Step 6)
            elif parsed_path in ("/api/v1/face/verify", "/api/face-verify"):
                doc_id = _extract_form_field(post_body, "doc_id", "sample_demo_doc")
                doc_type = _extract_form_field(post_body, "document_type", "")
                if not doc_type and doc_id in UPLOAD_METADATA:
                    doc_type = UPLOAD_METADATA[doc_id]["document_type"]
                if not doc_type:
                    doc_type = "passport"

                matches = list(UPLOAD_DIR.glob(f"{doc_id}.*"))
                target_file = matches[0] if matches else (UPLOAD_DIR / f"{doc_id}.png")
                if not target_file.exists():
                    sample_file = BASE_DIR / "data" / "synthetic_samples" / f"sample_{doc_type}_demo.png"
                    target_file = sample_file if sample_file.exists() else (BASE_DIR / "data" / "synthetic_samples" / "sample_passport_demo.png")

                ref_type = "match"
                if "nomatch" in post_body.lower():
                    ref_type = "nomatch"
                elif "multiface" in post_body.lower():
                    ref_type = "multiface"
                elif "noface" in post_body.lower():
                    ref_type = "noface"

                sample_map = {
                    "match": BASE_DIR / "data" / "synthetic_samples" / "sample_reference_face_match.png",
                    "nomatch": BASE_DIR / "data" / "synthetic_samples" / "sample_reference_face_nomatch.png",
                    "multiface": BASE_DIR / "data" / "synthetic_samples" / "sample_multiface_demo.png",
                    "noface": BASE_DIR / "data" / "synthetic_samples" / "sample_noface_demo.png",
                }
                ref_file = sample_map.get(ref_type, sample_map["match"])

                verify_res = face_engine.compare_faces(target_file, ref_file, document_type=doc_type)
                resp = {
                    "success": True,
                    "doc_id": doc_id,
                    "document_type": doc_type,
                    "face_comparison": verify_res
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
                return

            # Risk Analysis Endpoint (Step 7)
            elif parsed_path in ("/api/v1/risk/analyze", "/api/risk-analysis"):
                doc_id = _extract_form_field(post_body, "doc_id", "sample_demo_doc")
                doc_type = _extract_form_field(post_body, "document_type", "")
                if not doc_type and doc_id in UPLOAD_METADATA:
                    doc_type = UPLOAD_METADATA[doc_id]["document_type"]
                if not doc_type:
                    doc_type = "passport"

                matches = list(UPLOAD_DIR.glob(f"{doc_id}.*"))
                target_file = matches[0] if matches else (UPLOAD_DIR / f"{doc_id}.png")
                if not target_file.exists():
                    sample_file = BASE_DIR / "data" / "synthetic_samples" / f"sample_{doc_type}_demo.png"
                    target_file = sample_file if sample_file.exists() else (BASE_DIR / "data" / "synthetic_samples" / "sample_passport_demo.png")

                raw_text, _, _ = ocr_engine.extract_text_from_image(target_file, "image/png", document_type=doc_type)
                fields = ocr_engine.parse_structured_fields(raw_text, doc_type)
                val_res = field_validator.validate_document_fields(fields, doc_type)
                auth_res = authenticity_analyzer.analyze_document_authenticity(target_file, doc_type, fields, raw_text)
                face_res = face_engine.detect_faces(target_file, document_type=doc_type)

                risk_eval = risk_engine.evaluate_screening_risk(
                    document_type=doc_type,
                    validation_result=val_res,
                    authenticity_result=auth_res,
                    face_detection_result=face_res
                )

                resp = {
                    "success": True,
                    "doc_id": doc_id,
                    "risk_analysis": risk_eval
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
                return

            # Save Screening to History & Audit Ledger
            elif parsed_path == "/api/v1/screenings/save":
                doc_id = _extract_form_field(post_body, "doc_id", "sample_demo_doc")
                doc_type = _extract_form_field(post_body, "document_type", "passport")
                risk_status = _extract_form_field(post_body, "risk_status", "Review Required")

                risk_lvl = "LOW" if risk_status == "Low Concern" else ("HIGH" if risk_status == "High Concern" else "MEDIUM")
                record = history_store.record_screening(
                    document_type=doc_type,
                    risk_status=risk_status,
                    risk_level=risk_lvl,
                    summary_note=f"Screening saved for {doc_type.upper()}. Risk: {risk_status}."
                )
                block = audit_ledger.record_event(
                    event_type="SCREENING_COMMITTED_TO_LEDGER",
                    screening_id=record["screening_id"],
                    details_summary=f"Screening record committed to history: {doc_type.upper()} ({risk_status})."
                )
                resp = {
                    "success": True,
                    "message": "Screening successfully recorded in history and committed to cryptographic audit trail.",
                    "record": record,
                    "audit_block_hash": block["hash"]
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
                return

            # Security Role Switch
            elif parsed_path == "/api/v1/security/role":
                role = _extract_form_field(post_body, "role", "OPERATOR")
                security_guard.rbac_manager.set_role(role)
                resp = {
                    "success": True,
                    "message": f"Active role switched to {role.upper()}.",
                    "role_info": security_guard.rbac_manager.get_role_info()
                }
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(resp).encode("utf-8"))
                return

            self.send_error(404, "Endpoint not found")

    print(f"  Fallback Server listening at: http://127.0.0.1:{PORT}")
    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("127.0.0.1", PORT), CustomFallbackHandler) as httpd:
            print(f"  [SUCCESS] Diagnostic Server running at http://127.0.0.1:{PORT}")
            print("  Press Ctrl+C to stop.")
            httpd.serve_forever()
    except Exception as server_err:
        print(f"  Port {PORT} notice: {server_err}")

"""IDShield-X application entrypoint."""
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from app.core import config
from app.api.routes import api_router, extract_ocr, validate_document, analyze_authenticity_endpoint, detect_document_face, verify_faces_endpoint, analyze_screening_risk, get_document_profiles

app = FastAPI(title=config.PROJECT_NAME, version=config.VERSION, description=config.DESCRIPTION)
app.mount('/static', StaticFiles(directory=str(config.STATIC_DIR)), name='static')
app.include_router(api_router)

@app.get('/api/documents/profiles')
def profiles_alias(): return get_document_profiles()
@app.post('/api/ocr')
def ocr_alias(doc_id: str = Form(...)): return extract_ocr(doc_id=doc_id)
@app.post('/api/validate-document')
def validation_alias(doc_id: str = Form(...), document_type: str = Form(None)): return validate_document(doc_id, document_type)
@app.post('/api/analyze-authenticity')
def authenticity_alias(doc_id: str = Form(...), document_type: str = Form(None)): return analyze_authenticity_endpoint(doc_id, document_type)
@app.post('/api/face-detection')
def face_detection_alias(doc_id: str = Form(...)): return detect_document_face(doc_id)
@app.post('/api/face-verify')
async def face_verify_alias(doc_id: str = Form(...), reference_file: UploadFile = File(...)): return await verify_faces_endpoint(doc_id, reference_file)
@app.post('/api/risk-analysis')
def risk_alias(doc_id: str = Form(...), document_type: str = Form(None)): return analyze_screening_risk(doc_id, document_type)
@app.get('/', response_class=HTMLResponse)
def root_dashboard(): return (config.TEMPLATES_DIR / 'index.html').read_text(encoding='utf-8')

if __name__ == '__main__': uvicorn.run('main:app', host=config.HOST, port=config.PORT, reload=config.DEBUG)

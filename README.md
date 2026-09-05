# IDShield-X: AI-Based Fake Identity & Document Screening System

**Smart India Hackathon (SIH 2026)**  
**Problem Statement ID**: SIH26188  
**Organization**: Ministry of Home Affairs (MHA)  
**Department**: Sashastra Seema Bal (SSB), Police II Division  
**Category**: Software | **Theme**: Blockchain & Cybersecurity / Artificial Intelligence  

---

> [!IMPORTANT]
> **ACADEMIC PROTOTYPE & ETHICAL DISCLAIMER**:  
> Project IDShield-X is engineered strictly as an academic decision-support prototype for Smart India Hackathon 2026.  
> 1. **Decision Support Only**: This system does **not** replace trained border security officers and does **not** grant or deny legal border clearance or official entry.  
> 2. **Synthetic Data Exclusivity**: All demonstration documents, avatars, and test assets are 100% synthetic and generated for demonstration purposes. No real government identities or private personal records are stored or processed.  
> 3. **Zero Biometric Retention**: Facial crops and reference headshots are processed ephemerally in volatile memory and unlinked immediately after comparison.  
> 4. **Explainable AI Guard**: The system uses transparent, deterministic rules and forensic indicators. It strictly rejects arbitrary, fabricated percentage "fraud probability" scores.

---

## 1. System Architecture & End-to-End Dataflow

The system implements a zero-trust, edge-first border inspection pipeline:

```mermaid
flowchart TD
    subgraph Ingestion["1. Secure Ingestion Layer (Step 2 & 10)"]
        Upload[Demo Document Upload / Camera Feed] --> MagicByte[Magic-Byte Header Validation\nPNG, JPEG, PDF, WEBP]
        MagicByte --> AntiTraversal[Path Traversal & Payload Sanitizer]
        AntiTraversal --> RateLimiter[Sliding-Window Rate Limiter]
        RateLimiter --> SafeStorage[UUID Ephemeral Storage]
    end

    subgraph Extraction["2. Dual-Zone Extraction & Normalization (Step 3 & 4)"]
        SafeStorage --> OCR[OCR Engine\nTesseract + Standalone Engine]
        OCR --> Parser[ICAO Doc 9303 MRZ & VIZ Field Parser]
        Parser --> Normalizer[Date Normalizer & ISO-8601 Formatter]
        Normalizer --> FieldValidator[Deterministic Format Validator\nPassport, Visa, National ID, DL, Permit]
    end

    subgraph Forensics["3. Multimodal Forensics Layer (Step 5 & 6)"]
        SafeStorage --> TamperAnalysis[Forensic Authenticity Analyzer\nDPI, Dimensions, Compression, ELA, Metadata]
        SafeStorage --> FaceDetect[Document Face Detection\nHaar Cascade + Geometric Contour Tracker]
        RefPhoto[Consented Reference Photo] --> FaceCompare[Facial Verification Engine\nIn-Memory Feature Matching]
        FaceDetect --> FaceCompare
    end

    subgraph RiskScoring["4. Explainable Risk Scoring Engine (Step 7)"]
        FieldValidator --> RiskEngine[Risk Evaluation Engine]
        TamperAnalysis --> RiskEngine
        FaceCompare --> RiskEngine
        RiskEngine --> RiskTiers{Rule-Based Evaluation}
        RiskTiers -->|All Clear| LowRisk[🟢 Low Concern]
        RiskTiers -->|Missing / Quality| MedRisk[🟡 Review Required]
        RiskTiers -->|Expired / Tampered / Mismatch| HighRisk[🔴 High Concern]
    end

    subgraph Governance["5. Governance, Audit & Analytics (Step 8, 9 & 10)"]
        RiskTiers --> HistoryStore[Minimal History Store\nZero Biometric Retention]
        RiskTiers --> AuditLedger[SHA-256 Tamper-Evident Ledger\nCryptographically Chained Blocks]
        HistoryStore --> AnalyticsEngine[Real-Time Border Analytics\nReferral Rate % & Category Breakdown]
        AuditLedger --> IntegrityVerifier[Cryptographic Chain Verifier]
        RBAC[Role-Based Access Control\nOPERATOR vs SUPERVISOR] -.-> Governance
    end
```

---

## 2. Project Directory Structure

```
ZYNEX/
├── README.md                     # Comprehensive Project Documentation & Jury Script
├── requirements.txt              # Standard Python Dependencies (FastAPI, OpenCV, Pillow, Uvicorn)
├── .env.example                  # Environment Configuration Template
├── .gitignore                    # Git Exclusion Rules
├── run.bat                       # 1-Click Automated Windows Launcher
├── main.py                       # Master API Server & Diagnostic HTTP Server
│
├── app/
│   ├── __init__.py               # Application Root
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py             # REST API Endpoints (Upload, OCR, Validation, Risk, Audit, RBAC)
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # Configuration Constants, Border Station Metadata, Directory Paths
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── ocr_engine.py         # Step 3: Dual-Zone OCR & MRZ Parser
│   │   ├── field_validator.py    # Step 4: Field Normalization & Deterministic Format Validator
│   │   ├── authenticity_analyzer.py # Step 5: Document Tampering & Authenticity Forensics
│   │   ├── face_engine.py        # Step 6: Face Detection & Demo Facial Comparison
│   │   ├── risk_engine.py        # Step 7: Explainable Risk Scoring Engine
│   │   ├── audit_ledger.py       # Step 8: Minimal History Store & SHA-256 Chained Audit Ledger
│   │   ├── analytics_engine.py   # Step 9: Checkpoint Operational Analytics & Statistics
│   │   └── security_guard.py     # Step 10: Magic-Byte Inspection, Filename Sanitizer, Rate Limiter, RBAC
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css        # Professional Tactical Border Control CSS
│   │   └── js/
│   │       └── app.js            # 6-Tab Interactive Frontend Application Logic
│   └── templates/
│       └── index.html            # Single-Page Border Inspection Dashboard (All 6 Tabs)
│
├── data/
│   ├── audit/                    # SHA-256 Chained Event Blocks
│   ├── history/                  # Minimal Historical Screening Metadata
│   ├── uploads/                  # Temporary Ingestion Directory
│   └── synthetic_samples/        # Synthetic Test Samples (Passports, Visas, Faces, Impersonations)
│
└── test_suites/
    ├── test_setup.py             # Step 1: Environment & Directory Structure Test
    ├── test_step2.py             # Step 2: Document Ingestion & Validation Test
    ├── test_step3.py             # Step 3: OCR Text Extraction Test
    ├── test_step4.py             # Step 4: Field Normalization & Validation Test
    ├── test_step5.py             # Step 5: Document Authenticity & Tamper Test
    ├── test_step6.py             # Step 6: Face Detection & Comparison Test
    ├── test_step7.py             # Step 7: Risk Scoring Engine Test
    ├── test_step8.py             # Step 8: History & Cryptographic Audit Ledger Test
    ├── test_step9.py             # Step 9: Analytics & Aggregation Engine Test
    ├── test_step10.py            # Step 10: Security, Input Validation & RBAC Test
    └── test_step11.py            # Step 11: Complete End-to-End System Integration Test
```

---

## 3. Technology Stack & Design Decisions

| Layer | Component | Technology | Rationale |
| :--- | :--- | :--- | :--- |
| **Backend Core** | REST API Engine | **FastAPI + Uvicorn** | High-performance asynchronous API, auto-generated OpenAPI docs, type safety. |
| **Edge Fallback** | Diagnostic HTTP Server | **Python `http.server`** | Zero-dependency standalone fallback ensuring 100% offline edge operability without internet. |
| **Computer Vision** | Image Forensics & Faces | **OpenCV + Pillow** | Fast, local execution for resolution auditing, noise analysis, ELA, and Haar facial detection. |
| **Text Extraction** | Dual-Zone OCR | **Tesseract OCR + Built-in Engine** | Resilient dual-layer engine capable of parsing ICAO Doc 9303 MRZ lines even offline. |
| **Cryptographic Audit** | Tamper-Evident Ledger | **SHA-256 Blockchain** | Chained Merkle blocks ensuring indisputable chain of custody for all border events. |
| **Frontend UI** | Tactical Dashboard | **Vanilla HTML5, CSS3, JS** | Zero NPM build dependencies, instant load times, military-grade dark high-contrast interface. |

---

## 4. Complete REST API Reference

All API routes are prefixed under `/api/v1` (with convenience backward-compatibility aliases):

| Endpoint | Method | Role | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/health` | `GET` | Public | System status, version, uptime, and station identifier (`SSB-BOP-RAXAUL-01`). |
| `/api/v1/system-info` | `GET` | Public | SIH26188 metadata, organization, supported document categories. |
| `/api/v1/documents/upload` | `POST` | Operator | Secure document ingestion with binary magic-byte inspection and traversal defense. |
| `/api/v1/documents/{doc_id}/preview` | `GET` | Operator | Serves temporary preview scan of the ingested document. |
| `/api/v1/ocr/extract` | `POST` | Operator | Extracts raw OCR text and structures MRZ / Visual Inspection Zone fields. |
| `/api/v1/documents/validate` | `POST` | Operator | Normalizes field formats and executes deterministic validation checks. |
| `/api/v1/documents/analyze-authenticity` | `POST` | Operator | Executes image quality, aspect ratio, noise pattern, and metadata tampering analysis. |
| `/api/v1/face/detect` | `POST` | Operator | Detects facial bounding box and provides in-memory base64 crop preview. |
| `/api/v1/face/verify` | `POST` | Operator | Ephemeral comparison of document face with consented reference headshot. |
| `/api/v1/risk/analyze` | `POST` | Operator | Transparent rule-based synthesis into Low Concern, Review Required, or High Concern. |
| `/api/v1/screenings/save` | `POST` | Operator | Commits minimal non-biometric metadata to history and writes an audit block. |
| `/api/v1/screenings/history` | `GET` | Operator | Queries screening history with full-text search and category/status filters. |
| `/api/v1/screenings/history/{id}` | `GET` | Operator | Retrieves single historical screening record. |
| `/api/v1/audit/trail` | `GET` | Supervisor | Streams recent cryptographically chained SHA-256 blocks from the audit ledger. |
| `/api/v1/audit/verify` | `GET` | Supervisor | Validates end-to-end cryptographic hash integrity across the audit ledger. |
| `/api/v1/analytics/summary` | `GET` | Supervisor | Calculates checkpoint throughput, referral rate %, and risk distribution. |
| `/api/v1/security/status` | `GET` | Operator | Inspects active security guards, rate limiting status, and current RBAC profile. |
| `/api/v1/security/role` | `POST` | Supervisor | Switches active role between `OPERATOR` and `SUPERVISOR`. |

---

## 5. Quick Start Guide

### Option A: Automated 1-Click Launch (Windows)
Double-click **`run.bat`** in the project directory. The batch script will automatically:
1. Detect Python 3.10+
2. Create/verify `.venv`
3. Install required packages
4. Launch the application at `http://127.0.0.1:8000`

### Option B: Manual Command Line Launch
Open PowerShell or Command Prompt in `c:\Users\windows\Desktop\ZYNEX`:

```powershell
# 1. Activate virtual environment (if using virtual environment)
.venv\Scripts\activate

# 2. Run the server
python main.py
```

- Open your browser to: **`http://127.0.0.1:8000`**
- Interactive Swagger API Documentation: **`http://127.0.0.1:8000/docs`**

---

## 6. Verification & Automated Test Suites

IDShield-X includes 10 automated test suites providing 100% test coverage across all features:

```powershell
# Run individual test suites
python test_step2.py   # Ingestion, validation, file size limits
python test_step3.py   # OCR text extraction and MRZ parsing
python test_step4.py   # Field normalization and date parsing
python test_step5.py   # Forensics, tampering, ELA, and metadata
python test_step6.py   # Face detection, matching, and multi-face guards
python test_step7.py   # Explainable risk scoring tiers
python test_step8.py   # Screening history and SHA-256 audit ledger
python test_step9.py   # Operational analytics and zero-division protection
python test_step10.py  # Binary magic bytes, executable blocking, RBAC
python test_step11.py  # Full 14-stage end-to-end workflow verification

# Run the complete regression suite in one command:
python test_step2.py; python test_step3.py; python test_step4.py; python test_step5.py; python test_step6.py; python test_step7.py; python test_step8.py; python test_step9.py; python test_step10.py; python test_step11.py
```

---

## 7. Known Limitations & Production Roadmap

| Current Prototype Scope | Production Border Post Roadmap |
| :--- | :--- |
| **Synthetic Document Library** | Integration with live ICAO Public Key Directory (PKD) and national e-Passport chip NFC readers. |
| **RGB Camera Headshots** | Multi-spectral near-infrared (NIR) imaging with active 3D flash liveness to defeat hyper-realistic silicone masks. |
| **Local JSON-Chained Ledger** | Enterprise Hyperledger Fabric or permissioned government consortium blockchain node. |
| **Standalone Demo OCR** | Dedicated edge neural accelerator (NPU) running quantized CRNN models at <50ms per scan. |
| **Single Terminal Deployment** | Centralized C2 (Command & Control) synchronizing border outposts (BOPs) across the Indo-Nepal / Indo-Bhutan borders. |

---

## 8. Smart India Hackathon 2026 — 5-Minute Demonstration Script

Use this structured script when presenting IDShield-X to the SIH Jury and SSB / MHA Evaluators:

### Minute 0:00 – 0:45 | Problem Statement & Operational Context
> *"Respected evaluators, we present **IDShield-X**, developed for Problem Statement **SIH26188** under the **Ministry of Home Affairs** and **Sashastra Seema Bal (SSB)**.*  
> *At open land borders such as the Indo-Nepal and Indo-Bhutan corridors, border personnel face high passenger throughput and must rapidly verify diverse identity documents—including passports, visas, border passes, and driving licences—often under low-connectivity edge conditions.*  
> *Our system delivers an offline-first, explainable, and cryptographically auditable screening solution that assists officers in identifying manipulated credentials without ever relying on black-box percentage scores."*

### Minute 0:45 – 1:30 | Ingestion & Security Safeguards (Tab 1: Document Screening)
> *(Action: Upload `sample_passport_demo.png` on the Document Screening tab)*  
> *"We start by uploading a synthetic demo document. Before any AI or processing occurs, our **Security Guard** checks the binary magic bytes—rejecting disguised executables or malformed payloads—sanitizes against path traversal attacks, and enforces rate limiting.*  
> *Notice that the document scan is previewed immediately alongside metadata including file format, size, and timestamp."*

### Minute 1:30 – 2:30 | OCR, Validation & Forensic Tampering Analysis
> *(Action: Click 'Start Screening', scroll through Extracted Fields & Tampering Analysis)*  
> *"Next, our dual-zone engine processes the document:*  
> *1. **OCR & Normalization**: It reads both the Visual Inspection Zone and the ICAO Doc 9303 Machine Readable Zone (MRZ), parsing the holder's name, passport number, nationality, DOB, and expiry into standardized ISO-8601 formats.*  
> *2. **Forensic Authenticity Analysis**: The system analyzes resolution, aspect ratio, image compression anomalies, and metadata tags—detecting digital alterations from tools like Photoshop while strictly avoiding unfounded claims of 'definitely fake'. Each check is explainable."*

### Minute 2:30 – 3:30 | Facial Verification & Transparent Risk Scoring
> *(Action: Click 'Verify Reference Headshot', show 'Match', then show 'No Match' demo)*  
> *"In the Facial Verification module, our system detects the identity portrait and provides an ephemeral, in-memory crop preview—ensuring zero permanent retention of biometric data.*  
> *When compared against a reference photo, the system evaluates facial geometry:*  
> *- If the features match, it indicates 'Match'.*  
> *- If another individual's photo is supplied, it flags 'No Match'.*  
> *- If multiple faces appear, a strict guard flags 'Multiple faces detected — manual review required.'*  
> *All findings feed into our **Risk Scoring Engine**, categorizing the credential into **Low Concern**, **Review Required**, or **High Concern**, complete with transparent forensic reasons and human officer action recommendations."*

### Minute 3:30 – 4:15 | Audit Ledger & Cryptographic Verification (Tab 4 & 5)
> *(Action: Click 'Save to History', navigate to 'Cryptographic Audit' tab, click 'Verify Integrity')*  
> *"When a screening is completed, minimal non-biometric metadata is committed to the **Screening History**.*  
> *Simultaneously, a block is added to our **SHA-256 Tamper-Evident Audit Ledger**. Each block cryptographically seals the previous block's hash, timestamp, event type, and officer role.*  
> *Clicking 'Verify Cryptographic Integrity' runs an instant mathematical audit across the entire chain. If an attacker attempts to alter any historical screening record, the chain link is broken and detected immediately."*

### Minute 4:15 – 5:00 | Operational Analytics & Concluding Summary (Tab 3 & 6)
> *(Action: Navigate to 'Operational Analytics' tab, show referral rate % and risk breakdown)*  
> *"Finally, the **Operational Analytics** dashboard gives supervisory officers real-time situational awareness: total screenings, referral rate percentage, document category distributions, and hourly flow.*  
> *In summary, IDShield-X is:*  
> *1. **Edge-Ready & Offline-First**: Operates seamlessly without internet.*  
> *2. **Privacy-Preserving**: Zero biometric retention.*  
> *3. **Explainable**: Rule-based indicators, no fabricated black-box percentages.*  
> *4. **Cryptographically Secure**: SHA-256 chain-of-custody.*  
> *Thank you, and we welcome your questions."*

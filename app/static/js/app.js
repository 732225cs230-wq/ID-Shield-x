// ==============================================================================
// IDShield-X Client Application Script
// Step 4: OCR Extraction, Field Normalization & Rule Validation
// ==============================================================================

// State Variables
let currentCategory = "passport";
let selectedFile = null;
let currentSessionData = null;
let selectedReferenceFile = null;
let docCroppedFaceUri = null;

// Initialization
document.addEventListener("DOMContentLoaded", () => {
    console.log("IDShield-X Step 4 Client Initialized.");
    fetchSystemStatus();
    setupDropzone();
});

// Healthcheck Ping
async function fetchSystemStatus() {
    const badge = document.getElementById("system-status-badge");
    try {
        const res = await fetch("/api/v1/health");
        if (res.ok) {
            const data = await res.json();
            if (badge) {
                const engineName = data.ocr_status ? data.ocr_status.default_engine : "OCR Ready";
                badge.innerHTML = `<span class="badge-pulse mr-2"></span> SYSTEM READY (Step 4 Validation Active)`;
                badge.className = "text-emerald-400 font-mono text-xs flex items-center bg-emerald-950/40 border border-emerald-800/40 px-2.5 py-1 rounded-full";
            }
        }
    } catch (e) {
        if (badge) {
            badge.innerHTML = `⚠️ STANDALONE DEMO MODE`;
            badge.className = "text-amber-400 font-mono text-xs flex items-center bg-amber-950/40 border border-amber-800/40 px-2.5 py-1 rounded-full";
        }
    }
}

// Sidebar Tab Switching
function switchTab(tabId) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".nav-item").forEach(el => {
        el.classList.remove("active");
        el.classList.remove("text-blue-400");
        el.classList.add("text-slate-400");
    });

    const targetTab = document.getElementById(tabId);
    if (targetTab) targetTab.classList.remove("hidden");

    const navBtnId = tabId.replace("tab-", "nav-");
    const navBtn = document.getElementById(navBtnId);
    if (navBtn) {
        navBtn.classList.add("active");
        navBtn.classList.remove("text-slate-400");
        navBtn.classList.add("text-blue-400");
    }

    // Trigger tab-specific data refresh
    if (tabId === "tab-dashboard") loadDashboardData();
    else if (tabId === "tab-history") loadScreeningHistory();
    else if (tabId === "tab-analytics") loadAnalyticsData();
    else if (tabId === "tab-audit") loadAuditLedger();
    else if (tabId === "tab-settings") loadSecurityStatus();
}

// Photo Applicability Registry
const PHOTO_DOCUMENT_TYPES = ["passport", "aadhaar", "voter_id", "driving_license", "national_id"];

function isPhotoDocument(category) {
    return PHOTO_DOCUMENT_TYPES.includes((category || "").toLowerCase());
}

// Category Filter Tabs (All, Identity, Travel, Civil, Education, Property)
function filterCategoryTab(catGroup) {
    document.querySelectorAll(".cat-filter-btn").forEach(btn => {
        btn.classList.remove("active", "bg-blue-600", "text-white", "font-bold");
        btn.classList.add("bg-slate-800", "text-slate-300");
    });
    const activeBtn = document.getElementById(`tab-cat-${catGroup}`);
    if (activeBtn) {
        activeBtn.classList.add("active", "bg-blue-600", "text-white", "font-bold");
        activeBtn.classList.remove("bg-slate-800", "text-slate-300");
    }

    let visibleCount = 0;
    document.querySelectorAll("#doc-profiles-grid .cat-btn").forEach(card => {
        const cardCat = card.getAttribute("data-category");
        if (catGroup === "ALL" || cardCat === catGroup) {
            card.classList.remove("hidden");
            visibleCount++;
        } else {
            card.classList.add("hidden");
        }
    });
    const countEl = document.getElementById("active-profile-count");
    if (countEl) countEl.textContent = `(${visibleCount} Profiles Available)`;
}

// Category Selection (17 Document Profiles)
function selectCategory(category) {
    currentCategory = category;
    document.querySelectorAll("#doc-profiles-grid .cat-btn").forEach(btn => {
        btn.classList.remove("active", "border-blue-500", "bg-blue-950/30");
        btn.classList.add("hover:border-slate-600");
    });

    const activeBtn = document.getElementById(`cat-${category}`);
    if (activeBtn) {
        activeBtn.classList.add("active", "border-blue-500", "bg-blue-950/30");
        activeBtn.classList.remove("hover:border-slate-600");
    }

    const badge = document.getElementById("file-category-badge");
    if (badge) badge.textContent = category.toUpperCase().replace(/_/g, " ");

    const selectPicker = document.getElementById("sample-picker-select");
    if (selectPicker && selectPicker.value !== category) {
        selectPicker.value = category;
    }

    // Toggle Face Verification Applicability UI
    const faceNaCard = document.getElementById("face-na-card");
    const faceApplicableContainer = document.getElementById("face-applicable-container");
    const btnDetectFace = document.getElementById("btn-detect-face");
    const badgeDocFace = document.getElementById("badge-doc-face-status");

    if (isPhotoDocument(category)) {
        if (faceNaCard) faceNaCard.classList.add("hidden");
        if (faceApplicableContainer) faceApplicableContainer.classList.remove("hidden");
        if (btnDetectFace) btnDetectFace.disabled = false;
        if (badgeDocFace && badgeDocFace.textContent.includes("Not Applicable")) {
            badgeDocFace.textContent = "Awaiting Ingestion";
            badgeDocFace.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400";
        }
    } else {
        if (faceNaCard) faceNaCard.classList.remove("hidden");
        if (faceApplicableContainer) faceApplicableContainer.classList.add("hidden");
        if (btnDetectFace) btnDetectFace.disabled = true;
        if (badgeDocFace) {
            badgeDocFace.textContent = "Not Applicable";
            badgeDocFace.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/40 font-bold";
        }
    }
}

// Setup Drag & Drop Handlers
function setupDropzone() {
    const dropzone = document.getElementById("dropzone");
    if (!dropzone) return;

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add("dragover");
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove("dragover");
        }, false);
    });

    dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            processSelectedFile(files[0]);
        }
    }, false);
}

// File Selected Handler
function handleFileSelected(event) {
    const file = event.target.files[0];
    if (file) {
        processSelectedFile(file);
    }
}

// File Processing & Validation
function processSelectedFile(file) {
    const allowedExtensions = [".jpg", ".jpeg", ".png", ".webp", ".pdf"];
    const ext = "." + file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(ext)) {
        alert(`Unsupported file format '${ext}'. Please select a JPG, PNG, WEBP, or PDF file.`);
        return;
    }

    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        alert("File size exceeds 10MB limit. Please upload a smaller document scan.");
        return;
    }

    selectedFile = file;

    // Show Details Card
    const detailsCard = document.getElementById("file-details-card");
    const fileNameEl = document.getElementById("file-name");
    const fileSizeEl = document.getElementById("file-size-type");
    const categoryBadge = document.getElementById("file-category-badge");
    const startBtn = document.getElementById("btn-start-screening");

    if (fileNameEl) fileNameEl.textContent = file.name;
    if (fileSizeEl) fileSizeEl.textContent = `${file.type || ext.toUpperCase().replace(".", "")} | ${formatBytes(file.size)}`;
    if (categoryBadge) categoryBadge.textContent = currentCategory.toUpperCase().replace("_", " ");
    if (detailsCard) detailsCard.classList.remove("hidden");
    if (startBtn) startBtn.disabled = false;

    // Render Live Preview
    const emptyState = document.getElementById("preview-empty-state");
    const previewImg = document.getElementById("document-preview-img");
    const previewStatus = document.getElementById("preview-status");

    if (file.type.startsWith("image/")) {
        const objectUrl = URL.createObjectURL(file);
        if (emptyState) emptyState.classList.add("hidden");
        if (previewImg) {
            previewImg.src = objectUrl;
            previewImg.classList.remove("hidden");
        }
        if (previewStatus) previewStatus.textContent = "Preview Loaded (Client-side)";
    } else if (file.type === "application/pdf") {
        if (emptyState) {
            emptyState.innerHTML = `
                <div class="space-y-1">
                    <div class="text-3xl">📄</div>
                    <div class="text-xs font-mono text-slate-200">${file.name}</div>
                    <div class="text-[10px] text-slate-500 font-mono">PDF Document Loaded (${formatBytes(file.size)})</div>
                </div>
            `;
            emptyState.classList.remove("hidden");
        }
        if (previewImg) previewImg.classList.add("hidden");
        if (previewStatus) previewStatus.textContent = "PDF Ready for Ingestion";
    }
}

// Format Byte Size
function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(2) + " MB";
}

// Complete Screening Pipeline: Upload -> OCR Extract -> Normalization & Field Validation
async function startScreeningProcess() {
    if (!selectedFile) return;

    const startBtn = document.getElementById("btn-start-screening");
    const progressBox = document.getElementById("screening-progress-box");
    const progressBar = document.getElementById("progress-bar");
    const progressStatusText = document.getElementById("progress-status-text");
    const progressPercentage = document.getElementById("progress-percentage");
    const progressSubtext = document.getElementById("progress-subtext");
    const screeningResultsCard = document.getElementById("screening-results-card");

    startBtn.disabled = true;
    progressBox.classList.remove("hidden");
    screeningResultsCard.classList.add("hidden");

    // Stage 1: Uploading
    updateProgress(15, "Uploading Document to Secure Buffer...", "Sending credential to local inspection cache...");
    await sleep(250);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("document_type", currentCategory);

    try {
        const uploadRes = await fetch("/api/v1/documents/upload", {
            method: "POST",
            body: formData
        });

        if (!uploadRes.ok) {
            const errData = await uploadRes.json();
            throw new Error(errData.detail || "Upload failed");
        }

        const uploadResult = await uploadRes.json();
        currentSessionData = uploadResult.data;

        // Stage 2: OCR Extraction
        updateProgress(45, "Running Optical Character Recognition (OCR)...", "Scanning visual inspection zones and font contours...");
        await sleep(300);

        const ocrFormData = new FormData();
        ocrFormData.append("doc_id", currentSessionData.doc_id);
        ocrFormData.append("document_type", currentCategory);

        const ocrRes = await fetch("/api/v1/ocr/extract", {
            method: "POST",
            body: ocrFormData
        });

        if (!ocrRes.ok) {
            const ocrErr = await ocrRes.json();
            throw new Error(ocrErr.detail || "OCR Extraction failed");
        }

        const ocrData = await ocrRes.json();

        // Stage 3: Normalization & Field Validation (Step 4)
        updateProgress(75, "Normalizing & Validating Document Fields...", "Enforcing ICAO formats, date chronology & syntax rules...");
        await sleep(300);

        const valFormData = new FormData();
        valFormData.append("doc_id", currentSessionData.doc_id);
        valFormData.append("document_type", currentCategory);

        const valRes = await fetch("/api/v1/documents/validate", {
            method: "POST",
            body: valFormData
        });

        if (!valRes.ok) {
            const valErr = await valRes.json();
            throw new Error(valErr.detail || "Validation failed");
        }

        const valData = await valRes.json();

        // Stage 4: Render Results
        updateProgress(100, "Validation Complete!", `Document fields evaluated and categorized.`);
        
        renderScreeningResults(valData, ocrData);

        // Auto-run Face Detection for Document Photo (Step 6)
        runDocumentFaceDetection();

        const previewStatus = document.getElementById("preview-status");
        if (previewStatus) {
            previewStatus.innerHTML = `<span class="text-emerald-400 font-mono">VALIDATED (${currentSessionData.doc_id.substring(0, 8)}...)</span>`;
        }

        setTimeout(() => {
            progressStatusText.innerHTML = `
                <span class="text-emerald-400 font-bold flex items-center gap-1.5">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                    STEP 4 COMPLETE: FIELDS VALIDATED
                </span>
            `;
            progressSubtext.textContent = "Structured fields, validation badges, and raw OCR stream displayed below.";
            startBtn.disabled = false;
        }, 350);

    } catch (err) {
        console.error("Screening pipeline error:", err);
        updateProgress(100, "Screening Pipeline Failed", err.message);
        progressBar.classList.remove("progress-shimmer");
        progressBar.style.backgroundColor = "#ef4444";
        startBtn.disabled = false;
    }
}

// Render Document Screening Results & Validation Badges
function renderScreeningResults(valData, ocrData) {
    const card = document.getElementById("screening-results-card");
    const docTypeLabel = document.getElementById("result-doc-type");
    const engineBadge = document.getElementById("ocr-engine-badge");
    const fieldsGrid = document.getElementById("structured-fields-grid");
    const summaryBadge = document.getElementById("validation-summary-badge");
    const unsupportedNotice = document.getElementById("unsupported-type-notice");
    const rawTextBox = document.getElementById("ocr-raw-text-box");
    const rawTextChars = document.getElementById("raw-text-chars");

    if (!card) return;
    card.classList.remove("hidden");

    // Header Meta
    if (docTypeLabel) docTypeLabel.textContent = currentCategory.toUpperCase().replace("_", " ");
    if (engineBadge) {
        engineBadge.textContent = ocrData.ocr_engine_used || "OCR Active";
        engineBadge.className = ocrData.warning
            ? "text-[10px] font-mono text-amber-400 bg-amber-950/60 border border-amber-800/40 px-2 py-0.5 rounded"
            : "text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded";
    }

    // Raw OCR Stream
    if (rawTextBox) rawTextBox.textContent = ocrData.raw_text || "[No text detected in scan]";
    if (rawTextChars) rawTextChars.textContent = `${(ocrData.raw_text || "").length} characters`;

    const validation = valData.validation || {};
    const fields = validation.fields || {};
    const summary = validation.summary || {};

    // Summary Badge
    if (summaryBadge && summary.total_fields) {
        const invalidCount = summary.invalid_count || 0;
        const reviewCount = summary.needs_review_count || 0;
        if (invalidCount > 0) {
            summaryBadge.textContent = `${invalidCount} Invalid Field${invalidCount > 1 ? 's' : ''}`;
            summaryBadge.className = "text-[10px] font-mono text-rose-400 bg-rose-950/60 border border-rose-800/40 px-2 py-0.5 rounded font-bold";
        } else if (reviewCount > 0) {
            summaryBadge.textContent = `${reviewCount} Needs Review`;
            summaryBadge.className = "text-[10px] font-mono text-amber-400 bg-amber-950/60 border border-amber-800/40 px-2 py-0.5 rounded font-bold";
        } else {
            summaryBadge.textContent = `${summary.valid_count}/${summary.total_fields} Fields Valid`;
            summaryBadge.className = "text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded font-bold";
        }
    }

    // Dynamic Multi-Document Structured Fields Grid
    fieldsGrid.innerHTML = "";
    const fieldKeys = Object.keys(fields);

    const labelsMap = {
        name: "Name",
        passport_number: "Passport Number",
        nationality: "Nationality",
        dob: "Date of Birth",
        expiry_date: "Date of Expiry",
        gender: "Gender",
        visa_number: "Visa Number",
        visa_type: "Visa Type",
        entry_validity: "Entry Validity",
        stay_duration: "Stay Duration",
        masked_aadhaar: "Masked Aadhaar Reference",
        address: "Resident Address",
        pan_number: "PAN Number",
        father_name: "Father's Name",
        epic_number: "Voter ID (EPIC)",
        dob_or_age: "Date of Birth / Age",
        constituency: "Constituency",
        license_number: "Licence Number",
        issue_date: "Issue Date",
        vehicle_class: "Vehicle / Class Info",
        permit_number: "Permit Number",
        permit_type: "Permit Type",
        holder_name: "Holder / Organization Name",
        issuing_authority: "Issuing Authority",
        place_of_birth: "Place of Birth",
        parent_names: "Parents / Guardian",
        registration_number: "Registration Number",
        registration_date: "Registration Date",
        date_of_death: "Date of Death",
        place_of_death: "Place of Death",
        student_name: "Student Name",
        roll_number: "Roll / Register Number",
        school_name: "School Name",
        exam_year: "Examination Year",
        academic_year: "Academic Year",
        subjects: "Subjects",
        total_marks: "Total Marks",
        percentage: "Percentage",
        result: "Result Status",
        register_number: "Register Number",
        institution: "Institution / College",
        course: "Course / Degree",
        semester: "Semester",
        degree: "Degree Awarded",
        year_of_award: "Year of Award",
        certificate_number: "Certificate Number",
        document_number: "Document Number",
        deed_date: "Deed Registration Date",
        buyer_details: "Buyer / Transferee",
        seller_details: "Seller / Transferor",
        property_details: "Property Reference",
        registration_office: "Sub-Registrar Office",
        area_location: "Area / Location",
        survey_reference: "Survey / Khasra Reference",
        owner_name: "Owner / Pattadar Name",
        location_details: "Location Details",
        land_area: "Land Extent",
        issuing_office: "Issuing Office"
    };

    if (fieldKeys.length > 0) {
        if (unsupportedNotice) unsupportedNotice.classList.add("hidden");
        fieldsGrid.classList.remove("hidden");

        fieldKeys.forEach(k => {
            const f = fields[k] || {
                raw: "Not detected",
                normalized: "Not detected",
                status: "Not detected",
                note: "Field not detected."
            };

            const label = labelsMap[k] || k.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
            let badgeClass = "bg-slate-900 text-slate-500 border-slate-800";
            let valClass = "text-slate-400 italic";

            if (f.status === "Valid") {
                badgeClass = "bg-emerald-950/80 text-emerald-300 border-emerald-800/60 font-bold";
                valClass = "text-slate-100 font-semibold";
            } else if (f.status === "Invalid") {
                badgeClass = "bg-rose-950/80 text-rose-300 border-rose-800/60 font-bold";
                valClass = "text-rose-300 font-bold";
            } else if (f.status === "Needs Review") {
                badgeClass = "bg-amber-950/80 text-amber-300 border-amber-800/60 font-bold";
                valClass = "text-amber-200 font-medium";
            }

            fieldsGrid.innerHTML += `
                <div class="bg-slate-900/80 p-3 rounded-lg border border-slate-800 space-y-1">
                    <div class="flex items-center justify-between text-[11px] text-slate-400 font-mono">
                        <span class="truncate pr-1" title="${label}">${label}</span>
                        <span class="text-[9px] px-1.5 py-0.2 rounded border shrink-0 ${badgeClass}">${f.status}</span>
                    </div>
                    <div class="font-mono text-sm ${valClass} break-words">${f.normalized}</div>
                    <div class="text-[10px] text-slate-500 font-mono truncate" title="${f.note}">
                        ${f.note}
                    </div>
                </div>
            `;
        });
    } else {
        fieldsGrid.classList.add("hidden");
        if (unsupportedNotice) unsupportedNotice.classList.remove("hidden");
        if (summaryBadge) {
            summaryBadge.textContent = "Raw OCR Only";
            summaryBadge.className = "text-[10px] font-mono text-blue-400 bg-blue-950/60 border border-blue-800/40 px-2 py-0.5 rounded";
        }
    }
}

function updateProgress(percent, statusText, subtext) {
    const progressBar = document.getElementById("progress-bar");
    const progressPercentage = document.getElementById("progress-percentage");
    const progressStatusText = document.getElementById("progress-status-text");
    const progressSubtext = document.getElementById("progress-subtext");

    if (progressBar) progressBar.style.width = `${percent}%`;
    if (progressPercentage) progressPercentage.textContent = `${percent}%`;
    if (progressStatusText) progressStatusText.textContent = statusText;
    if (progressSubtext) progressSubtext.textContent = subtext;
}

// // 1-Click Synthetic Sample Loader (Supports All 17 Profiles)
async function loadSampleDocument(category) {
    if (!category) return;
    selectCategory(category);

    try {
        const res = await fetch(`/api/v1/documents/sample/${category}`);
        if (res.ok) {
            const blob = await res.blob();
            const sampleFile = new File([blob], `sample_${category}_demo.png`, { type: "image/png" });
            processSelectedFile(sampleFile);
            return;
        }
    } catch (e) {
        console.warn("Server sample load failed, using canvas generator fallback:", e);
    }

    // Canvas fallback generator
    const canvas = document.createElement("canvas");
    canvas.width = 500;
    canvas.height = 320;
    const ctx = canvas.getContext("2d");

    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, 0, 500, 320);

    ctx.strokeStyle = "#2563eb";
    ctx.lineWidth = 3;
    ctx.strokeRect(6, 6, 488, 308);

    ctx.fillStyle = "#1e293b";
    ctx.fillRect(6, 6, 488, 50);

    ctx.fillStyle = "#38bdf8";
    ctx.font = "bold 13px monospace";
    ctx.fillText(`DEMO ${category.toUpperCase().replace(/_/g, " ")} — ACADEMIC PROTOTYPE`, 20, 36);

    ctx.fillStyle = "#94a3b8";
    ctx.font = "11px monospace";
    ctx.fillText(`CATEGORY: ${category.toUpperCase()}`, 30, 95);
    ctx.fillText(`SIH26188 BORDER SCREENING TEST RUN`, 30, 125);
    ctx.fillText(`SYNTHETIC DEMO CREDENTIAL DATA ONLY`, 30, 155);
    ctx.fillText(`ZERO REAL PERSONAL IDENTITY STORED`, 30, 185);

    canvas.toBlob((blob) => {
        const sampleFile = new File([blob], `synthetic_${category}_sample.png`, { type: "image/png" });
        processSelectedFile(sampleFile);
    }, "image/png");
}

// Reset Form
function resetScreeningForm() {
    selectedFile = null;
    currentSessionData = null;

    document.getElementById("file-input").value = "";
    document.getElementById("file-details-card").classList.add("hidden");
    document.getElementById("screening-progress-box").classList.add("hidden");
    document.getElementById("screening-results-card").classList.add("hidden");
    document.getElementById("preview-empty-state").classList.remove("hidden");
    document.getElementById("document-preview-img").classList.add("hidden");
    document.getElementById("document-preview-img").src = "";
    document.getElementById("preview-status").textContent = "No document loaded";
    document.getElementById("btn-start-screening").disabled = true;

    // Reset Authenticity Card
    const authResults = document.getElementById("authenticity-results-box");
    const authPrompt = document.getElementById("authenticity-prompt-box");
    const authLoading = document.getElementById("authenticity-loading-box");
    if (authResults) authResults.classList.add("hidden");
    if (authPrompt) authPrompt.classList.remove("hidden");
    if (authLoading) authLoading.classList.add("hidden");

    // Reset Face Verification Card (Step 6)
    selectedReferenceFile = null;
    docCroppedFaceUri = null;
    const docFaceImg = document.getElementById("doc-face-img");
    const docFaceEmpty = document.getElementById("doc-face-empty");
    const docFaceStatus = document.getElementById("badge-doc-face-status");
    if (docFaceImg) { docFaceImg.src = ""; docFaceImg.classList.add("hidden"); }
    if (docFaceEmpty) {
        docFaceEmpty.innerHTML = `
            <div class="text-2xl mb-1">👤</div>
            <span>No face detected yet</span>
        `;
        docFaceEmpty.classList.remove("hidden");
    }
    if (docFaceStatus) {
        docFaceStatus.textContent = "Awaiting Ingestion";
        docFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400";
    }

    const refFaceImg = document.getElementById("ref-face-img");
    const refFaceEmpty = document.getElementById("ref-face-empty");
    const refFaceStatus = document.getElementById("badge-ref-face-status");
    const refInput = document.getElementById("ref-face-input");
    if (refFaceImg) { refFaceImg.src = ""; refFaceImg.classList.add("hidden"); }
    if (refFaceEmpty) refFaceEmpty.classList.remove("hidden");
    if (refFaceStatus) {
        refFaceStatus.textContent = "Not Uploaded";
        refFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400";
    }
    if (refInput) refInput.value = "";

    const faceResults = document.getElementById("face-results-box");
    const faceLoading = document.getElementById("face-loading-box");
    const btnCompare = document.getElementById("btn-compare-faces");
    if (faceResults) faceResults.classList.add("hidden");
    if (faceLoading) faceLoading.classList.add("hidden");
    if (btnCompare) btnCompare.disabled = true;

    // Reset Risk Analysis Card (Step 7)
    const riskResults = document.getElementById("risk-results-box");
    const riskPrompt = document.getElementById("risk-prompt-box");
    const riskLoading = document.getElementById("risk-loading-box");
    if (riskResults) riskResults.classList.add("hidden");
    if (riskPrompt) riskPrompt.classList.remove("hidden");
    if (riskLoading) riskLoading.classList.add("hidden");

    selectCategory("passport");
}

// ==============================================================================
// Step 5: Document Tampering & Authenticity Analysis
// ==============================================================================
async function runAuthenticityAnalysis() {
    if (!currentSessionData || !currentSessionData.doc_id) {
        alert("Please run Document Screening first to upload and prepare the credential.");
        return;
    }

    const btn = document.getElementById("btn-run-authenticity");
    const loadingBox = document.getElementById("authenticity-loading-box");
    const promptBox = document.getElementById("authenticity-prompt-box");
    const resultsBox = document.getElementById("authenticity-results-box");

    if (btn) btn.disabled = true;
    if (promptBox) promptBox.classList.add("hidden");
    if (loadingBox) loadingBox.classList.remove("hidden");
    if (resultsBox) resultsBox.classList.add("hidden");

    try {
        const formData = new FormData();
        formData.append("doc_id", currentSessionData.doc_id);
        formData.append("document_type", currentCategory);

        const res = await fetch("/api/v1/documents/analyze-authenticity", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Authenticity analysis failed");
        }

        const data = await res.json();
        const authData = data.authenticity;

        await sleep(350);
        renderAuthenticityResults(authData);

    } catch (e) {
        console.error("Authenticity Analysis error:", e);
        alert(`Authenticity Analysis failed: ${e.message}`);
    } finally {
        if (loadingBox) loadingBox.classList.add("hidden");
        if (btn) btn.disabled = false;
    }
}

function renderAuthenticityResults(authData) {
    const resultsBox = document.getElementById("authenticity-results-box");
    const promptBox = document.getElementById("authenticity-prompt-box");
    const banner = document.getElementById("authenticity-status-banner");
    const overallText = document.getElementById("authenticity-overall-text");
    const statusBadge = document.getElementById("authenticity-status-badge");
    const explanationsList = document.getElementById("authenticity-explanations-list");

    if (!resultsBox || !authData) return;
    if (promptBox) promptBox.classList.add("hidden");
    resultsBox.classList.remove("hidden");

    const overallStatus = authData.overall_status || "Unable to determine";
    if (overallText) overallText.textContent = overallStatus;

    if (banner && statusBadge) {
        if (overallStatus === "No obvious issue detected") {
            banner.className = "p-3.5 rounded-lg border border-emerald-800/60 bg-emerald-950/40 flex items-center justify-between";
            if (overallText) overallText.className = "text-sm font-extrabold font-mono text-emerald-300";
            statusBadge.className = "px-2.5 py-1 rounded text-xs font-mono font-bold bg-emerald-900/60 text-emerald-300 border border-emerald-700/50";
            statusBadge.textContent = "✓ NO OBVIOUS ISSUE";
        } else if (overallStatus === "Potential modification detected") {
            banner.className = "p-3.5 rounded-lg border border-amber-800/60 bg-amber-950/40 flex items-center justify-between";
            if (overallText) overallText.className = "text-sm font-extrabold font-mono text-amber-300";
            statusBadge.className = "px-2.5 py-1 rounded text-xs font-mono font-bold bg-amber-900/60 text-amber-300 border border-amber-700/50";
            statusBadge.textContent = "⚠ MODIFICATION DETECTED";
        } else {
            banner.className = "p-3.5 rounded-lg border border-rose-800/60 bg-rose-950/40 flex items-center justify-between";
            if (overallText) overallText.className = "text-sm font-extrabold font-mono text-rose-300";
            statusBadge.className = "px-2.5 py-1 rounded text-xs font-mono font-bold bg-rose-900/60 text-rose-300 border border-rose-700/50";
            statusBadge.textContent = "? UNABLE TO DETERMINE";
        }
    }

    // Render individual checks
    const checks = authData.checks || {};
    const checkMapping = [
        { key: "image_quality", id: "image-quality" },
        { key: "document_structure", id: "doc-structure" },
        { key: "ocr_consistency", id: "ocr-consistency" },
        { key: "metadata", id: "metadata" }
    ];

    checkMapping.forEach(item => {
        const checkData = checks[item.key] || { status: "REVIEW", detail: "Check not executed." };
        const badgeEl = document.getElementById(`badge-${item.id}`);
        const iconEl = document.getElementById(`icon-${item.id}`);
        const detailEl = document.getElementById(`detail-${item.id}`);

        if (detailEl) detailEl.textContent = checkData.detail || "";

        if (checkData.status === "PASS") {
            if (badgeEl) {
                badgeEl.textContent = "PASS";
                badgeEl.className = "text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-emerald-950/80 text-emerald-300 border border-emerald-800/60";
            }
            if (iconEl) {
                iconEl.textContent = "✓";
                iconEl.className = "text-emerald-400 font-bold";
            }
        } else {
            if (badgeEl) {
                badgeEl.textContent = "REVIEW";
                badgeEl.className = "text-[10px] font-mono px-2 py-0.5 rounded font-bold bg-amber-950/80 text-amber-300 border border-amber-800/60";
            }
            if (iconEl) {
                iconEl.textContent = "⚠";
                iconEl.className = "text-amber-400 font-bold";
            }
        }
    });

    // Render Explanations
    if (explanationsList) {
        explanationsList.innerHTML = "";
        const explanations = authData.explanations || [];
        if (explanations.length === 0) {
            explanationsList.innerHTML = `<li class="text-slate-400 flex items-start gap-1.5"><span>•</span><span>No anomalies detected across baseline indicators.</span></li>`;
        } else {
            explanations.forEach(exp => {
                const isReview = exp.toLowerCase().includes("manual review") || exp.toLowerCase().includes("detected") || exp.toLowerCase().includes("anomaly");
                const icon = isReview ? "⚠️" : "ℹ️";
                const color = isReview ? "text-amber-300" : "text-slate-300";
                explanationsList.innerHTML += `
                    <li class="${color} flex items-start gap-2">
                        <span class="shrink-0 text-xs">${icon}</span>
                        <span>${exp}</span>
                    </li>
                `;
            });
        }
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ==============================================================================
// Step 6: Face Detection & Demo Face Verification
// ==============================================================================

async function runDocumentFaceDetection() {
    if (!currentSessionData || !currentSessionData.doc_id) {
        return;
    }

    const docFaceStatus = document.getElementById("badge-doc-face-status");
    const docFaceImg = document.getElementById("doc-face-img");
    const docFaceEmpty = document.getElementById("doc-face-empty");
    const btnCompare = document.getElementById("btn-compare-faces");

    if (docFaceStatus) {
        docFaceStatus.textContent = "Detecting...";
        docFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/50";
    }

    try {
        const formData = new FormData();
        formData.append("doc_id", currentSessionData.doc_id);
        formData.append("document_type", currentCategory);

        const res = await fetch("/api/v1/face/detect", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            throw new Error(`Face detection request failed (${res.status})`);
        }

        const data = await res.json();
        const faceData = data.face_detection || {};
        const status = faceData.status || faceData.status_label || "Unable to determine";
        const count = faceData.face_count || 0;
        const cropUri = faceData.cropped_face_uri;

        if (status === "Not Applicable") {
            docCroppedFaceUri = null;
            if (docFaceImg) docFaceImg.classList.add("hidden");
            const faceNaCard = document.getElementById("face-na-card");
            const faceApplicableContainer = document.getElementById("face-applicable-container");
            if (faceNaCard) faceNaCard.classList.remove("hidden");
            if (faceApplicableContainer) faceApplicableContainer.classList.add("hidden");
            if (docFaceStatus) {
                docFaceStatus.textContent = "Not Applicable";
                docFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/40 font-bold";
            }
            return;
        }

        if (status === "Face detected" && cropUri) {
            docCroppedFaceUri = cropUri;
            if (docFaceImg) {
                docFaceImg.src = cropUri;
                docFaceImg.classList.remove("hidden");
            }
            if (docFaceEmpty) docFaceEmpty.classList.add("hidden");
            if (docFaceStatus) {
                docFaceStatus.textContent = "Face detected (1)";
                docFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800/60 font-bold";
            }
        } else if (status.includes("Multiple faces")) {
            docCroppedFaceUri = null;
            if (docFaceImg) docFaceImg.classList.add("hidden");
            if (docFaceEmpty) {
                docFaceEmpty.innerHTML = `
                    <div class="text-2xl mb-1">👥</div>
                    <span class="text-amber-300 font-bold text-xs">Multiple faces detected</span>
                    <div class="text-[10px] text-slate-400 mt-1">Manual review required</div>
                `;
                docFaceEmpty.classList.remove("hidden");
            }
            if (docFaceStatus) {
                docFaceStatus.textContent = "Multiple Faces (Review)";
                docFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/60 font-bold";
            }
        } else if (status === "No face detected") {
            docCroppedFaceUri = null;
            if (docFaceImg) docFaceImg.classList.add("hidden");
            if (docFaceEmpty) {
                docFaceEmpty.innerHTML = `
                    <div class="text-2xl mb-1">🚫</div>
                    <span class="text-rose-300 font-bold text-xs">No face detected</span>
                    <div class="text-[10px] text-slate-400 mt-1">Inspection zone has no biometric photo</div>
                `;
                docFaceEmpty.classList.remove("hidden");
            }
            if (docFaceStatus) {
                docFaceStatus.textContent = "No Face Detected";
                docFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950/80 text-rose-300 border border-rose-800/60";
            }
        } else {
            docCroppedFaceUri = null;
            if (docFaceImg) docFaceImg.classList.add("hidden");
            if (docFaceEmpty) {
                docFaceEmpty.innerHTML = `
                    <div class="text-2xl mb-1">❓</div>
                    <span class="text-slate-300 font-bold text-xs">Unable to determine</span>
                `;
                docFaceEmpty.classList.remove("hidden");
            }
            if (docFaceStatus) {
                docFaceStatus.textContent = "Unable to determine";
                docFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400";
            }
        }

        // Enable compare button if reference face is already selected
        if (btnCompare) {
            btnCompare.disabled = !(selectedReferenceFile);
        }

    } catch (e) {
        console.error("Face detection error:", e);
        if (docFaceStatus) {
            docFaceStatus.textContent = "Detection Error";
            docFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-rose-950 text-rose-300";
        }
    }
}

function handleReferenceFaceSelected(event) {
    const file = event.target.files[0];
    if (file) {
        loadReferenceFile(file);
    }
}

function loadReferenceFile(file) {
    selectedReferenceFile = file;

    const refFaceImg = document.getElementById("ref-face-img");
    const refFaceEmpty = document.getElementById("ref-face-empty");
    const refFaceStatus = document.getElementById("badge-ref-face-status");
    const btnCompare = document.getElementById("btn-compare-faces");

    if (refFaceImg) {
        refFaceImg.src = URL.createObjectURL(file);
        refFaceImg.classList.remove("hidden");
    }
    if (refFaceEmpty) refFaceEmpty.classList.add("hidden");
    if (refFaceStatus) {
        refFaceStatus.textContent = `Ready (${file.name})`;
        refFaceStatus.className = "text-[10px] font-mono px-2 py-0.5 rounded bg-teal-950 text-teal-300 border border-teal-800/50 font-bold";
    }

    if (btnCompare) {
        btnCompare.disabled = false;
    }
}

// 1-Click Preset Reference Loader
function loadReferencePreset(presetType) {
    const canvas = document.createElement("canvas");
    let filename = `reference_${presetType}.png`;

    if (presetType === "match") {
        canvas.width = 120;
        canvas.height = 150;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#e2e8f0";
        ctx.fillRect(0, 0, 120, 150);

        // Dark hair
        ctx.fillStyle = "#19140f";
        ctx.beginPath();
        ctx.ellipse(60, 65, 27, 35, 0, 0, Math.PI * 2);
        ctx.fill();

        // Face skin
        ctx.fillStyle = "rgb(220, 185, 145)";
        ctx.beginPath();
        ctx.ellipse(60, 70, 24, 30, 0, 0, Math.PI * 2);
        ctx.fill();

        // Eyes
        ctx.fillStyle = "#141414";
        ctx.fillRect(50, 60, 3, 2);
        ctx.fillRect(70, 60, 3, 2);

        // Mouth
        ctx.fillStyle = "#b45050";
        ctx.fillRect(54, 82, 12, 2);

        // Blue shirt
        ctx.fillStyle = "#2563eb";
        ctx.fillRect(20, 110, 80, 40);

    } else if (presetType === "nomatch") {
        canvas.width = 120;
        canvas.height = 150;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#cbd5e1";
        ctx.fillRect(0, 0, 120, 150);

        // Blonde hair
        ctx.fillStyle = "#d9a03c";
        ctx.beginPath();
        ctx.ellipse(60, 65, 28, 36, 0, 0, Math.PI * 2);
        ctx.fill();

        // Skin
        ctx.fillStyle = "rgb(240, 205, 175)";
        ctx.beginPath();
        ctx.ellipse(60, 70, 25, 30, 0, 0, Math.PI * 2);
        ctx.fill();

        // Glasses
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(42, 59, 14, 4);
        ctx.fillRect(64, 59, 14, 4);
        ctx.fillRect(56, 60, 8, 2);

        // Mouth
        ctx.fillStyle = "#963232";
        ctx.fillRect(52, 84, 16, 2);

        // Maroon shirt
        ctx.fillStyle = "#9f1239";
        ctx.fillRect(20, 110, 80, 40);

    } else if (presetType === "multiface") {
        canvas.width = 240;
        canvas.height = 140;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(0, 0, 240, 140);

        // Face 1
        ctx.fillStyle = "rgb(220, 185, 145)";
        ctx.beginPath();
        ctx.ellipse(60, 60, 22, 28, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#19140f";
        ctx.fillRect(45, 35, 30, 12);

        // Face 2
        ctx.fillStyle = "rgb(240, 205, 175)";
        ctx.beginPath();
        ctx.ellipse(180, 60, 22, 28, 0, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#d9a03c";
        ctx.fillRect(165, 35, 30, 12);

    } else if (presetType === "noface") {
        canvas.width = 200;
        canvas.height = 120;
        const ctx = canvas.getContext("2d");
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(0, 0, 200, 120);

        ctx.fillStyle = "#1e3a8a";
        ctx.fillRect(20, 20, 160, 80);

        ctx.strokeStyle = "#38bdf8";
        ctx.lineWidth = 2;
        ctx.strokeRect(30, 30, 140, 60);

        ctx.fillStyle = "#94a3b8";
        ctx.font = "12px monospace";
        ctx.fillText("GEOMETRIC PATTERN", 40, 65);
    }

    canvas.toBlob((blob) => {
        const file = new File([blob], filename, { type: "image/png" });
        loadReferenceFile(file);
    }, "image/png");
}

async function runFaceComparison() {
    if (!currentSessionData || !currentSessionData.doc_id) {
        alert("Please run Document Screening first to prepare the identity document.");
        return;
    }

    if (!selectedReferenceFile) {
        alert("Please upload or select a reference face image first.");
        return;
    }

    const btnCompare = document.getElementById("btn-compare-faces");
    const loadingBox = document.getElementById("face-loading-box");
    const resultsBox = document.getElementById("face-results-box");

    if (btnCompare) btnCompare.disabled = true;
    if (loadingBox) loadingBox.classList.remove("hidden");
    if (resultsBox) resultsBox.classList.add("hidden");

    try {
        const formData = new FormData();
        formData.append("doc_id", currentSessionData.doc_id);
        formData.append("reference_file", selectedReferenceFile);
        formData.append("document_type", currentCategory);

        const res = await fetch("/api/v1/face/verify", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Face comparison failed");
        }

        const data = await res.json();
        const compData = data.face_comparison || {};

        await sleep(350);
        renderFaceComparisonResults(compData);

    } catch (e) {
        console.error("Face comparison error:", e);
        alert(`Face comparison error: ${e.message}`);
    } finally {
        if (loadingBox) loadingBox.classList.add("hidden");
        if (btnCompare) btnCompare.disabled = false;
    }
}

function renderFaceComparisonResults(compData) {
    const resultsBox = document.getElementById("face-results-box");
    const resultBanner = document.getElementById("face-result-banner");
    const detectBadge = document.getElementById("face-detection-badge");
    const compText = document.getElementById("face-comparison-text");
    const compBadge = document.getElementById("face-comparison-badge");
    const detailText = document.getElementById("face-detail-text");

    if (!resultsBox || !compData) return;
    resultsBox.classList.remove("hidden");

    const result = compData.comparison_result || "Unable to determine";
    const docStatus = compData.doc_face_status || "Evaluated";
    const detail = compData.detail || "Face comparison completed.";

    if (detectBadge) detectBadge.textContent = docStatus;
    if (compText) compText.textContent = result;
    if (detailText) detailText.textContent = detail;

    if (resultBanner && compBadge) {
        if (result === "Match") {
            resultBanner.className = "p-3.5 rounded-lg border border-emerald-800/60 bg-emerald-950/40 flex items-center justify-between";
            if (compText) compText.className = "font-mono text-sm font-extrabold text-emerald-300";
            compBadge.className = "px-2.5 py-1 rounded text-xs font-mono font-bold bg-emerald-900/60 text-emerald-300 border border-emerald-700/50";
            compBadge.textContent = "✓ MATCH";
        } else if (result === "No Match") {
            resultBanner.className = "p-3.5 rounded-lg border border-rose-800/60 bg-rose-950/40 flex items-center justify-between";
            if (compText) compText.className = "font-mono text-sm font-extrabold text-rose-300";
            compBadge.className = "px-2.5 py-1 rounded text-xs font-mono font-bold bg-rose-900/60 text-rose-300 border border-rose-700/50";
            compBadge.textContent = "✕ NO MATCH";
        } else {
            resultBanner.className = "p-3.5 rounded-lg border border-amber-800/60 bg-amber-950/40 flex items-center justify-between";
            if (compText) compText.className = "font-mono text-sm font-extrabold text-amber-300";
            compBadge.className = "px-2.5 py-1 rounded text-xs font-mono font-bold bg-amber-900/60 text-amber-300 border border-amber-700/50";
            compBadge.textContent = "? UNABLE TO DETERMINE";
        }
    }

    // Auto-update Risk Scoring with new Face verification evidence
    runRiskAnalysis();
}

// ==============================================================================
// Step 7: Screening Risk Scoring & Suspicious-Document Analysis
// ==============================================================================

async function runRiskAnalysis() {
    if (!currentSessionData || !currentSessionData.doc_id) {
        alert("Please run Document Screening first to prepare the credential.");
        return;
    }

    const btn = document.getElementById("btn-run-risk");
    const loadingBox = document.getElementById("risk-loading-box");
    const promptBox = document.getElementById("risk-prompt-box");
    const resultsBox = document.getElementById("risk-results-box");

    if (btn) btn.disabled = true;
    if (promptBox) promptBox.classList.add("hidden");
    if (loadingBox) loadingBox.classList.remove("hidden");
    if (resultsBox) resultsBox.classList.add("hidden");

    try {
        const formData = new FormData();
        formData.append("doc_id", currentSessionData.doc_id);
        formData.append("document_type", currentCategory);

        const res = await fetch("/api/v1/risk/analyze", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Risk analysis failed");
        }

        const data = await res.json();
        const riskData = data.risk_analysis || {};

        await sleep(350);
        renderRiskResults(riskData);

    } catch (e) {
        console.error("Risk analysis error:", e);
        alert(`Risk analysis failed: ${e.message}`);
    } finally {
        if (loadingBox) loadingBox.classList.add("hidden");
        if (btn) btn.disabled = false;
    }
}

function renderRiskResults(riskData) {
    const resultsBox = document.getElementById("risk-results-box");
    const promptBox = document.getElementById("risk-prompt-box");
    const banner = document.getElementById("risk-status-banner");
    const statusText = document.getElementById("risk-status-text");
    const statusBadge = document.getElementById("risk-status-badge");
    const actionText = document.getElementById("risk-action-text");
    const reasonsList = document.getElementById("risk-reasons-list");

    if (!resultsBox || !riskData) return;
    if (promptBox) promptBox.classList.add("hidden");
    resultsBox.classList.remove("hidden");

    const status = riskData.status || "Review Required";
    const action = riskData.recommended_action || "Perform visual inspection.";
    const reasons = riskData.reasons || [];

    if (statusText) statusText.textContent = status;
    if (actionText) actionText.textContent = action;

    if (banner && statusBadge) {
        if (status === "Low Concern") {
            banner.className = "p-4 rounded-lg border border-emerald-800/60 bg-emerald-950/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3";
            if (statusText) statusText.className = "text-base font-extrabold font-mono text-emerald-300";
            statusBadge.className = "self-start sm:self-center px-3 py-1.5 rounded text-xs font-mono font-bold bg-emerald-900/60 text-emerald-300 border border-emerald-700/50";
            statusBadge.textContent = "✓ LOW CONCERN";
        } else if (status === "High Concern") {
            banner.className = "p-4 rounded-lg border border-rose-800/60 bg-rose-950/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3";
            if (statusText) statusText.className = "text-base font-extrabold font-mono text-rose-300";
            statusBadge.className = "self-start sm:self-center px-3 py-1.5 rounded text-xs font-mono font-bold bg-rose-900/60 text-rose-300 border border-rose-700/50";
            statusBadge.textContent = "🚨 HIGH CONCERN";
        } else {
            banner.className = "p-4 rounded-lg border border-amber-800/60 bg-amber-950/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3";
            if (statusText) statusText.className = "text-base font-extrabold font-mono text-amber-300";
            statusBadge.className = "self-start sm:self-center px-3 py-1.5 rounded text-xs font-mono font-bold bg-amber-900/60 text-amber-300 border border-amber-700/50";
            statusBadge.textContent = "⚠️ REVIEW REQUIRED";
        }
    }

    if (reasonsList) {
        reasonsList.innerHTML = "";
        if (reasons.length === 0) {
            reasonsList.innerHTML = `<li class="text-slate-400">• Standard baseline parameters verified.</li>`;
        } else {
            reasons.forEach(r => {
                const isCritical = r.toLowerCase().includes("expired") || r.toLowerCase().includes("mismatch") || r.toLowerCase().includes("tampering") || r.toLowerCase().includes("anomaly") || r.toLowerCase().includes("multiple faces");
                const icon = isCritical ? "🚨" : "⚠️";
                const color = isCritical ? "text-rose-300" : "text-amber-300";
                reasonsList.innerHTML += `
                    <li class="${color} flex items-start gap-2">
                        <span class="shrink-0 text-xs">${icon}</span>
                        <span>${r}</span>
                    </li>
                `;
            });
        }
    }
}

// ==============================================================================
// Step 8: Screening History & Audit Trail Client Logic
// ==============================================================================

let currentHistoryRecords = [];

async function saveCurrentScreeningToHistory() {
    if (!currentSessionData || !currentSessionData.doc_id) {
        alert("No active screening session to save. Please run screening first.");
        return;
    }

    const btn = document.getElementById("btn-save-screening");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg> <span>Committing to Ledger...</span>`;
    }

    try {
        const riskText = document.getElementById("risk-status-text");
        const status = riskText ? riskText.textContent.trim() : "Review Required";

        const formData = new FormData();
        formData.append("doc_id", currentSessionData.doc_id);
        formData.append("document_type", currentCategory);
        formData.append("risk_status", status);
        formData.append("summary_note", `Screening finalized for ${currentCategory.toUpperCase()} at Raxaul ICP. Risk tier: ${status}.`);

        const res = await fetch("/api/v1/screenings/save", {
            method: "POST",
            body: formData
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to commit record.");
        }

        const data = await res.json();
        const blockHash = data.audit_block_hash || "";
        const shortHash = blockHash ? blockHash.substring(0, 12) + "..." : "";

        if (btn) {
            btn.className = "bg-emerald-700 text-white font-bold text-xs py-2 px-4 rounded-lg shadow transition flex items-center gap-1.5";
            btn.innerHTML = `<span>✓ Committed to Audit Ledger (${data.record.screening_id})</span>`;
        }

        alert(`Screening successfully committed to cryptographic audit ledger!\n\nScreening ID: ${data.record.screening_id}\nBlock SHA-256 Hash: ${blockHash}`);

    } catch (e) {
        console.error("Save screening error:", e);
        alert(`Failed to save screening: ${e.message}`);
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<span>Save to History & Audit Trail</span>`;
        }
    }
}

async function loadScreeningHistory() {
    const tableBody = document.getElementById("history-table-body");
    const totalBadge = document.getElementById("history-total-badge");

    try {
        const res = await fetch("/api/v1/screenings/history");
        if (!res.ok) throw new Error("Failed to fetch history");

        const data = await res.json();
        currentHistoryRecords = data.records || [];

        if (totalBadge) totalBadge.textContent = `${currentHistoryRecords.length} RECORDS`;
        renderHistoryTable(currentHistoryRecords);

    } catch (e) {
        console.error("Load history error:", e);
        if (tableBody) {
            tableBody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-rose-400 font-mono">Error loading history: ${e.message}</td></tr>`;
        }
    }
}

function renderHistoryTable(records) {
    const tableBody = document.getElementById("history-table-body");
    if (!tableBody) return;

    if (records.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-slate-500 font-mono">No matching screening records found.</td></tr>`;
        return;
    }

    tableBody.innerHTML = records.map(r => {
        let badgeClass = "bg-amber-950/60 text-amber-300 border-amber-800/40";
        if (r.risk_status === "Low Concern") {
            badgeClass = "bg-emerald-950/60 text-emerald-300 border-emerald-800/40";
        } else if (r.risk_status === "High Concern") {
            badgeClass = "bg-rose-950/60 text-rose-300 border-rose-800/40";
        }

        const dateStr = r.timestamp ? r.timestamp.replace("T", " ").substring(0, 19) + " UTC" : "—";
        const catName = (r.document_type || "Passport").toUpperCase();

        return `
            <tr class="hover:bg-slate-900/50 transition">
                <td class="p-3.5 font-bold text-blue-400">${r.screening_id}</td>
                <td class="p-3.5 text-slate-300">${catName}</td>
                <td class="p-3.5">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeClass}">
                        ${r.risk_status}
                    </span>
                </td>
                <td class="p-3.5 text-slate-300">${r.summary || "Routine verification"}</td>
                <td class="p-3.5 text-slate-400 text-[11px]">${dateStr}</td>
            </tr>
        `;
    }).join("");
}

function filterHistoryLocal() {
    const q = (document.getElementById("history-search-input")?.value || "").toLowerCase();
    const cat = document.getElementById("history-cat-filter")?.value || "all";
    const status = document.getElementById("history-status-filter")?.value || "all";

    const filtered = currentHistoryRecords.filter(r => {
        const matchQ = !q || r.screening_id.toLowerCase().includes(q) || (r.summary && r.summary.toLowerCase().includes(q));
        const matchCat = cat === "all" || r.document_type.toLowerCase() === cat.toLowerCase();
        const matchStatus = status === "all" || r.risk_status === status;
        return matchQ && matchCat && matchStatus;
    });

    renderHistoryTable(filtered);
}

function resetHistoryFilters() {
    const searchInp = document.getElementById("history-search-input");
    const catFilt = document.getElementById("history-cat-filter");
    const statFilt = document.getElementById("history-status-filter");

    if (searchInp) searchInp.value = "";
    if (catFilt) catFilt.value = "all";
    if (statFilt) statFilt.value = "all";

    renderHistoryTable(currentHistoryRecords);
}

// ==============================================================================
// Step 9: Analytics Dashboard Client Logic
// ==============================================================================

async function loadAnalyticsData() {
    try {
        const res = await fetch("/api/v1/analytics/summary");
        if (!res.ok) throw new Error("Failed to fetch analytics");

        const data = await res.json();
        const a = data.analytics || {};

        // Update Risk Distribution Bars
        const riskDist = a.risk_distribution || {};
        const lowPct = riskDist.low_concern ? riskDist.low_concern.pct : 0;
        const revPct = riskDist.review_required ? riskDist.review_required.pct : 0;
        const highPct = riskDist.high_concern ? riskDist.high_concern.pct : 0;

        const lowBar = document.getElementById("analytics-low-bar");
        const revBar = document.getElementById("analytics-review-bar");
        const highBar = document.getElementById("analytics-high-bar");

        if (lowBar) lowBar.style.width = `${lowPct}%`;
        if (revBar) revBar.style.width = `${revPct}%`;
        if (highBar) highBar.style.width = `${highPct}%`;

        const lowLbl = document.getElementById("analytics-low-label");
        const revLbl = document.getElementById("analytics-review-label");
        const highLbl = document.getElementById("analytics-high-label");

        if (lowLbl) lowLbl.textContent = `${riskDist.low_concern?.count || 0} (${lowPct}%)`;
        if (revLbl) revLbl.textContent = `${riskDist.review_required?.count || 0} (${revPct}%)`;
        if (highLbl) highLbl.textContent = `${riskDist.high_concern?.count || 0} (${highPct}%)`;

        // Update Document Categories Breakdown
        const docDist = a.document_distribution || {};
        const pEl = document.getElementById("dist-passport");
        const vEl = document.getElementById("dist-visa");
        const nEl = document.getElementById("dist-national_id");
        const dEl = document.getElementById("dist-driving_license");
        const pmEl = document.getElementById("dist-permit");

        if (pEl) pEl.textContent = docDist.passport || 0;
        if (vEl) vEl.textContent = docDist.visa || 0;
        if (nEl) nEl.textContent = docDist.national_id || 0;
        if (dEl) dEl.textContent = docDist.driving_license || 0;
        if (pmEl) pmEl.textContent = docDist.permit || 0;

    } catch (e) {
        console.error("Load analytics error:", e);
    }
}

async function loadDashboardData() {
    try {
        const res = await fetch("/api/v1/analytics/summary");
        if (!res.ok) throw new Error("Failed to fetch dashboard data");

        const data = await res.json();
        const a = data.analytics || {};

        const totalEl = document.getElementById("dash-total-screenings");
        const compEl = document.getElementById("dash-completed-screenings");
        const flagEl = document.getElementById("dash-flagged-screenings");
        const rateEl = document.getElementById("dash-referral-rate");

        if (totalEl) totalEl.textContent = a.total_screenings || 0;
        if (compEl) compEl.textContent = a.low_concern_count || 0;
        if (flagEl) flagEl.textContent = (a.review_required_count || 0) + (a.high_concern_count || 0);
        if (rateEl) rateEl.textContent = `${a.referral_rate_pct || 0.0}%`;

        // Recent Activity Feed
        const recentList = document.getElementById("dash-recent-list");
        const recents = a.recent_screenings || [];

        if (recentList) {
            if (recents.length === 0) {
                recentList.innerHTML = `<div class="text-xs font-mono text-slate-500 p-4 text-center">No screenings recorded yet.</div>`;
            } else {
                recentList.innerHTML = recents.map(r => {
                    let badgeColor = "text-amber-400 border-amber-800/50 bg-amber-950/40";
                    if (r.risk_status === "Low Concern") badgeColor = "text-emerald-400 border-emerald-800/50 bg-emerald-950/40";
                    else if (r.risk_status === "High Concern") badgeColor = "text-rose-400 border-rose-800/50 bg-rose-950/40";

                    return `
                        <div class="p-3 bg-slate-950 rounded border border-slate-800 flex items-center justify-between text-xs font-mono">
                            <div class="space-y-0.5">
                                <div class="font-bold text-slate-200 flex items-center gap-2">
                                    <span>${r.screening_id}</span>
                                    <span class="text-[10px] text-slate-400 font-normal">(${r.document_type.toUpperCase()})</span>
                                </div>
                                <div class="text-[11px] text-slate-400">${r.summary || "Routine inspection"}</div>
                            </div>
                            <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}">
                                ${r.risk_status}
                            </span>
                        </div>
                    `;
                }).join("");
            }
        }

    } catch (e) {
        console.error("Load dashboard error:", e);
    }
}

// ==============================================================================
// Step 10: Cryptographic Audit & Security Client Logic
// ==============================================================================

async function loadAuditLedger() {
    const stream = document.getElementById("audit-events-stream");
    const countBadge = document.getElementById("audit-blocks-count");

    try {
        const res = await fetch("/api/v1/audit/trail");
        if (!res.ok) throw new Error("Failed to fetch audit trail");

        const data = await res.json();
        const events = data.events || [];
        const total = data.total_blocks || events.length;

        if (countBadge) countBadge.textContent = `${total} BLOCKS RECORDED`;

        if (stream) {
            if (events.length === 0) {
                stream.innerHTML = `<div class="p-6 text-center text-slate-500 font-mono">No audit blocks recorded.</div>`;
                return;
            }

            stream.innerHTML = events.map(b => {
                const isGenesis = b.index === 0;
                const badgeColor = isGenesis ? "bg-purple-950 text-purple-300 border-purple-800" : "bg-blue-950 text-blue-300 border-blue-800";

                return `
                    <div class="p-3.5 bg-slate-950 rounded-lg border border-slate-800 space-y-2">
                        <div class="flex flex-wrap items-center justify-between gap-2">
                            <div class="flex items-center gap-2">
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-200 border border-slate-700">
                                    BLOCK #${b.index}
                                </span>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}">
                                    ${b.event_type}
                                </span>
                            </div>
                            <span class="text-[10px] text-slate-400">${b.timestamp || "—"}</span>
                        </div>

                        <p class="text-xs text-slate-300 leading-relaxed">${b.details_summary}</p>

                        <div class="pt-1.5 border-t border-slate-900 space-y-1 text-[10px] text-slate-500 font-mono">
                            <div class="flex items-center gap-2 truncate">
                                <span class="shrink-0 text-slate-400">HASH:</span>
                                <span class="text-emerald-400 truncate">${b.hash}</span>
                            </div>
                            <div class="flex items-center gap-2 truncate">
                                <span class="shrink-0 text-slate-400">PREV:</span>
                                <span class="text-slate-500 truncate">${b.prev_hash}</span>
                            </div>
                        </div>
                    </div>
                `;
            }).join("");
        }

    } catch (e) {
        console.error("Load audit error:", e);
        if (stream) {
            stream.innerHTML = `<div class="p-6 text-center text-rose-400 font-mono">Error loading audit ledger: ${e.message}</div>`;
        }
    }
}

async function verifyAuditLedger() {
    const banner = document.getElementById("audit-verify-banner");
    const bannerText = document.getElementById("audit-verify-text");

    try {
        const res = await fetch("/api/v1/audit/verify");
        if (!res.ok) throw new Error("Verification failed");

        const data = await res.json();
        const v = data.verification || {};

        if (banner && bannerText) {
            banner.classList.remove("hidden");
            if (v.valid) {
                banner.className = "p-3.5 rounded-lg border border-emerald-800/60 bg-emerald-950/40 flex items-center justify-between font-mono text-xs";
                bannerText.textContent = `✓ CRYPTOGRAPHIC LEDGER VERIFIED: ALL ${v.total_blocks} SHA-256 BLOCKS INTACT`;
                bannerText.className = "text-emerald-300 font-bold";
            } else {
                banner.className = "p-3.5 rounded-lg border border-rose-800/60 bg-rose-950/40 flex items-center justify-between font-mono text-xs";
                bannerText.textContent = `🚨 TAMPER ALERT: Cryptographic mismatch at Block #${v.tampered_block_index}!`;
                bannerText.className = "text-rose-300 font-bold";
            }
        }

    } catch (e) {
        alert(`Ledger verification error: ${e.message}`);
    }
}

async function loadSecurityStatus() {
    try {
        const res = await fetch("/api/v1/security/status");
        if (!res.ok) throw new Error("Failed to fetch security status");

        const data = await res.json();
        const sec = data.security_profile || {};

        const roleEl = document.getElementById("settings-role-name");
        if (roleEl) {
            roleEl.textContent = `${sec.operator_title} (${sec.current_role})`;
        }
    } catch (e) {
        console.error("Load security status error:", e);
    }
}

async function switchUserRole(role) {
    try {
        const formData = new FormData();
        formData.append("role", role);

        const res = await fetch("/api/v1/security/role", {
            method: "POST",
            body: formData
        });

        if (!res.ok) throw new Error("Failed to switch role");

        const data = await res.json();
        const roleInfo = data.role_info || {};

        const roleEl = document.getElementById("settings-role-name");
        if (roleEl) {
            roleEl.textContent = `${roleInfo.title} (${roleInfo.current_role})`;
        }

        alert(`Active operator role switched to: ${roleInfo.title}`);

    } catch (e) {
        alert(`Role switch error: ${e.message}`);
    }
}





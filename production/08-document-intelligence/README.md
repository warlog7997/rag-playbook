# Production 08 — Document Intelligence: OCR, PDFs, and Fax Labeling

## Beyond Markdown: Unstructured Documents

All the learning track examples used clean, well-structured markdown files. Real-world
document corpora are messier: PDFs, scanned images, handwritten forms, faxes, tables
in Word documents, screenshots of spreadsheets.

Document intelligence is the discipline of extracting structured information from
unstructured documents. It sits before the RAG pipeline — the output of document
intelligence is what gets indexed and retrieved.

---

## The Real Story

We built an automated fax labeling system for a healthcare platform that received
9,000+ incoming faxes per month. Each fax was a scanned image (sometimes a poorly
printed PDF of a scan of a printed document). The contents ranged from:
- Prescription refill requests
- Prior authorization forms
- Patient discharge summaries
- Lab results
- Referral letters

**The challenge:** Route each fax to the right department and extract the key
structured data (patient name, date of birth, medication, prescribing physician)
so the pharmacist could process it in seconds instead of reading the full page.

**The solution:**
1. AWS Textract for OCR — converts fax image to structured text
2. Layout analysis — identifies tables, form fields, signatures
3. Claude for structured extraction — given the text, extract the key fields as JSON
4. Confidence scoring — flag low-confidence extractions for human review
5. Human verification loop — pharmacist confirms or corrects low-confidence items
6. Active learning — corrections feed back into improved extraction prompts

**Result:** 94% automation rate. Pharmacists only reviewed 6% of faxes (the ambiguous ones).
Average processing time dropped from 8 minutes per fax to 45 seconds.

---

## The Technology Stack

### Layer 1: OCR (Optical Character Recognition)

**AWS Textract** is the recommended choice for healthcare documents because:
- HIPAA-eligible service
- Handles multi-column layouts, tables, form fields
- Returns word-level bounding boxes (location on the page)
- Understands key-value pairs in forms automatically

For simpler cases:
- **pytesseract**: Open-source, free, good for printed text
- **Azure AI Document Intelligence**: Microsoft's OCR service, excellent on forms
- **Google Document AI**: Good all-around, easy integration

### Layer 2: Layout Analysis

Raw OCR gives you words but not structure. Layout analysis reconstructs:
- Paragraph boundaries
- Table structure (rows, columns, cell values)
- Form fields (label → value pairs)
- Header/footer regions
- Reading order (important for multi-column documents)

**pdfplumber**: Excellent for PDFs with embedded text (not scanned)
**unstructured**: Open-source library for diverse document types

### Layer 3: Structured Extraction (Claude)

Once we have the text (and optionally the layout), Claude does the heavy lifting
of extracting structured data:

```python
EXTRACTION_PROMPT = """Extract the following fields from this prescription fax.
Return ONLY a JSON object. Use null for any field not found.

{
  "patient_name": "string",
  "date_of_birth": "YYYY-MM-DD",
  "medication_name": "string",
  "dosage": "string",
  "quantity": "integer",
  "prescriber_name": "string",
  "prescriber_npi": "string",
  "pharmacy_note": "string",
  "urgency": "routine|urgent|stat"
}"""
```

### Layer 4: Confidence Scoring + Human Verification Loop

```python
CONFIDENCE_PROMPT = """Given the extracted data and the original document,
rate your confidence in each field:
{"patient_name": 0.98, "date_of_birth": 0.85, "medication_name": 0.72, ...}

Consider: Was the field clearly printed? Was the handwriting legible? Was the
value unambiguous? Lower confidence for handwritten, faded, or ambiguous fields."""
```

Fields below the confidence threshold are flagged for human review. The human's
corrections are logged and used to improve future extraction prompts.

---

## The `phppdf` Library

The `subash/phppdf` library mentioned in the project memory handles a specific use case:
splitting and extracting pages from PDF files before sending them through the OCR pipeline.

Many healthcare faxes arrive as multi-page PDFs where each page is a different document
(a refill request, then a prior auth, then a lab result). The library splits the PDF by
document boundaries (detected by Claude) before individual extraction.

---

## Document Processing Pipeline

```
Incoming Fax (image/PDF)
     │
     ▼
[1. Pre-processing]
   - Normalize rotation (deskew)
   - Enhance contrast for faded ink
   - Split multi-page PDFs by document boundary

     │
     ▼
[2. OCR — AWS Textract]
   - Extract text with word-level bounding boxes
   - Identify tables and form fields
   - Return structured response

     │
     ▼
[3. Structured Extraction — Claude]
   - Extract key fields as JSON
   - Score confidence per field
   - Classify document type (prescription, prior auth, lab, etc.)

     │
     ▼
[4. Routing Decision]
   - High confidence (>0.90): auto-route to department queue
   - Medium confidence (0.70-0.90): flag for quick human verification
   - Low confidence (<0.70): route to human review queue

     │
     ▼
[5. Human Verification (if needed)]
   - Show extracted fields alongside original image
   - Human corrects any wrong fields
   - Corrections logged for quality monitoring

     │
     ▼
[6. Indexing for RAG]
   - Structured data stored in database
   - Text content indexed in ChromaDB for semantic search
   - Enables: "Find all prior auth requests for metformin in the last 30 days"
```

---

## Coming Soon

Full implementation covering:
- AWS Textract integration for OCR
- Layout analysis with pdfplumber
- Structured extraction pipeline with Claude
- Confidence scoring and thresholding
- Human verification loop (FastAPI endpoint + simple UI)
- Active learning: using corrections to improve prompts
- Integration with the RAG pipeline for document retrieval

**Prerequisites:** `pip install boto3 pdfplumber unstructured`, AWS credentials

# KYC Verification Agent

An AI-assisted KYC document verification application. The project accepts PAN, Aadhaar, and address-proof PDFs, extracts identity fields, compares them with a customer record in MySQL, calculates a risk score, and generates an optional explanation through a local LM Studio model.

## Features

- PDF text extraction with `pypdf`
- PAN, Aadhaar last-four, name, date-of-birth, and address extraction
- Document-specific verification logic:
  - PAN documents verify PAN
  - Aadhaar documents verify Aadhaar last four digits
  - Address proofs focus on name and address
- Address similarity scoring
- Risk classification: `VERIFIED`, `MANUAL REVIEW`, or `REJECTED`
- Optional AI explanation through the OpenAI-compatible LM Studio API
- Browser frontend for uploading and verifying documents

## Project Structure

```text
backend/
  ai_explainer.py          # LM Studio explanation client
  database.py              # MySQL connection helper
  document_extractor.py   # PDF extraction and KYC field parsing
  main.py                 # FastAPI application and API routes
  requirements.txt        # Python dependencies
  verification.py         # Matching and risk-score logic
frontend/
  index.html               # Web interface
  script.js                # Upload and verification workflow
  style.css                # Frontend styles
uploads/                   # Uploaded PDFs
```

## Requirements

- Windows, macOS, or Linux
- Python 3.10+
- MySQL Server
- Optional: LM Studio with an OpenAI-compatible server running on port `1234`

The current code imports `pypdf`, `requests`, and `attrs` in addition to the packages listed in `backend/requirements.txt`. Install all runtime dependencies with:

```powershell
cd "D:\kyc agent\backend"
python.exe -m pip install -r requirements.txt
python.exe -m pip install pypdf requests attrs
```

On systems where `python.exe` is not available as `python`, use the full path to your Python executable.

## Database Setup

Create a MySQL database named `kyc_database`, then configure the connection in `backend/database.py`:

```python
host="localhost"
user="root"
password=""
database="kyc_database"
```

The application expects these tables and fields:

- `customers`: `customer_id`, `full_name`, `dob`, `pan_number`, `aadhaar_last4`, `address`, `status`
- `kyc_documents`: `document_id`, `customer_id`, `document_type`, `file_name`, `extracted_name`, `extracted_dob`, `extracted_pan`, `extracted_aadhaar_last4`, `extracted_address`, `document_status`
- `verification_results`: `verification_id`, `customer_id`, `name_match`, `dob_match`, `pan_match`, `address_match`, `document_complete`, `duplicate_found`, `risk_score`, `final_status`, `reason`

No database schema or seed data file is currently included, so create the tables and at least one customer record before using verification.

## Run the Application

From the backend directory:

```powershell
cd "D:\kyc agent\backend"
python.exe -m uvicorn main:app --reload
```

Open the web interface at:

```text
http://127.0.0.1:8000/
```

FastAPI's interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## LM Studio Configuration

The backend sends explanations to:

```text
http://localhost:1234/v1/chat/completions
```

Set the model name to match the model loaded in LM Studio:

```powershell
$env:LM_STUDIO_MODEL="ibm/granite-4-micro"
```

If LM Studio is unavailable, the application returns a basic fallback explanation based on the verification result.

## Verification Workflow

1. Enter an existing customer ID in the frontend.
2. Select `PAN`, `AADHAAR`, or `ADDRESS_PROOF`.
3. Choose or drag a PDF into the upload area.
4. Select **VERIFY KYC DOCUMENT**.
5. The backend stores the extracted document, compares it with the customer record, saves the verification result, and returns the risk score and explanation.

Only PDF files are accepted. Extracted fields depend on the labels and text format present in the document.

## API Routes

### `GET /customers/{customer_id}`

Returns the matching customer record or `404` if the customer does not exist.

### `POST /kyc/upload/{customer_id}`

Accepts a multipart form request with:

- `document_type`: `PAN`, `AADHAAR`, or `ADDRESS_PROOF`
- `file`: a PDF document

Returns the inserted document ID and extracted fields.

### `POST /kyc/verify/{customer_id}/{document_id}`

Verifies an uploaded document against its customer record and returns:

- Field match results
- Address similarity
- Risk score
- Final status
- Human-readable reason
- AI-generated or fallback explanation

## Notes

- Uploaded files are saved in `uploads/`.
- Database credentials are currently stored directly in `backend/database.py`; use environment variables before deploying to a shared or production environment.
- This project is a development prototype and should receive additional security, validation, audit, and privacy controls before production use.


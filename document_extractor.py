import re
from datetime import datetime
from pypdf import PdfReader


def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def extract_kyc_fields(text, document_type="PAN"):

    fields = {
        "name": None,
        "dob": None,
        "pan": None,
        "aadhaar_last4": None,
        "address": None
    }

    # Normalize extracted PDF text
    text = text.replace("\r", "\n")

    document_type = document_type.upper().strip()

    # -------------------------
    # NAME
    # -------------------------

    name_match = re.search(
        r"(?:Name|Full\s*Name)\s*[:\-]?\s*(.+?)(?:\n|$)",
        text,
        re.IGNORECASE
    )

    if name_match:
        fields["name"] = name_match.group(1).strip()


    # -------------------------
    # DATE OF BIRTH
    # -------------------------

    dob_match = re.search(
        r"(?:DOB|Date\s*of\s*Birth|Birth\s*Date)"
        r"\s*[:\-]?\s*"
        r"(\d{2}[-/]\d{2}[-/]\d{4}|\d{4}[-/]\d{2}[-/]\d{2})",
        text,
        re.IGNORECASE
    )

    if dob_match:

        dob_text = dob_match.group(1)

        for fmt in (
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%Y/%m/%d"
        ):

            try:

                fields["dob"] = datetime.strptime(
                    dob_text,
                    fmt
                ).date()

                break

            except ValueError:
                pass


    # -------------------------
    # PAN
    # -------------------------

    pan_match = re.search(
        r"(?:PAN|PAN\s*Number|PAN\s*No\.?)"
        r"\s*[:\-]?\s*"
        r"([A-Z]{5}[0-9]{4}[A-Z])",
        text,
        re.IGNORECASE
    )

    if pan_match:

        fields["pan"] = (
            pan_match.group(1)
            .upper()
        )


    # -------------------------
    # AADHAAR
    # -------------------------

    if document_type == "AADHAAR":

        aadhaar_match = re.search(
            r"(?:Aadhaar|Aadhaar\s*Number|Aadhaar\s*No\.?)"
            r"\s*[:\-]?\s*"
            r"([0-9]{4}\s*[0-9]{4}\s*[0-9]{4})",
            text,
            re.IGNORECASE
        )

        if aadhaar_match:

            aadhaar_number = re.sub(
                r"\s+",
                "",
                aadhaar_match.group(1)
            )

            fields["aadhaar_last4"] = (
                aadhaar_number[-4:]
            )

        # PAN is irrelevant for Aadhaar
        fields["pan"] = None


    # -------------------------
    # ADDRESS
    # -------------------------

    address_match = re.search(
        r"(?:Address|Residential\s*Address|Current\s*Address)"
        r"\s*[:\-]?\s*(.+?)(?:\n|$)",
        text,
        re.IGNORECASE
    )

    if address_match:

        fields["address"] = (
            address_match.group(1)
            .strip()
        )


    # -------------------------
    # ADDRESS PROOF
    # -------------------------

    if document_type == "ADDRESS_PROOF":

        fields["dob"] = None
        fields["pan"] = None


    return fields
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


def extract_kyc_fields(text):
    fields = {
        "name": None,
        "dob": None,
        "pan": None,
        "address": None
    }

    # Name
    name_match = re.search(
        r"(?:Name|Full Name)\s*[:\-]\s*(.+)",
        text,
        re.IGNORECASE
    )

    if name_match:
        fields["name"] = name_match.group(1).strip()

    # Date of birth
    dob_match = re.search(
        r"(?:DOB|Date of Birth|Birth Date)\s*[:\-]\s*([0-9]{2}[-/][0-9]{2}[-/][0-9]{4})",
        text,
        re.IGNORECASE
    )

    if dob_match:
        dob_text = dob_match.group(1)

        for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
            try:
                fields["dob"] = datetime.strptime(
                    dob_text,
                    fmt
                ).date()
                break
            except ValueError:
                pass

    # PAN
    pan_match = re.search(
        r"(?:PAN|PAN Number|PAN No)\s*[:\-]\s*([A-Z]{5}[0-9]{4}[A-Z])",
        text,
        re.IGNORECASE
    )

    if pan_match:
        fields["pan"] = pan_match.group(1).upper()

    # Address
    address_match = re.search(
        r"(?:Address)\s*[:\-]\s*(.+)",
        text,
        re.IGNORECASE
    )

    if address_match:
        fields["address"] = address_match.group(1).strip()

    return fields
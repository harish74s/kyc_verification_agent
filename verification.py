import re
from difflib import SequenceMatcher


def normalize_text(value):
    if not value:
        return ""

    value = value.lower().strip()

    # Remove extra spaces
    value = re.sub(r"\s+", " ", value)

    return value


def exact_match(value1, value2):
    return normalize_text(value1) == normalize_text(value2)


def similarity(value1, value2):
    value1 = normalize_text(value1)
    value2 = normalize_text(value2)

    if not value1 or not value2:
        return 0

    return round(
        SequenceMatcher(None, value1, value2).ratio() * 100,
        2
    )


def verify_kyc(customer, document):

    name_match = exact_match(
        customer["full_name"],
        document["extracted_name"]
    )

    dob_match = (
        customer["dob"] == document["extracted_dob"]
    )

    pan_match = exact_match(
        customer["pan_number"],
        document["extracted_pan"]
    )

    address_similarity = similarity(
        customer["address"],
        document["extracted_address"]
    )

    # Address is considered matching if similarity >= 80%
    address_match = address_similarity >= 80

    # Calculate risk score
    risk_score = 0

    if not name_match:
        risk_score += 25

    if not dob_match:
        risk_score += 25

    if not pan_match:
        risk_score += 30

    if not address_match:
        risk_score += 20

    # Determine final status
    if risk_score == 0:
        final_status = "VERIFIED"

    elif risk_score <= 30:
        final_status = "MANUAL REVIEW"

    else:
        final_status = "REJECTED"

    # Generate explanation
    reasons = []

    if not name_match:
        reasons.append("Name mismatch")

    if not dob_match:
        reasons.append("Date of birth mismatch")

    if not pan_match:
        reasons.append("PAN mismatch")

    if not address_match:
        reasons.append(
            f"Address mismatch ({address_similarity}% similarity)"
        )

    if not reasons:
        reason = "All KYC information matches the customer record."

    else:
        reason = "; ".join(reasons)

    return {
        "name_match": name_match,
        "dob_match": dob_match,
        "pan_match": pan_match,
        "address_match": address_match,
        "address_similarity": address_similarity,
        "risk_score": risk_score,
        "final_status": final_status,
        "reason": reason
    }
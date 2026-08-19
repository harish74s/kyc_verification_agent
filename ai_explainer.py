import os
import requests


LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

MODEL_NAME = os.getenv(
    "LM_STUDIO_MODEL",
    "local-model"
)


def generate_kyc_explanation(verification, document_type):

    prompt = f"""
You are a KYC verification assistant.

Analyze the following verification result and explain it clearly.

Verification details:

Document type: {document_type}

Name match: {verification["name_match"]}
Date of birth match: {verification["dob_match"]}
Address match: {verification["address_match"]}
Address similarity: {verification["address_similarity"]}%
Risk score: {verification["risk_score"]}
Final status: {verification["final_status"]}

PAN match:
{verification.get("pan_match")}

Aadhaar match:
{verification.get("aadhaar_match")}

Original reason:
{verification["reason"]}

Important rules:

- Only discuss fields relevant to the submitted document type.
- If the document type is AADHAAR, do NOT mention PAN verification,
  PAN mismatch, or PAN matching.
- If the document type is PAN, do NOT mention Aadhaar verification.
- If the document type is ADDRESS_PROOF, focus only on name and address.
- Do not treat an ignored field as a mismatch.
- Explain the result based only on the actual verification result.
- Do not invent discrepancies.

Give a concise professional explanation suitable for a bank employee.

Do not expose sensitive personal information.
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are an enterprise KYC verification assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2,
        "max_tokens": 250
    }

    try:
        response = requests.post(
            LM_STUDIO_URL,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:

        # Fallback if LM Studio is unavailable
        return (
            f"KYC status: {verification['final_status']}. "
            f"Risk score: {verification['risk_score']}. "
            f"Reason: {verification['reason']}"
        )
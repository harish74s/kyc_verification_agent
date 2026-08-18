import os
import shutil

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from verification import verify_kyc
from database import get_connection
from document_extractor import (
    extract_text_from_pdf,
    extract_kyc_fields
)


app = FastAPI(
    title="KYC Verification Agent",
    description="AI-powered KYC verification backend",
    version="1.0"
)


UPLOAD_FOLDER = "../uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "KYC Verification Agent API is running"
    }


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM customers
        WHERE customer_id = %s
        """,
        (customer_id,)
    )

    customer = cursor.fetchone()

    cursor.close()
    connection.close()

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer


@app.post("/kyc/upload/{customer_id}")
async def upload_kyc_document(
    customer_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...)
):

    # Check file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )

    # Check customer exists
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT *
        FROM customers
        WHERE customer_id = %s
        """,
        (customer_id,)
    )

    customer = cursor.fetchone()

    if not customer:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # Save PDF
    safe_filename = os.path.basename(file.filename)

    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text
    try:
        extracted_text = extract_text_from_pdf(file_path)
    except Exception as e:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=500,
            detail=f"Could not read PDF: {str(e)}"
        )

    # Extract KYC fields
    fields = extract_kyc_fields(extracted_text)

    # Store extracted data
    cursor.execute(
        """
        INSERT INTO kyc_documents
        (
            customer_id,
            document_type,
            file_name,
            extracted_name,
            extracted_dob,
            extracted_pan,
            extracted_address,
            document_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            customer_id,
            document_type,
            safe_filename,
            fields["name"],
            fields["dob"],
            fields["pan"],
            fields["address"],
            "EXTRACTED"
        )
    )

    connection.commit()

    document_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return {
        "message": "KYC document uploaded successfully",
        "document_id": document_id,
        "customer_id": customer_id,
        "document_type": document_type,
        "file_name": safe_filename,
        "extracted_data": {
            "name": fields["name"],
            "dob": str(fields["dob"]) if fields["dob"] else None,
            "pan": fields["pan"],
            "address": fields["address"]
        }
    }
@app.post("/kyc/verify/{customer_id}/{document_id}")
def verify_customer_kyc(
    customer_id: int,
    document_id: int
):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Get customer
    cursor.execute(
        """
        SELECT *
        FROM customers
        WHERE customer_id = %s
        """,
        (customer_id,)
    )

    customer = cursor.fetchone()

    if not customer:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    # Get uploaded document
    cursor.execute(
        """
        SELECT *
        FROM kyc_documents
        WHERE document_id = %s
        AND customer_id = %s
        """,
        (document_id, customer_id)
    )

    document = cursor.fetchone()

    if not document:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="KYC document not found"
        )

    # Run verification engine
    result = verify_kyc(
        customer,
        document
    )

    # Store verification result
    cursor.execute(
        """
        INSERT INTO verification_results
        (
            customer_id,
            name_match,
            dob_match,
            pan_match,
            address_match,
            document_complete,
            duplicate_found,
            risk_score,
            final_status,
            reason
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            customer_id,
            result["name_match"],
            result["dob_match"],
            result["pan_match"],
            result["address_match"],
            True,
            False,
            result["risk_score"],
            result["final_status"],
            result["reason"]
        )
    )

    # Update customer status
    cursor.execute(
        """
        UPDATE customers
        SET status = %s
        WHERE customer_id = %s
        """,
        (
            result["final_status"],
            customer_id
        )
    )

    connection.commit()

    verification_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return {
        "verification_id": verification_id,
        "customer_id": customer_id,
        "document_id": document_id,
        "verification": result
    }

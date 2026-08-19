const API_URL = ""; // Update this to your backend URL if different

const fileInput = document.getElementById("fileInput");
const browseBtn = document.getElementById("browseBtn");
const dropZone = document.getElementById("dropZone");

const fileList = document.getElementById("fileList");

const verifyButton =
    document.getElementById("verifyButton");

const processingCard =
    document.getElementById("processingCard");

const resultsCard =
    document.getElementById("resultsCard");

const errorMessage =
    document.getElementById("errorMessage");

let selectedFile = null;


/* FILE SELECTION */

browseBtn.addEventListener("click", () => {
    fileInput.click();
});


fileInput.addEventListener("change", () => {

    if (fileInput.files.length > 0) {

        setFile(fileInput.files[0]);

    }

});


/* DRAG AND DROP */

dropZone.addEventListener("dragover", (event) => {

    event.preventDefault();

    dropZone.classList.add("dragover");

});


dropZone.addEventListener("dragleave", () => {

    dropZone.classList.remove("dragover");

});


dropZone.addEventListener("drop", (event) => {

    event.preventDefault();

    dropZone.classList.remove("dragover");

    const file = event.dataTransfer.files[0];

    if (file) {
        setFile(file);
    }

});


function setFile(file) {

    if (!file.name.toLowerCase().endsWith(".pdf")) {

        showError("Please select a PDF file.");

        return;
    }

    selectedFile = file;

    fileList.innerHTML = `
        <div class="file-item">
            <span>📄 ${file.name}</span>
            <span>✓ Ready</span>
        </div>
    `;

    verifyButton.disabled = false;

    hideError();
}


/* VERIFY */

verifyButton.addEventListener("click", async () => {

    if (!selectedFile) {
        return;
    }

    const customerId =
        document.getElementById("customerId").value;

    const documentType =
        document.getElementById("documentType").value;


    if (!customerId) {

        showError("Please enter a customer ID.");

        return;
    }


    /* UI STATE */

    verifyButton.disabled = true;

    resultsCard.classList.add("hidden");

    processingCard.classList.remove("hidden");

    hideError();


    resetSteps();


    try {

        /*
         * Show live processing stages
         */

        setStep("stepUpload", "active");

        await delay(400);

        setStep("stepUpload", "complete");

        setStep("stepExtract", "active");

        await delay(600);

        setStep("stepExtract", "complete");

        setStep("stepDatabase", "active");

        await delay(500);

        setStep("stepDatabase", "complete");

        setStep("stepVerify", "active");


        /* BUILD REQUEST */

        const formData = new FormData();

        formData.append(
            "document_type",
            documentType
        );

        formData.append(
            "file",
            selectedFile
        );


        /* CALL BACKEND */

        /* STEP 1: UPLOAD DOCUMENT */

const uploadResponse = await fetch(
    `${API_URL}/kyc/upload/${customerId}`,
    {
        method: "POST",
        body: formData
    }
);

if (!uploadResponse.ok) {

    const errorText =
        await uploadResponse.text();

    throw new Error(
        errorText || "Document upload failed."
    );
}

const uploadData =
    await uploadResponse.json();

const documentId =
    uploadData.document_id;


/* DOCUMENT UPLOADED */

setStep("stepUpload", "complete");

setStep("stepExtract", "active");

await delay(500);

setStep("stepExtract", "complete");

setStep("stepDatabase", "active");

await delay(400);

setStep("stepDatabase", "complete");

setStep("stepVerify", "active");


/* STEP 2: VERIFY DOCUMENT */

const verifyResponse = await fetch(
    `${API_URL}/kyc/verify/${customerId}/${documentId}`,
    {
        method: "POST",
        headers: {
            "Accept": "application/json"
        }
    }
);

if (!verifyResponse.ok) {

    const errorText =
        await verifyResponse.text();

    throw new Error(
        errorText || "KYC verification failed."
    );
}

const data =
    await verifyResponse.json();


/* VERIFICATION COMPLETE */

setStep("stepVerify", "complete");

setStep("stepAI", "active");

await delay(700);

setStep("stepAI", "complete");


/* SHOW RESULT */

displayResults(data);


        setStep("stepVerify", "complete");

        setStep("stepAI", "active");

        await delay(700);

        setStep("stepAI", "complete");


        /* SHOW RESULT */

        displayResults(data);


    } catch (error) {

        showError(
            "Verification failed: " + error.message
        );

    } finally {

        verifyButton.disabled = false;

    }

});


/* STEP CONTROL */

function setStep(id, state) {

    const step = document.getElementById(id);

    step.classList.remove(
        "active",
        "complete"
    );

    const icon =
        step.querySelector(".step-icon");


    if (state === "active") {

        step.classList.add("active");

        icon.textContent = "●";

    }

    if (state === "complete") {

        step.classList.add("complete");

        icon.textContent = "✓";

    }

}


function resetSteps() {

    document.querySelectorAll(".step")
        .forEach(step => {

            step.classList.remove(
                "active",
                "complete"
            );

            step.querySelector(
                ".step-icon"
            ).textContent = "○";

        });

}


/* DISPLAY RESULT */

function displayResults(data) {

    const verification = data.verification;

    resultsCard.classList.remove("hidden");


    /*
     * Determine document type
     */

    const documentType =
        document.getElementById("documentType").value;


    /*
     * Name
     */

    setMatch(
        "nameResult",
        verification.name_match
    );


    /*
     * Address
     */

    setMatch(
        "addressResult",
        verification.address_match
    );


    /*
     * Document-specific fields
     */

    const dobValidation =
        document.getElementById("dobValidation");

    const panValidation =
        document.getElementById("panValidation");

    const identityLabel =
        document.getElementById("identityLabel");


    if (documentType === "PAN") {

        // Show DOB
        dobValidation.style.display = "flex";

        // Show PAN
        panValidation.style.display = "flex";

        identityLabel.textContent = "PAN";

        setMatch(
            "dobResult",
            verification.dob_match
        );

        setMatch(
            "panResult",
            verification.pan_match
        );

    }

    else if (documentType === "AADHAAR") {

        // Show DOB
        dobValidation.style.display = "flex";

        // Show Aadhaar
        panValidation.style.display = "flex";

        identityLabel.textContent = "Aadhaar";

        setMatch(
            "dobResult",
            verification.dob_match
        );

        setMatch(
            "panResult",
            verification.aadhaar_match
        );

    }

    else if (
        documentType === "ADDRESS_PROOF"
    ) {

        // Hide DOB
        dobValidation.style.display = "none";

        // Hide PAN/Aadhaar
        panValidation.style.display = "none";

    }


    /*
     * Risk score
     */

    const score =
        verification.risk_score;

    document.getElementById(
        "riskScore"
    ).textContent = score;

    document.getElementById(
        "riskBar"
    ).style.width =
        Math.min(score, 100) + "%";


    /*
     * Final status
     */

    const badge =
        document.getElementById("resultBadge");

    const status =
        verification.final_status;

    badge.textContent = status;

    badge.className = "badge";


    if (status === "VERIFIED") {

        badge.classList.add("verified");

    }

    else if (
        status === "MANUAL REVIEW"
    ) {

        badge.classList.add("review");

    }

    else {

        badge.classList.add("rejected");

    }


 
    /* AI */

    document.getElementById(
        "aiExplanation"
    ).textContent =
        data.ai_explanation || verification.reason;

}


function setMatch(elementId, matched) {

    const element =
        document.getElementById(elementId);

    if (matched) {

        element.textContent = "✓ MATCH";

        element.style.color = "#16a34a";

    } else {

        element.textContent = "✗ MISMATCH";

        element.style.color = "#dc2626";

    }

}


/* HELPERS */

function delay(ms) {

    return new Promise(
        resolve => setTimeout(resolve, ms)
    );

}


function showError(message) {

    errorMessage.textContent = message;

    errorMessage.classList.remove(
        "hidden"
    );

}


function hideError() {

    errorMessage.classList.add(
        "hidden"
    );

}
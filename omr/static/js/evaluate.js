document.addEventListener("DOMContentLoaded", function () {
    // For multiple sheet files
    function handleMultiFileList(input, listId) {
        const list = document.getElementById(listId);
        list.innerHTML = "";

        Array.from(input.files).forEach((file, index) => {
            const li = document.createElement("li");
            li.textContent = file.name + " ";

            const removeBtn = document.createElement("span");
            removeBtn.textContent = "✖";
            removeBtn.style.cursor = "pointer";
            removeBtn.style.color = "red";
            removeBtn.onclick = function () {
                const dt = new DataTransfer();
                Array.from(input.files)
                    .filter((_, i) => i !== index)
                    .forEach((f) => dt.items.add(f));
                input.files = dt.files;
                handleMultiFileList(input, listId);
            };

            li.appendChild(removeBtn);
            list.appendChild(li);
        });
    }

    // For single answer file
    function handleSingleFile(input, listId) {
        const list = document.getElementById(listId);
        list.innerHTML = "";

        if (input.files.length > 0) {
            const file = input.files[0];
            const li = document.createElement("li");
            li.textContent = file.name + " ";

            const removeBtn = document.createElement("span");
            removeBtn.textContent = "✖";
            removeBtn.style.cursor = "pointer";
            removeBtn.style.color = "red";
            removeBtn.onclick = function () {
                input.value = ""; // reset file input
                list.innerHTML = "";
            };

            li.appendChild(removeBtn);
            list.appendChild(li);
        }
    }

    document.getElementById("sheet_upload").addEventListener("change", function () {
        handleMultiFileList(this, "sheetList");
    });

    document.getElementById("answer_upload").addEventListener("change", function () {
        handleSingleFile(this, "answerList");
    });
});

const processButton = document.getElementById("process-button");
document.getElementById("process-form").addEventListener("submit", async function (event) {
    event.preventDefault(); // stop normal submit

    // submit button ux
    processButton.disabled = true;
    processButton.textContent = "Processing...";

    const form = document.getElementById("process-form");
    const formData = new FormData();

    // Add regular inputs (text/date/radio etc.)
    new FormData(form).forEach((value, key) => {
        if (key !== "sheet_files" && key !== "answer_file") {
            formData.append(key, value);
        }
    });

    // Add multiple sheet files
    const sheetInput = document.getElementById("sheet_upload");
    Array.from(sheetInput.files).forEach((file) => {
        formData.append("sheet_files", file);
    });

    // Add single answer file
    const answerInput = document.getElementById("answer_upload");
    if (answerInput.files.length > 0) {
        formData.append("answer_file", answerInput.files[0]);
    }

    // Send request
    const response = await fetch("{% url 'process_ajax' %}", {
        method: "POST",
        headers: {
            "X-CSRFToken": "{{ csrf_token }}",
        },
        body: formData,
    });

    // --- Streaming response handling ---
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    function handleData(data) {
        // progress bar
        if (data.progress !== undefined) {
            const bar = document.getElementById("progress-bar");
            if (bar) {
                bar.style.width = data.progress + "%";
                bar.innerText = data.progress + "%";
            }
        }

        // results
        if (data.exam_id) {
            const resultsDiv = document.getElementById("results");
            if (resultsDiv) {
                resultsDiv.style.display = "block";
                resultsDiv.innerHTML = `
                                <p>Processing completed successfully!</p>
                                <a href="/results/${data.exam_id}/" class="btn btn-primary">
                                    View Results
                                </a>
                            `;
            }
        }
        console.log("Chunk received:", data);
    }

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        let parts = buffer.split("\n");
        buffer = parts.pop();

        for (let part of parts) {
            if (!part.trim()) continue;
            try {
                const data = JSON.parse(part);
                handleData(data);
            } catch (e) {
                console.error("Failed to parse chunk:", part, e);
            }
        }
    }

    if (buffer.trim()) {
        try {
            const data = JSON.parse(buffer);
            handleData(data);
        } catch (e) {
            console.error("Failed to parse leftover:", buffer, e);
        }
    }

    processButton.disabled = false;
    processButton.textContent = "Process Sheets";
});

// --- Preview handling ---
const previewButtons = document.querySelectorAll(".preview-btn");
const overlay = document.getElementById("previewOverlay");
const previewImage = document.getElementById("previewImage");
const closeBtn = document.getElementById("closePreview");

previewButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
        const imgSrc = btn.getAttribute("data-img");
        previewImage.src = imgSrc;
        overlay.style.display = "flex";
    });
});

closeBtn.addEventListener("click", () => {
    overlay.style.display = "none";
    previewImage.src = "";
});

overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
        overlay.style.display = "none";
        previewImage.src = "";
    }
});

// --- Default exam date ---
const today = new Date().toISOString().split("T")[0];
document.getElementById("dateInput").value = today;

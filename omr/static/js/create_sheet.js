// --- Template preview overlay ---
const templateOverlay = document.getElementById("templateOverlay");
const templatePreviewImage = document.getElementById("templatePreviewImage");
const closeTemplatePreview = document.getElementById("closeTemplatePreview");

document.querySelectorAll(".preview-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        templatePreviewImage.src = btn.dataset.img;
        templateOverlay.style.display = "flex";
    });
});

closeTemplatePreview.addEventListener("click", () => {
    templateOverlay.style.display = "none";
    templatePreviewImage.src = "";
});

templateOverlay.addEventListener("click", (e) => {
    if (e.target === templateOverlay) {
        templateOverlay.style.display = "none";
        templatePreviewImage.src = "";
    }
});

// --- Default exam date ---
const today = new Date().toISOString().split("T")[0];
document.getElementById("exam-date").value = today;

// --- Generated sheet preview overlay ---
const form = document.querySelector("form");
const overlay = document.getElementById("sheetOverlay");
const preview = document.getElementById("sheetPreview");
const closeBtn = document.getElementById("closeSheetPreview");
const downloadBtn = document.getElementById("download-btn");

// Generate Preview
form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const res = await fetch("", {
        method: "POST",
        body: formData,
        headers: { "X-Requested-With": "XMLHttpRequest" }, // marks as AJAX
    });

    const contentType = res.headers.get("content-type");

    if (contentType && contentType.includes("application/pdf")) {
        // 🟢 In case backend ever returns a PDF
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "generated_sheet.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } else {
        // 🟢 Normal preview JSON response
        const data = await res.json();

        const imgSrc = "data:image/png;base64," + data.image_data;
        preview.src = imgSrc;
        overlay.style.display = "flex";
    }
});

// Close preview overlay
closeBtn.addEventListener("click", () => {
    overlay.style.display = "none";
    preview.src = "";
});

overlay.addEventListener("click", (e) => {
    if (e.target === overlay) {
        overlay.style.display = "none";
        preview.src = "";
    }
});

// 🔵 Download last generated sheet
downloadBtn.addEventListener("click", async () => {
    try {
        const res = await fetch("{% url 'sheet_download' %}");
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "exam_sheet.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();

        URL.revokeObjectURL(url);
    } catch (err) {
        console.error("Download failed:", err);
        alert("⚠️ Failed to download the sheet. Try generating it again.");
    }
});

// Handle "Download Template" buttons
document.querySelectorAll(".download-template-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
        const templateId = btn.dataset.template;

        // Optionally collect other form data if needed
        const form = document.getElementById("sheet-form");
        const formData = new FormData(form);
        formData.set("sheet_template", templateId);

        try {
            const response = await fetch("", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) throw new Error("Failed to generate sheet");

            // If backend sends a direct PDF file
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = `${templateId}_sheet.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error(err);
            alert("Error downloading sheet. Please try again.");
        }
    });
});

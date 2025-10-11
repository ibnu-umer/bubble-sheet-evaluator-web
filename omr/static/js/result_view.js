// --- Sheet preview overlay ---
const sheetOverlay = document.getElementById("sheetOverlay");
const sheetPreviewImage = document.getElementById("sheetPreviewImage");
const closeSheetPreview = document.getElementById("closeSheetPreview");

document.querySelectorAll(".preview-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        sheetPreviewImage.src = btn.dataset.img;
        sheetOverlay.style.display = "flex";
    });
});

closeSheetPreview.addEventListener("click", () => {
    sheetOverlay.style.display = "none";
    sheetPreviewImage.src = "";
});

sheetOverlay.addEventListener("click", (e) => {
    if (e.target === sheetOverlay) {
        sheetOverlay.style.display = "none";
        sheetPreviewImage.src = "";
    }
});




const examID = "{{ exam.exam_id|safe }}";
const examName = "{{ exam.exam_name|safe }}";
const examNameLower = examName.toLowerCase().replace(/\s+/g, "_");

document.getElementById("download-pdf-btn").addEventListener("click", async function (event) {
    event.preventDefault();
    let btn = this;
    btn.textContent = "Downloading...";
    btn.disabled = true;

    try {
        const response = await fetch("{% url 'download_sheet_pdf' %}", {
            method: "POST",
            headers: {
                "X-CSRFToken": "{{ csrf_token }}",
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ exam_id: examID }),
        });

        if (!response.ok) throw new Error("Failed to generate PDF");

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `${examNameLower}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url);
    } catch (err) {
        console.error("Error:", err);
        alert("Failed to download PDF. Please try again.");
    }

    setTimeout(() => {
        btn.textContent = "Download Sheet PDF";
        btn.disabled = false;
    }, 3000);
});

// Function to export table to CSV
function downloadTableCSV(filename) {
    let btn = document.getElementById("download-csv-btn");
    btn.textContent = "Downloading...";
    btn.disabled = true;

    let csv = [];
    let rows = document.querySelectorAll("#result-table tr");

    for (let row of rows) {
        let cols = row.querySelectorAll("td, th");
        let rowData = [];
        for (let col of cols) {
            rowData.push(col.innerText);
        }
        csv.push(rowData.join(","));
    }

    let csvFile = new Blob([csv.join("\n")], { type: "text/csv" });
    let downloadLink = document.createElement("a");
    downloadLink.download = filename;
    downloadLink.href = URL.createObjectURL(csvFile);
    downloadLink.click();

    setTimeout(() => {
        btn.textContent = "Download CSV";
        btn.disabled = false;
    }, 2000);
}

// Function to export table to Excel
function downloadTableExcel(filename) {
    let btn = document.getElementById("download-xlsx-btn");
    btn.textContent = "Downloading...";
    btn.disabled = true;

    let table = document.getElementById("result-table");
    let wb = XLSX.utils.table_to_book(table, { sheet: "Results" });
    XLSX.writeFile(wb, filename, { bookType: "xlsx", type: "binary" });

    setTimeout(() => {
        btn.textContent = "Download Excel";
        btn.disabled = false;
    }, 2000);
}

// Event Listeners
document.getElementById("download-csv-btn").addEventListener("click", function () {
    downloadTableCSV(examNameLower + ".csv");
});

document.getElementById("download-xlsx-btn").addEventListener("click", function () {
    downloadTableExcel(examNameLower + ".xlsx");
});

// Submit error table data
const exam_id = "{{ exam.exam_id|safe }}";
document.addEventListener("DOMContentLoaded", function () {
    const buttons = document.querySelectorAll(".submit-btn");

    buttons.forEach((btn) => {
        btn.addEventListener("click", function () {
            const row = btn.closest("tr");
            const roll_no = row.querySelector(".rollno-input").value;
            const score = row.querySelector(".score-input").value;

            if (!roll_no || !score) {
                alert("Please fill roll number and mark first.");
                return;
            }

            const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

            fetch("{% url 'submit_mark' %}", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": csrfToken,
                },
                body: new URLSearchParams({
                    roll_no: roll_no,
                    score: Number(score),
                    exam_id: exam_id,
                }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        const tableBody = document.querySelector("#result-table tbody");
                        let existingRow = Array.from(tableBody.rows).find(
                            (row) => row.cells[0].textContent === roll_no
                        );
                        if (existingRow) {
                            alert(`Roll No: ${roll_no} already exists`);
                        } else {
                            updateResultTable(roll_no, score);
                            btn.textContent = "✅ Saved";
                            btn.disabled = true;
                        }
                    }
                })
                .catch((err) => {
                    alert("Server error: " + err);
                });
        });
    });
});

const passMark = Number("{{ exam.pass_mark|safe }}");
function updateResultTable(roll_no, score) {
    const tableBody = document.querySelector("#result-table tbody");
    const newRow = document.createElement("tr");

    newRow.innerHTML = `
                    <td>${roll_no}</td>
                    <td>${score}</td>
                    <td>${score >= passMark ? "Pass" : "Fail"}</td>
                `;
    tableBody.appendChild(newRow);
}

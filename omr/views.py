from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadedFileForm
from .models import UploadedFile
from .processing.pdf_utils import pdf_to_images, ensure_dir
from .processing.evaluator import process_sheet, save_results_to_csv, load_answers
from .constants import RESULT_IMG_PATH, CONVERTED_IMG_PATH
import os



def upload_file(request):
    if request.method == 'POST':
        form = UploadedFileForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save()
            messages.success(request, f"Uploaded: {instance.file.name}")
            return redirect('upload_file')
        else:
            messages.error(request, "Upload failed. Fix the errors below.")
    else:
        form = UploadedFileForm()

    recent = UploadedFile.objects.order_by('-uploaded_at')[:20]
    return render(request, 'uploads.html', {'form': form, 'recent': recent})



def evaluate(request, pdf_path, answer_key_path):
    """
    End-to-end pipeline to process OMR sheets from a PDF.

    Steps:
        1. Converts PDF pages to images.
        2. Extracts student data (e.g., roll number) from QR codes on each sheet.
        3. Ensures the result images directory exists.
        4. Iterates through each converted sheet and processes answers.
        5. Aggregates results for all students and saves them into a CSV file.

    Args:
        pdf_path (str): Path to the input PDF containing scanned OMR sheets.

    Returns:
        str: File path of the generated results CSV.
    """
    students_data = pdf_to_images(pdf_path)
    ensure_dir(RESULT_IMG_PATH)
    sheet_files = os.listdir(CONVERTED_IMG_PATH)

    final_results = []
    answer_keys = load_answers(answer_key_path)
    for student_data, sheet_file in zip(students_data, sheet_files):

        final_results.append(process_sheet(sheet_file, student_data, answer_keys))
    save_results_to_csv(final_results) # result sheet path

    return render(request, "evaluate.html")


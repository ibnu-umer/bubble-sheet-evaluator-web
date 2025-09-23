from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadedFileForm
from .models import UploadedFile
from .processing.pdf_utils import pdf_to_images
from .processing.evaluator import process_sheet
from .constants import RESULT_IMG_PATH, CONVERTED_IMG_PATH
import os
from django.http import StreamingHttpResponse, JsonResponse
import json



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



def process_ajax(request):
    print(request.POST)
    if request.method == "POST":
        sheet_files = request.POST.getlist("sheet_files")
        print("****", sheet_files)
        answer_file = request.POST.get("answer_file")
        print(sheet_files, answer_file)

        def stream():
            students_data = pdf_to_images(sheet_files[0])  # only taking first file for testing
            sheet_files_local = os.listdir(CONVERTED_IMG_PATH)

            final_results = []
            total = len(sheet_files_local)

            for i, (student_data, sheet_file) in enumerate(zip(students_data, sheet_files_local), 1):
                print(i)
                result = process_sheet(sheet_file, student_data, answer_keys=None)
                final_results.append(result)

                progress = int((i / total) * 100)
                yield json.dumps({"progress": progress}) + "\n"

            # send results at the end
            yield json.dumps({"results": final_results}) + "\n"

        return StreamingHttpResponse(stream(), content_type="application/json")

    return JsonResponse({"error": "Invalid request"}, status=400)

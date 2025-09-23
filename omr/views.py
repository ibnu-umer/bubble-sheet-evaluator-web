from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadedFileForm
from .models import UploadedFile
from .processing.pdf_utils import pdf_to_images
from .processing.evaluator import process_sheet
from .constants import RESULT_IMG_PATH, CONVERTED_IMG_PATH
import os
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
import json
from django.core.cache import cache
import uuid
from django.urls import reverse



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
    if request.method == "POST":
        sheet_files = request.POST.getlist("sheet_files")
        answer_file = request.POST.get("answer_file")

        def stream():
            students_data = pdf_to_images(sheet_files[0])  # only taking first file for testing
            sheet_files_local = os.listdir(CONVERTED_IMG_PATH)

            final_results = []
            task_id = str(uuid.uuid4())
            total = len(sheet_files_local)

            for i, (student_data, sheet_file) in enumerate(zip(students_data, sheet_files_local), 1):
                result = process_sheet(sheet_file, student_data, answer_keys=None)
                final_results.append(result)

                progress = int((i / total) * 100)
                yield json.dumps({"progress": progress}) + "\n"

            # Save results temporarily (10 min)
            cache.set(task_id, final_results, timeout=600)

            # send results_id instead of redirect_url
            yield json.dumps({
                "results_id": task_id
            }) + "\n"

        return StreamingHttpResponse(stream(), content_type="application/json")

    return JsonResponse({"error": "Invalid request"}, status=400)





def results_view(request, task_id):
    results = cache.get(str(task_id))
    if not results:
        return HttpResponse("No results found or expired", status=404)

    return render(request, "results.html", {"results": results})


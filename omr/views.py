from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadedFileForm
from .models import UploadedFile
from django.conf import settings
from .processing.pdf_utils import pdf_to_images
from .processing.evaluator import process_sheet, load_answers
from .constants import *
import os
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
import json
from django.core.cache import cache
import uuid



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
        exam_name = request.POST.get("examName")

        converted_img_path = CONVERTED_IMG_PATH.format(exam_name)
        evaluated_img_path = EVALUATED_IMG_PATH.format(exam_name)

        def stream():
            final_results = []
            task_id = str(uuid.uuid4())
            answer_keys = load_answers(answer_file)

            # Collect all students_data from all PDFs
            all_students_data = []
            all_sheet_files = []

            for sheet_file in sheet_files:
                students_data = pdf_to_images(
                    sheet_file,
                    save_path=converted_img_path,
                    dpi=PDF_DPI,
                    poppler_path=POPPLER_PATH
                )
                sheet_files_local = os.listdir(converted_img_path)

                # Match each image/student with its file
                all_students_data.extend(students_data)
                all_sheet_files.extend(sheet_files_local)

            total = len(all_students_data)
            errored_files = []

            # Process each sheet
            for i, (student_data, sheet_file) in enumerate(zip(all_students_data, all_sheet_files), 1):
                result = process_sheet(
                    sheet_file, student_data,
                    answer_keys=answer_keys,
                    converted_folder=converted_img_path,
                    evaluated_folder=evaluated_img_path,
                    thresh=MEAN_INTENSITY_THRESHOLD,
                    options=OPTIONS
                )
                if type(result) == str:
                    errored_files.append(result)
                else:
                    final_results.append(result)

                # Stream progress update
                progress = int((i / total) * 100)
                yield json.dumps({"progress": progress}) + "\n"

            os.removedirs(converted_img_path)
            # Save results temporarily (10 min)
            cache.set(
                task_id,
                {"results": final_results, "errors": errored_files, "examName": exam_name},
                timeout=600
            )

            # Send results_id at the end
            yield json.dumps({"results_id": task_id}) + "\n"

        return StreamingHttpResponse(stream(), content_type="application/json")

    return JsonResponse({"error": "Invalid request"}, status=400)






def results_view(request, task_id):
    cached_data = cache.get(str(task_id))
    exam_name = cached_data.get("examName", "Examination").upper

    if cached_data:
        final_results = cached_data.get("results", [])
        errored_files = cached_data.get("errors", [])
    else:
        final_results = []
        errored_files = []

    if not final_results:
        return HttpResponse("No results found or expired", status=404)

    # add status to the final results
    for result in final_results:
        result["status"] = "Pass" if result.get("score") > PASS_MARK else "Fail"

    return render(request, "results.html", {
        "results": final_results,
        "error": errored_files,
        "examName": exam_name
    })


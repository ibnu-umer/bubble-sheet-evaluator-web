from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadForm
from .models import UploadLog
from django.conf import settings
from .processing.pdf_utils import pdf_to_images
from .processing.evaluator import process_sheet, load_answers
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from .constants import *
import os
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
import json
from django.core.cache import cache
import uuid
from PIL import Image, ImageDraw, ImageFont
from django.utils.timezone import now
from .models import Exam, Result
import random
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from io import BytesIO
from reportlab.pdfgen import canvas







def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("evaluator")
    else:
        form = UserCreationForm()
    return render(request, "signup.html", {"form": form})





@login_required
def evaluator(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            sheet_file = form.cleaned_data.get("answer_sheets")
            key_file = form.cleaned_data.get("answer_key")

            if sheet_file:
                UploadLog.objects.create(filename=sheet_file.name, filetype="sheet")
                messages.success(request, f"Processed answer sheet: {sheet_file.name}")

            if key_file:
                UploadLog.objects.create(filename=key_file.name, filetype="key")
                messages.success(request, f"Processed answer key: {key_file.name}")

            return redirect("evaluator")
        else:
            messages.error(request, "Upload failed. Fix the errors below.")
    else:
        form = UploadForm()

    recent = UploadLog.objects.order_by('-uploaded_at')[:20]
    exams = request.user.exams.all().order_by('-exam_date')
    return render(request, 'evaluate.html', {'form': form, 'recent': recent, 'exams': exams})



@login_required
def process_ajax(request):
    if request.method == "POST":
        template = request.POST.get("sheet_template")
        sheet_files = request.FILES.getlist("sheet_files")
        answer_file = request.FILES.get("answer_file")
        exam_name = request.POST.get("exam_name")
        org_name = request.POST.get("org_name")
        subject = request.POST.get("subject")
        pass_mark = request.POST.get("pass_mark")
        exam_date = request.POST.get("exam_date")
        exam_id = str(uuid.uuid4())

        exam = Exam.objects.create(
            exam_name=exam_name,
            org_name=org_name,
            exam_date=exam_date,
            sheet_template=template,
            exam_id=exam_id,
            subject=subject,
            pass_mark=pass_mark,
            user=request.user
        )

        converted_img_path = CONVERTED_IMG_PATH.format(exam_name.lower().replace(" ", "_"))
        evaluated_img_path = EVALUATED_IMG_PATH.format(exam_name.lower().replace(" ", "_"))

        def stream():
            final_results = []
            answer_keys = load_answers(answer_file)
            template_config = TEMPLATE_CONFIG.get(template)

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
                result, answers  = process_sheet(
                    sheet_file, student_data,
                    answer_keys=answer_keys,
                    converted_folder=converted_img_path,
                    evaluated_folder=evaluated_img_path,
                    thresh=MEAN_INTENSITY_THRESHOLD,
                    options=OPTIONS[:template_config.get("options")],
                )
                if not answers:
                    errored_files.append(result)

                # save results
                result, _ = Result.objects.update_or_create(
                    exam=exam,
                    roll_no=result['roll'],
                    defaults={
                        "answers": answers,
                        "score": result['score'],
                    }
                )

                # Stream progress update
                progress = int((i / total) * 100)
                yield json.dumps({"progress": progress}) + "\n"

            os.removedirs(converted_img_path)
            # Save results temporarily (10 min)
            cache.set(
                exam_id,
                {
                    #! Handle errored files
                    "errors": errored_files
                },
                timeout=600
            )

            # Send results_id at the end
            yield json.dumps({"exam_id": exam_id}) + "\n"

        return StreamingHttpResponse(stream(), content_type="application/json")

    return JsonResponse({"error": "Invalid request"}, status=400)



@login_required
def results_view(request, exam_id):
    exam = Exam.objects.get(exam_id=exam_id)
    results = Result.objects.filter(exam=exam)

    return render(request, "results.html", {
        "exam": exam,
        "results": results
    })



@csrf_protect
def download_sheet_pdf(request):
    if request.method != "POST":
        return HttpResponse("Invalid request", status=400)

    try:
        body = json.loads(request.body.decode("utf-8"))
        exam_name = body.get("examName", f"exam_{now().strftime('%Y%m%d')}")  # default: current date
        file_name = exam_name.lower().replace(" ", "_")
        image_folder = EVALUATED_IMG_PATH.format(file_name)

        # Collect image paths
        image_paths = [
            os.path.join(image_folder, f)
            for f in os.listdir(image_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        if not image_paths:
            return HttpResponse("No images found", status=404)

        # Build PDF in memory
        buffer = BytesIO()

        # Create cover page with exam name
        width, height = 2480, 3508
        cover = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(cover)
        try:
            font = ImageFont.truetype("arial.ttf", 120)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), exam_name, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) / 2
        y = (height - text_height) / 2
        draw.text((x, y), exam_name, fill="black", font=font)

        # Convert rest of the sheets
        pil_images = [Image.open(path).convert("RGB") for path in image_paths]

        # Save all pages into BytesIO instead of disk
        cover.save(buffer, format="PDF", save_all=True, append_images=pil_images)
        buffer.seek(0)

        # Return as downloadable file
        response = HttpResponse(buffer, content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="{file_name}.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)

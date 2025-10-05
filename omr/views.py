from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadForm
from .models import UploadLog
from django.conf import settings
from .processing.pdf_utils import pdf_to_images
from .processing.evaluator import process_sheet, load_answers, cv2_to_base64
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

        def stream():
            answer_keys = load_answers(answer_file)
            template_config = TEMPLATE_CONFIG.get(template)
            sheet_images = []

            # Convert PDF sheets into PNG
            for sheet_file in sheet_files:
                sheet_images.extend(pdf_to_images(
                        sheet_file,
                        dpi=PDF_DPI,
                        poppler_path=POPPLER_PATH
                    )
                )

            errored_sheets = []
            num_of_sheets = len(sheet_images)

            # Process each sheet
            for i, sheet in enumerate(sheet_images, start=1):
                result_image, result, roll_no  = process_sheet(
                    sheet,
                    answer_keys=answer_keys,
                    thresh=MEAN_INTENSITY_THRESHOLD,
                    options=OPTIONS[:template_config.get("options")],
                )
                if not result:
                    errored_sheets.append(cv2_to_base64(result_image))
                else:
                    result, _ = Result.objects.update_or_create(
                        exam=exam,
                        roll_no=roll_no,
                        defaults={
                            "answers": result['answers'],
                            "score": result['score'],
                        }
                    )

                # Stream progress update
                progress = int((i / num_of_sheets * 100))
                yield json.dumps({"progress": progress}) + "\n"

            # Save data in cache temperarily (10 min)
            cache.set(
                exam_id,
                {
                    "errored_sheets": errored_sheets
                },
                timeout=600
            )

            yield json.dumps({"exam_id": exam_id}) + "\n"

        return StreamingHttpResponse(stream(), content_type="application/json")

    return JsonResponse({"error": "Invalid request"}, status=400)



@login_required
def results_view(request, exam_id):
    exam = Exam.objects.get(exam_id=exam_id)
    results = Result.objects.filter(exam=exam)
    try:
        cached_data = cache.get(exam_id)
        errored_sheets = cached_data.get("errored_sheets")
    except Exception as err:
        print(f"error: {err}")
        errored_sheets = []

    return render(request, "results.html", {
        "exam": exam,
        "results": results,
        "errored_sheets": errored_sheets
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



@login_required
def submit_mark(request):
    if request.method == "POST":
        rollno = request.POST.get("rollno")
        mark = request.POST.get("mark")

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request"})

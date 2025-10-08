from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import UploadForm
from .models import UploadLog
from django.conf import settings
from .processing.pdf_utils import pdf_to_images, create_cover_page, edit_answer_sheet
from .processing.evaluator import process_sheet, load_answers, get_exam_folder_name
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from .constants import *
import os, fitz
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
import json
from django.core.cache import cache
import uuid
from PIL import Image, ImageDraw, ImageFont
from django.utils.timezone import now
from .models import Exam, Result, Errors
import random
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from io import BytesIO
from reportlab.pdfgen import canvas
import cv2
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from datetime import datetime





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

    context = {
        'form': form,
        'recent': UploadLog.objects.order_by('-uploaded_at')[:20],
        'exams': request.user.exams.all().order_by('-exam_date'),
        'templates': list(TEMPLATE_CONFIG.keys())
    }
    return render(request, 'evaluate.html', context)



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

        exam, _ = Exam.objects.get_or_create(
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

            num_of_sheets = len(sheet_images)
            file_name = get_exam_folder_name(exam_name)

            # Create or check if the exam folders are exist in the media
            eval_path = EVALUATED_SHEET_PATH.format(file_name)
            os.makedirs(eval_path, exist_ok=True)
            err_path = ERRORED_SHEET_PATH.format(file_name)
            os.makedirs(err_path, exist_ok=True)

            # Process each sheet
            for i, sheet in enumerate(sheet_images, start=1):
                result_image, result, roll_no  = process_sheet(
                    sheet,
                    answer_keys=answer_keys,
                    thresh=MEAN_INTENSITY_THRESHOLD,
                    options=OPTIONS[:template_config.get("options")],
                )
                _, buffer = cv2.imencode('.png', result_image)
                image_file = ContentFile(buffer.tobytes(), name=f'{exam.id}-{roll_no}.png')

                if result:
                    Result.objects.update_or_create(
                        exam=exam,
                        roll_no=roll_no,
                        defaults={
                            "answers": result['answers'],
                            "score": result['score'],
                            "sheet": image_file
                        }
                    )
                else:
                    Errors.objects.update_or_create(
                        exam=exam,
                        defaults={
                            "sheet": image_file,
                            "reason": result,
                        }
                    )

                # Stream progress update
                progress = int((i / num_of_sheets * 100))
                yield json.dumps({"progress": progress}) + "\n"

            yield json.dumps({"exam_id": exam_id}) + "\n"

        return StreamingHttpResponse(stream(), content_type="application/json")

    return JsonResponse({"error": "Invalid request"}, status=400)



@login_required
def results_view(request, exam_id):
    exam = get_object_or_404(Exam, exam_id=exam_id)
    results = Result.objects.filter(exam=exam)
    errors = Errors.objects.filter(exam=exam)

    return render(request, "results.html", {
        "exam": exam,
        "results": results,
        "errors": errors
    })



@csrf_protect
def download_sheet_pdf(request):
    if request.method != "POST":
        return HttpResponse("Invalid request", status=400)

    try:
        body = json.loads(request.body.decode("utf-8"))
        exam_id = body.get("exam_id")
        exam = get_object_or_404(Exam, exam_id=exam_id)
        results = Result.objects.filter(exam=exam)
        image_paths = [res.sheet.path for res in results]

        if not image_paths:
            return HttpResponse("No evaluated sheets found for this exam.", status=404)

        # Build PDF in memory
        buffer = BytesIO()
        pil_images = [Image.open(path).convert("RGB") for path in image_paths]

        cover = create_cover_page(exam.exam_name)
        cover.save(buffer, format="PDF", save_all=True, append_images=pil_images)
        buffer.seek(0)

        # Return as downloadable file
        file_name = get_exam_folder_name(exam.exam_name)
        response = HttpResponse(buffer, content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="{file_name}.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)



@login_required
def submit_mark(request):
    if request.method == "POST":
        roll_no = request.POST.get("roll_no")
        score = request.POST.get("score")
        exam_id = request.POST.get("exam_id")

        exam = get_object_or_404(Exam, exam_id=exam_id)
        Result.objects.update_or_create(
            exam=exam,
            roll_no=roll_no,
            defaults={
                "answers": {},
                "score": score,
            }
        )

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": "Invalid request"})



@csrf_protect
def sheet_edit(request):
    if request.method == "POST":
        template = request.POST.get("sheet_template")
        exam_name = request.POST.get("exam_name")
        instr1 = request.POST.get("instruction_1")
        instr2 = request.POST.get("instruction_2")
        instr3 = request.POST.get("instruction_3")
        exam_date = datetime.strptime(request.POST.get("exam_date"), "%Y-%m-%d").strftime("%d-%m-%Y")
        exam_hour = request.POST.get("exam_hour")
        exam_min = request.POST.get("exam_min")

        context = {
            "template": template,
            "exam_name": exam_name,
            "instructions": [instr1, instr2, instr3],
            "exam_date": exam_date,
            "exam_time": f"{exam_hour}h {exam_min}m ",
        }

        #! TODO: Edit the template with the given values.
        template_path = os.path.join(settings.STATIC_ROOT, f"answer_sheet_template.pdf")
        output = edit_answer_sheet(template_path, context)
        response = HttpResponse(output.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{get_exam_folder_name(exam_name)}_sheet.pdf"'
        return response

    templates = list(TEMPLATE_CONFIG.keys())
    return render(request, "sheet_edit.html", {"templates": templates})


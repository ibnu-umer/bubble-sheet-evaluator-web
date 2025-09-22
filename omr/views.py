from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadedFileForm
from .models import UploadedFile



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

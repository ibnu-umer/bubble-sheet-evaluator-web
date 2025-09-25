from django.urls import path
from . import views

urlpatterns = [
    path('', views.evaluator, name='evaluator'),
    path('process_ajax/', views.process_ajax, name='process_ajax'),
    path("results/<uuid:task_id>/", views.results_view, name="results_page"),
    path("convert-to-pdf/", views.convert_to_pdf, name="convert_to_pdf")
]

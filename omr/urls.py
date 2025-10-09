from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # auth
    path('accounts/login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path("accounts/signup/", views.signup, name="signup"),
    path('accounts/logout/', views.logout_view, name='logout'),

    path('exam/evaluator/', views.evaluator, name='evaluator'),
    path('exam/process_ajax/', views.process_ajax, name='process_ajax'),
    path('exam/results/', views.results_page, name="results_page"),
    path("exam/results/<uuid:exam_id>/", views.result_view, name="result_view"),
    path("convert-to-pdf/", views.download_sheet_pdf, name="download_sheet_pdf"),
    path('submit_mark/', views.submit_mark, name='submit_mark'),
    path('sheet/create/', views.create_sheet, name='create_sheet'),
    path('sheet/download/', views.sheet_download, name='sheet_download')
]

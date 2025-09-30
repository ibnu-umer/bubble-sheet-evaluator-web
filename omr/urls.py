from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # auth
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path("accounts/signup/", views.signup, name="signup"),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    path('evaluator/', views.evaluator, name='evaluator'),
    path('process_ajax/', views.process_ajax, name='process_ajax'),
    path("results/<uuid:exam_id>/", views.results_view, name="results_page"),
    path("convert-to-pdf/", views.convert_to_pdf, name="convert_to_pdf"),
]

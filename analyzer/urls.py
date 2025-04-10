from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('result/<int:resume_id>/', views.result, name='result'),
    path('templates/', views.browse_templates, name='browse_templates'),
    path('template/download/<int:template_id>/', views.download_template, name='download_template'),
]
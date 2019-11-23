from django.contrib import admin
from django.urls import path, re_path, include
from .views import CreateAppointmentView

urlpatterns = [
  path('', CreateAppointmentView.as_view(), name="appointment-create")
]
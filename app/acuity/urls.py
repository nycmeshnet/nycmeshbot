from django.contrib import admin
from django.urls import path
from .views import CreateAppointmentView

urlpatterns = [
    # Webhook endpoint for Acuity
    path('', CreateAppointmentView.as_view(), name="appointment-create")
]

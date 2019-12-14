from django.contrib import admin
from django.urls import path
from .views import InteractionComponentView

urlpatterns = [
    # Webhook endpoint for Slack Interactive Components
    path('interactive', InteractionComponentView.as_view(), name="slackcmd-interactive")
]

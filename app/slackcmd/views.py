import logging

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import status
from django.conf import settings


class InteractionComponentView(generics.CreateAPIView):

    def post(self, request, *args, **kwargs):
        return Response(
            status=status.HTTP_200_OK
        )

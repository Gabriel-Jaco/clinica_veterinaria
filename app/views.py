from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .mixins import GrupoRequeridoMixin


class IndexView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "index.html")

    def post(self, request):
        pass


class ClienteView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, "cliente.html")

    def post(self, request):
        pass
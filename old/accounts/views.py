import logging

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import SignUpForm

logger = logging.getLogger(__name__)

class SignUpView(CreateView):
    form_class    = SignUpForm
    template_name = "registration/signup.html"
    success_url   = reverse_lazy("dashboard")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("dashboard")

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    http_method_names = ["get", "post"]

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("home")
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        logger.debug("CustomLogoutView.get called: user=%r", request.user)
        return super().post(request, *args, **kwargs)

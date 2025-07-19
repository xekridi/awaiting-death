from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import SignUpForm

class SignUpView(CreateView):
    form_class    = SignUpForm
    template_name = "registration/signup.html"
    success_url   = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    http_method_names = ["get", "post"]

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("home")
    http_method_names = ["get", "post"]
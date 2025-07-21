from django.urls import path
from .views import signup, CustomLoginView, CustomLogoutView

urlpatterns = [
    path("signup/", signup, name="signup"),
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", CustomLogoutView.as_view(), name="logout"),
]

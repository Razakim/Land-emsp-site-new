from django.urls import path

from .views import AccountLogoutView, LoginView, PasswordChangeView, RegisterView

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("password-change/", PasswordChangeView.as_view(), name="password_change"),
    path("logout/", AccountLogoutView.as_view(), name="logout"),
]

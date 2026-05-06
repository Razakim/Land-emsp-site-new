from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import FormView


class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = AuthenticationForm
    success_url = reverse_lazy("administration:dashboard")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Nom utilisateur"})
        form.fields["password"].widget.attrs.update({"class": "form-control", "placeholder": "Mot de passe"})
        return form

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect(self.request.GET.get("next") or self.success_url)


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("administration:dashboard")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["username"].widget.attrs.update({"class": "form-control", "placeholder": "Ex: akone"})
        form.fields["password1"].widget.attrs.update({"class": "form-control", "placeholder": "Mot de passe"})
        form.fields["password2"].widget.attrs.update({"class": "form-control", "placeholder": "Confirmation"})
        return form

    def form_valid(self, form):
        user = form.save(commit=False)
        user.email = self.request.POST.get("email", "").strip().lower()
        user.first_name = self.request.POST.get("first_name", "").strip()
        user.last_name = self.request.POST.get("last_name", "").strip()
        user.is_staff = True
        user.save()
        Group.objects.get_or_create(name="Administration")[0].user_set.add(user)
        login(self.request, user)
        messages.success(self.request, "Compte administrateur cree avec succes.")
        return redirect(self.request.GET.get("next") or self.success_url)


class PasswordChangeView(LoginRequiredMixin, FormView):
    template_name = "accounts/password_change.html"
    form_class = PasswordChangeForm
    success_url = reverse_lazy("administration:profil_admin")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({"class": "form-control"})
        return form

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, "Mot de passe modifie avec succes.")
        return super().form_valid(form)


class AccountLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("core:home")

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

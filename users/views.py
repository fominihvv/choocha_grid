from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView
from social_core.utils import first

from choocha import settings
from notes.mixins import send_notification_email
from users.forms import LoginUserForm, RegisterUserForm, ProfileUserForm, UserPasswordChangeForm


@login_required
def logout_user(request):
    logout(request)
    return HttpResponseRedirect(reverse('home'))


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'users/login.html'
    extra_context = {'title': "Авторизация"}
    pass


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'users/register.html'
    extra_context = {'title': "Регистрация"}
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):

        context_notification = {
            'subject': "Зарегистрирован новый пользователь",
            'message': f"""
                Зарегистрирован новый пользователь

                Логин: {form.cleaned_data['username']}
                Email: {form.cleaned_data['email'],}
                Имя: {form.cleaned_data['first_name']}
                Фамилия: {form.cleaned_data['last_name']}
            """,
            'additional': {
            }
        }

        send_notification_email(
            request=self.request,
            context=context_notification,
        )
        return super().form_valid(form)


class ProfileUser(LoginRequiredMixin, UpdateView):
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    extra_context = {'title': "Профиль пользователя"}

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('users:profile')


class UserPasswordChange(LoginRequiredMixin, PasswordChangeView):
    form_class = UserPasswordChangeForm
    template_name = 'users/password_change_form.html'
    success_url = reverse_lazy('users:password_change_done')
    extra_context = {'title': "Смена пароля"}

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):

        context_notification = {
            'subject': f"Попытка сброса пароля для пользователя {form.cleaned_data['username']}",
            'message': f"""
                Попытка сброса пароля для пользователя {form.cleaned_data['username']}

                Логин: {form.cleaned_data['username']}
                Email: {form.cleaned_data['email'],}
                Имя: {form.cleaned_data['first_name']}
                Фамилия: {form.cleaned_data['last_name']}
            """,
            'additional': {
            }
        }

        send_notification_email(
            request=self.request,
            context=context_notification,
        )
        return super().form_valid(form)

class UserPasswordResetConfirm:
    pass
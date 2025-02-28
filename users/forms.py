from datetime import datetime

from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.utils.translation import gettext_lazy

class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-input'}))

    class Meta:
        model = get_user_model()
        fields = ['username', 'password']


class RegisterUserForm(UserCreationForm):
    username = forms.CharField(label="Логин", widget=forms.TextInput(attrs={'class': 'form-input'}))
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    captcha = CaptchaField()

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        labels = {
            'email': 'Email',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }

        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError(gettext_lazy('Пользователь с таким email уже существует'))
        return email



class ProfileUserForm(forms.ModelForm):
    username = forms.CharField(
        disabled=True,
        label=gettext_lazy("Логин"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.CharField(
        disabled=True,
        required=False,
        label=gettext_lazy("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    this_year = datetime.now().year
    date_birth = forms.DateField(
        label=gettext_lazy("Дата рождения"),
        widget=forms.SelectDateWidget(years=range(this_year - 100, this_year - 18)),
        help_text=gettext_lazy("Введите дату Вашего рождения.")
    )

    class Meta:
        model = get_user_model()
        fields = ['photo', 'username', 'email', 'date_birth', 'first_name', 'last_name']
        labels = {
            'first_name': gettext_lazy("Имя"),
            'last_name': gettext_lazy("Фамилия"),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Валидация общих ошибок формы
        if self.errors:
            raise forms.ValidationError(gettext_lazy('Пожалуйста, исправьте ошибки в форме.'))
        return cleaned_data

class UserPasswordChangeForm(LoginRequiredMixin, PasswordChangeForm):
    old_password = forms.CharField(label="Старый пароль", widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    new_password1 = forms.CharField(label="Новый пароль", widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    new_password2 = forms.CharField(label="Повторите новый пароль", widget=forms.PasswordInput(attrs={'class': 'form-input'}))


from django import forms
# from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.deconstruct import deconstructible
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import Category, Note
from string import ascii_letters, digits


@deconstructible
class LettersAnDigitsValidator:
    ALLOWED_CHARACTERS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ123456789- " + digits + ascii_letters
    code = 'russian'

    def __init__(self, message=None):
        self.message = message if message else 'Должны присутствовать только буквы, цифры, дефис и пробел'

    def __call__(self, value, *args, **kwargs):
        if not (set(value) <= set(self.ALLOWED_CHARACTERS)):
            raise forms.ValidationError(self.message, code=self.code)


class AddPostForm(forms.ModelForm):
    cat = forms.ModelChoiceField(queryset=Category.objects.all(), label="Категория", empty_label="Категория не выбрана")

    class Meta:
        model = Note
        fields = ['title', 'content_short', 'content_full', 'image', 'is_published', 'cat', 'tags', 'meta_description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
        }
        # validators = {
        #    'title': LettersAnDigitsValidator(),
        # }
        # labels = {
        #    'title': 'Заголовок',
        # }

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы под Bootstrap
        """
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})

        self.fields['content_short'].widget.attrs.update({'class': 'form-control django_ckeditor_5'})
        self.fields['content_short'].required = False
        self.fields['content_full'].widget.attrs.update({'class': 'form-control django_ckeditor_5'})
        self.fields['content_full'].required = False


    # def clean_title(self):
    #     allowed_characters = "абвгдеёжзий̆клмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ123456789- "
    #     title = self.cleaned_data['title']
    #     if not set(title).issubset(set(allowed_characters)):
    #         raise forms.ValidationError('Должны присутствовать только русские буквы, цифры, дефис и пробел. V2')
    #     return title

class UpdatePostForm(forms.ModelForm):
    cat = forms.ModelChoiceField(queryset=Category.objects.all(), label="Категория", empty_label="Категория не выбрана")

    class Meta:
        model = Note
        fields = ['title', 'content_short', 'content_full', 'image', 'is_published', 'cat', 'tags', 'meta_description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})

        self.fields['content_short'].widget.attrs.update({'class': 'form-control django_ckeditor_5'})
        self.fields['content_short'].required = False
        self.fields['content_full'].widget.attrs.update({'class': 'form-control django_ckeditor_5'})
        self.fields['content_full'].required = False

class UploadFileForm(forms.Form):
    file = forms.ImageField(label="Файл")

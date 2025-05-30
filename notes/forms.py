from string import ascii_letters, digits

from captcha.fields import CaptchaField
from django import forms
# from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils.deconstruct import deconstructible
from django.utils.html import strip_tags

from .models import Category, Note, Comment


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
        fields = ['title', 'content_short', 'content_full', 'image', 'status', 'cat', 'tags', 'meta_description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
        }
        # validators = {
        #    'title': LettersAnDigitsValidator(),
        # }
        # labels = {
        #    'title': 'Заголовок',
        # }

    def __init__(self, *args, **kwargs) -> None:
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

    def clean_content_short(self) -> str:
        content = self.cleaned_data['content_short']
        print(len(strip_tags(content)))
        print(content)
        if content and len(strip_tags(content)) > 600:
            raise forms.ValidationError("Превышен лимит в 600 символов")
        return content


class UpdatePostForm(forms.ModelForm):
    cat = forms.ModelChoiceField(queryset=Category.objects.all(), label="Категория", empty_label="Категория не выбрана")

    class Meta:
        model = Note
        fields = ['title', 'content_short', 'content_full', 'image', 'status', 'cat', 'tags', 'meta_description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'autocomplete': 'off'})

        self.fields['content_short'].widget.attrs.update({'class': 'form-control django_ckeditor_5'})
        self.fields['content_short'].required = False
        self.fields['content_full'].widget.attrs.update({'class': 'form-control django_ckeditor_5'})
        self.fields['content_full'].required = False


class UploadFileForm(forms.Form):
    file = forms.ImageField(label="Файл")


class ContactForm(forms.Form):
    name = forms.CharField(
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    email = forms.CharField(
        required=False,
        label='E-mail',
        widget=forms.TextInput(attrs={'class': 'form-input'})
    )
    content = forms.CharField(
        label="Сообщение",
        widget=forms.Textarea(attrs={'rows': 3}),
        max_length=3000
    )
    captcha = CaptchaField()

    def __init__(self, *args, **kwargs) -> None:
        user = kwargs.pop('user', None)
        super(ContactForm, self).__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields['name'].initial = user.username
            self.fields['name'].widget.attrs['disabled'] = True  # Отключаем поле
            self.fields['name'].required = False
            self.fields['email'].initial = user.email
            self.fields['email'].widget.attrs['disabled'] = True  # Отключаем поле
            self.fields['email'].required = False

            # Добавляем скрытые поля для передачи данных на сервер
            self.fields['name_hidden'] = forms.CharField(
                initial=user.username,
                widget=forms.HiddenInput()
            )
            self.fields['email_hidden'] = forms.EmailField(
                initial=user.email,
                widget=forms.HiddenInput()
            )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']  # Только поле для текста комментария
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-textarea',
                'placeholder': 'Ваш комментарий...'
            }),
        }

    def __init__(self, *args, **kwargs) -> None:
        self.user = kwargs.pop('user', None)  # Передаём пользователя из view
        self.post = kwargs.pop('post', None)  # Передаём пост из view
        super().__init__(*args, **kwargs)

        # Если пользователь авторизован, скрываем ненужные поля
        if self.user and self.user.is_authenticated:
            self.fields['body'].label = ''  # Убираем label

        # Добавляем скрытое поле post_id, если пост передан
        if self.post:
            self.fields['post'] = forms.CharField(
                initial=self.post.id,
                widget=forms.HiddenInput()
            )

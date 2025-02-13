from typing import Any

from bs4 import BeautifulSoup
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, CreateView, DeleteView, UpdateView, FormView

from choocha import settings
from .forms import AddPostForm, UpdatePostForm, ContactForm
from .models import Note, TagPost, Category
from .utils import DataMixin


class NoteHome(DataMixin, ListView):
    template_name = 'notes/index.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        return Note.published.all().select_related('cat', 'author')

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['page_description'] = 'Домашняя страница'
        context['page_description_name'] = 'description'
        return self.get_mixin_context(context, title='Главная страница', cat_selected=0)


class ShowPost(DataMixin, DetailView):
    # model = Notes #Не использовать этот способ, если определен get_queryset
    template_name = 'notes/show_post.html'
    slug_url_kwarg = 'post_slug'
    context_object_name = 'post'

    def get_queryset(self) -> QuerySet:
        return Note.published.all().select_related('cat', 'author')

    def get_object(self, queryset: QuerySet = None) -> QuerySet:
        return get_object_or_404(queryset or self.get_queryset(), slug=self.kwargs[self.slug_url_kwarg])

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        post = context['post']  # получаем пост из контекста
        if post.meta_description and post.meta_description.strip():
            context['page_description'] = post.meta_description
        else:
            soup = BeautifulSoup(post.content_short, features="html5lib")  # Используем lxml для обработки HTML
            clean_text = soup.get_text(strip=True)  # Извлекаем текст и убираем лишние пробелы
            context['page_description'] = clean_text[:160]
            context['page_description_name'] = 'description'
        return self.get_mixin_context(context, title=context['post'].title)


class NotesCategory(DataMixin, ListView):
    template_name = 'notes/index.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        return Note.published.filter(cat__slug=self.kwargs['cat_slug']).select_related('cat', 'author')

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(Category, slug=self.kwargs['cat_slug'])
        context['page_description'] = f'Все статьи из категории {category.name}'
        context['page_description_name'] = 'description'
        return self.get_mixin_context(context, cat_selected=category.pk, title='Категория: ' + category.name)


class NotesTags(DataMixin, ListView):
    template_name = 'notes/index.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        return Note.published.filter(tags__slug=self.kwargs['tag_slug']).select_related('cat', 'author')

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        tag = get_object_or_404(TagPost, slug=self.kwargs['tag_slug'])
        context['page_description'] = f'Все статьи с тэгом {tag.tag}'
        context['page_description_name'] = 'description'
        return self.get_mixin_context(context, title='Тег: ' + tag.tag)


class AddPost(PermissionRequiredMixin, DataMixin, CreateView):
    template_name = 'notes/add_post.html'
    form_class = AddPostForm
    success_url = reverse_lazy('home')
    login_url = reverse_lazy('home')
    permission_required = ('notes.add_note',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_description'] = 'noindex, nofollow'
        context['page_description_name'] = 'robots'
        return self.get_mixin_context(context, title_page='Добавление статьи')

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        return super().form_valid(form)


class DeletePost(PermissionRequiredMixin, DataMixin, DeleteView):
    model = Note
    template_name = 'notes/delete_post.html'
    context_object_name = 'post'
    success_url = reverse_lazy('home')
    login_url = reverse_lazy('home')
    permission_required = ('notes.delete_note',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_description'] = 'noindex, nofollow'
        context['page_description_name'] = 'robots'
        return self.get_mixin_context(context, title_page='Удаление статьи')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.author == self.request.user or self.request.user.is_superuser or self.request.user.is_staff:
            return obj
        else:
            raise PermissionDenied("You can't delete this post.")


class UpdatePost(PermissionRequiredMixin, DataMixin, UpdateView):
    template_name = 'notes/update_post.html'
    form_class = UpdatePostForm
    success_url = reverse_lazy('home')  # Если не указывать, то идёт редирект на саму статью используя get_absolute_url
    login_url = reverse_lazy('home')
    permission_required = ('notes.change_note',)
    context_object_name = 'post'

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Note.objects.all()  # Администраторы видят все статьи
        return Note.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_description'] = 'noindex, nofollow'
        context['page_description_name'] = 'robots'
        return self.get_mixin_context(context, title_page='Редактирование статьи')

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        return super().form_valid(form)


class AboutView(DataMixin, TemplateView):
    template_name = 'notes/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_description'] = 'О сайте'
        context['page_description_name'] = 'description'
        return self.get_mixin_context(context, title_page='О сайте')


class ContactView(DataMixin, FormView):
    form_class = ContactForm
    success_url = reverse_lazy('home')
    template_name = "notes/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_description'] = 'Обратная связь'
        context['page_description_name'] = 'description'
        return self.get_mixin_context(context, title_page='Обратная связь')

    def form_valid(self, form):
        # Если пользователь аутентифицирован, используем данные из скрытых полей
        if self.request.user.is_authenticated:
            name = form.cleaned_data['name_hidden']
            email = form.cleaned_data['email_hidden']
        else:
            # Получаем данные из формы
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']

        content = form.cleaned_data['content']

        # Формируем тему и текст письма
        subject = f"Новое сообщение от {name}"
        message = f"""
        Имя: {name}
        Email: {email}
        Сообщение:
        {content}
        """
        # Отправляем письмо
        try:
            send_mail(
                subject,  # Тема письма
                message,  # Текст письма
                settings.DEFAULT_FROM_EMAIL,  # От кого (ваш email из настроек)
                [settings.EMAIL_ADMIN],  # Кому (ваш email из настроек)
                fail_silently=False,  # Выводить ошибки, если отправка не удалась
            )
            # Добавляем сообщение об успехе
            messages.success(self.request, 'Ваше сообщение успешно отправлено!')
        except Exception as e:
            # Добавляем сообщение об ошибке
            messages.error(self.request, f'Ошибка при отправке письма: {e}')

        return super().form_valid(form)

    def form_invalid(self, form):
        # Восстанавливаем значения полей name и email из скрытых полей
        if self.request.user.is_authenticated:
            form.data = form.data.copy()  # Делаем копию данных формы
            form.data['name'] = form.data.get('name_hidden', '')
            form.data['email'] = form.data.get('email_hidden', '')
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

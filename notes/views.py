from typing import Any

from bs4 import BeautifulSoup
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, CreateView, DeleteView, UpdateView

from .forms import AddPostForm, UpdatePostForm
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
        return Note.published.all()

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
        return Note.published.filter(cat__slug=self.kwargs['cat_slug']).select_related('cat')

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
        return Note.published.filter(tags__slug=self.kwargs['tag_slug']).select_related('cat')

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
        if not (obj.author == self.request.user and not self.request.user.is_superuser and not self.request.user.is_staff):
            raise PermissionDenied("You can't delete this post.")
        return obj

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


class ContactView(DataMixin, TemplateView):
    template_name = "notes/contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_description'] = 'Обратная связь'
        context['page_description_name'] = 'description'
        return self.get_mixin_context(context, title_page='Обратная связь')

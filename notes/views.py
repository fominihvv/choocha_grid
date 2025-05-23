from typing import Any

from bs4 import BeautifulSoup
from django.contrib import messages
from django.contrib.auth.mixins import (
    PermissionRequiredMixin,
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import View
from django.views.generic import (
    TemplateView,
    ListView,
    DetailView,
    CreateView,
    DeleteView,
    UpdateView,
    FormView,
)

from .forms import AddPostForm, UpdatePostForm, ContactForm, CommentForm
from .models import Note, TagPost, Category, Comment
from .utils import DataMixin, send_notification_email


###################################
#           Общий блок            #
###################################


class NoteHome(DataMixin, ListView):
    template_name = "notes/index.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        return Note.published.all().select_related("cat", "author")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_description"] = "Домашняя страница"
        context["page_description_name"] = "description"
        return self.get_mixin_context(context, title="Главная страница", cat_selected=0)


class AboutView(DataMixin, TemplateView):
    template_name = "notes/about.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_description"] = "О сайте"
        context["page_description_name"] = "description"
        return self.get_mixin_context(context, title_page="О сайте")


class ContactView(DataMixin, FormView):
    form_class = ContactForm
    success_url = reverse_lazy("home")
    template_name = "notes/contact.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_description"] = "Обратная связь"
        context["page_description_name"] = "description"
        return self.get_mixin_context(context, title_page="Обратная связь")

    def form_valid(self, form):
        # Если пользователь аутентифицирован, используем данные из скрытых полей
        if self.request.user.is_authenticated:
            name = form.cleaned_data["name_hidden"]
            email = form.cleaned_data["email_hidden"]
        else:
            # Получаем данные из формы
            name = form.cleaned_data["name"]
            email = form.cleaned_data["email"]

        context_notification = {
            "subject": "Сообщение из формы обратной связи",
            "message": f"""
                Сообщение из формы обратной связи

                Автор: {name}
                Email: {email}
                Текст: {form.cleaned_data['content']}
                """,
            "additional": {},
        }

        send_notification_email(
            request=self.request,
            context=context_notification,
            alert=True,
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        # Восстанавливаем значения полей name и email из скрытых полей
        if self.request.user.is_authenticated:
            form.data = form.data.copy()  # Делаем копию данных формы
            form.data["name"] = form.data.get("name_hidden", "")
            form.data["email"] = form.data.get("email_hidden", "")
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


###############################
# Блок для работы со статьями #
###############################


class ShowPost(DataMixin, DetailView):
    """Отображение статьи"""

    # model = Notes #Не использовать этот способ, если определен get_queryset
    template_name = "notes/show_post.html"
    slug_url_kwarg = "post_slug"
    context_object_name = "post"

    def get_queryset(self) -> QuerySet:
        return (
            Note.published.all()
            .select_related("cat", "author")
            .prefetch_related("post_comments", "post_comments__user")
        )

    def get_object(self, queryset: QuerySet = None) -> QuerySet:
        return get_object_or_404(
            queryset or self.get_queryset(), slug=self.kwargs[self.slug_url_kwarg]
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        post = context["post"]  # получаем пост из контекста
        if post.meta_description and post.meta_description.strip():
            context["page_description"] = post.meta_description
        else:
            soup = BeautifulSoup(
                post.content_short, features="html5lib"
            )  # Используем lxml для обработки HTML
            clean_text = soup.get_text(
                strip=True
            )  # Извлекаем текст и убираем лишние пробелы
            context["page_description"] = clean_text[:160]
            context["page_description_name"] = "description"

        context["comment_form"] = CommentForm()
        return self.get_mixin_context(context, title=context["post"].title)


class NotesCategory(DataMixin, ListView):
    """Вывод статей по определённой категории"""

    template_name = "notes/index.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        return Note.published.filter(cat__slug=self.kwargs["cat_slug"]).select_related(
            "cat", "author"
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(Category, slug=self.kwargs["cat_slug"])
        context["page_description"] = f"Все статьи из категории {category.name}"
        context["page_description_name"] = "description"
        return self.get_mixin_context(
            context, cat_selected=category.pk, title="Категория: " + category.name
        )


class NotesTags(DataMixin, ListView):
    """Вывод статей по определённому тэгу"""

    template_name = "notes/index.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        return Note.published.filter(tags__slug=self.kwargs["tag_slug"]).select_related(
            "cat", "author"
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        tag = get_object_or_404(TagPost, slug=self.kwargs["tag_slug"])
        context["page_description"] = f"Все статьи с тэгом {tag.tag}"
        context["page_description_name"] = "description"
        return self.get_mixin_context(context, title="Тег: " + tag.tag)


class AddPost(PermissionRequiredMixin, DataMixin, CreateView):
    template_name = "notes/add_post.html"
    form_class = AddPostForm
    success_url = reverse_lazy("home")
    login_url = reverse_lazy("users:login")
    permission_required = ("notes.add_note",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_description"] = "noindex, nofollow"
        context["page_description_name"] = "robots"
        return self.get_mixin_context(context, title_page="Добавление статьи")

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        return super().form_valid(form)


class DeletePost(PermissionRequiredMixin, DataMixin, DeleteView):
    model = Note
    template_name = "notes/delete_post.html"
    context_object_name = "post"
    success_url = reverse_lazy("home")
    login_url = reverse_lazy("users:login")
    permission_required = ("notes.delete_note",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_description"] = "noindex, nofollow"
        context["page_description_name"] = "robots"
        return self.get_mixin_context(context, title_page="Удаление статьи")

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if (
            obj.author == self.request.user
            or self.request.user.is_superuser
            or self.request.user.is_staff
        ):
            return obj
        else:
            raise PermissionDenied("У вас нет прав на удаление статьи")


class UpdatePost(PermissionRequiredMixin, DataMixin, UpdateView):
    template_name = "notes/update_post.html"
    form_class = UpdatePostForm
    success_url = reverse_lazy(
        "home"
    )  # Если не указывать, то идёт редирект на саму статью используя get_absolute_url
    login_url = reverse_lazy("users:login")
    permission_required = ("notes.change_note",)
    context_object_name = "post"

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Note.objects.all()  # Администраторы видят все статьи
        return Note.objects.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_description"] = "noindex, nofollow"
        context["page_description_name"] = "robots"
        return self.get_mixin_context(context, title_page="Редактирование статьи")

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        return super().form_valid(form)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if (
            obj.author == self.request.user
            or self.request.user.is_superuser
            or self.request.user.is_staff
        ):
            return obj
        else:
            raise PermissionDenied("У вас нет прав на редактирование статьи")


###################################
# Блок для работы с комментариями #
###################################


class CommentMixin:
    """Общая логика для работы с комментариями"""

    def _get_comment_notification_context(self, form, action):
        """Формирование контекста для уведомлений"""
        return {
            "subject": f"Комментарий {action}",
            "message": f"""
            Комментарий {action}

            Автор: {form.instance.user.username or '-'}
            Пост: {form.instance.post.title}
            Текст: {form.cleaned_data['body'][:200]}{'...' if len(form.cleaned_data['body']) > 200 else ''}
            """,
            "additional": {
                "post_url": self.request.build_absolute_uri(
                    reverse("post", kwargs={"post_slug": form.instance.post.slug})
                ),
                "full_text": form.cleaned_data["body"],
            },
        }

    @staticmethod
    def _handle_comment_status(form, request):
        """Обработка статуса комментария"""
        is_admin = request.user.is_staff or request.user.is_superuser
        if is_admin:
            form.instance.status = Comment.Status.ACTIVE
        messages.success(
            request,
            f'Комментарий {"добавлен" if is_admin else "отправлен на модерацию"}',
        )
        return is_admin


class AddCommentView(LoginRequiredMixin, CommentMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = "notes/show_post.html"  # Используем тот же шаблон

    def form_valid(self, form):
        request = self.request
        form.instance.user = request.user
        form.instance.post = Note.objects.get(slug=self.kwargs["post_slug"])

        is_admin = self._handle_comment_status(form, request)

        send_notification_email(
            request=self.request,
            context=self._get_comment_notification_context(
                form, "добавлен" if is_admin else "ожидает модерации"
            ),
        )

        return super().form_valid(form)

    def get_success_url(self):
        return (
            reverse_lazy("post", kwargs={"post_slug": self.object.post.slug})
            + f"#comment-{self.object.id}"
        )


class ApproveComment(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    @staticmethod
    def get(request, pk):
        comment = get_object_or_404(Comment, pk=pk)
        comment.active = True
        comment.save()
        messages.success(request, "Комментарий одобрен")
        return HttpResponseRedirect(
            reverse("post", kwargs={"post_slug": comment.post.slug})
            + f"#comment-{comment.id}"
        )


class DeleteComment(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = "notes/delete_comment.html"
    context_object_name = "comment"

    def get_success_url(self):
        return reverse_lazy("post", kwargs={"post_slug": self.object.post.slug})

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Проверяем права: автор, модератор или суперпользователь
        if (
            obj.user == self.request.user
            or self.request.user.is_staff
            or self.request.user.is_superuser
        ):
            return obj
        raise PermissionDenied("У вас нет прав на удаление этого комментария")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_description"] = "noindex, nofollow"
        context["page_description_name"] = "robots"
        context["title_page"] = "Удаление комментария"
        return context


class EditComment(LoginRequiredMixin, CommentMixin, UpdateView):
    model = Comment
    form_class = CommentForm  # Указываем форму для редактирования
    template_name = "notes/edit_comment.html"
    context_object_name = "comment"

    def get_success_url(self):
        # Добавляем якорь к комментарию для удобства
        return (
            reverse_lazy("post", kwargs={"post_slug": self.object.post.slug})
            + f"#comment-{self.object.id}"
        )

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Проверяем права: автор, модератор или суперпользователь
        if (
            obj.user == self.request.user
            or self.request.user.is_staff
            or self.request.user.is_superuser
        ):
            return obj

        raise PermissionDenied("У вас нет прав на редактирование этого комментария")

    def form_valid(self, form):
        # Автоматически обновляем дату редактирования
        form.instance.updated = timezone.now()

        is_admin = self._handle_comment_status(form, self.request)

        send_notification_email(
            request=self.request,
            context=self._get_comment_notification_context(form, "изменён"),
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "page_description": "noindex, nofollow",
                "page_description_name": "robots",
                "title_page": "Редактирование комментария",
                "post": self.object.post,  # Добавляем пост в контекст
            }
        )

        return context

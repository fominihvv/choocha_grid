from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin, UserPassesTestMixin
from django.db.models import QuerySet
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.html import escape
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, DeleteView, UpdateView, FormView
from redis import RedisError

from .forms import AddPostForm, UpdatePostForm, ContactForm, CommentForm
from .models import Note, TagPost, Category, Comment
from django.core.cache import cache
from .mixins import ObjectOwnershipMixin, CommentMixin,PaginationMixin, send_notification_email, AddPageDescriptionMixin


###################################
#           Общий блок            #
###################################

class IndexView(PaginationMixin, ListView):
    """
    Отображение основной страницы
    """
    template_name = "notes/index.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        return (
            Note.published.all()
            .select_related(
                "cat", "author"
            )
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Choocha.ru | Главная страница проекта",
            "page_description": "Choocha.ru | Главная страница проекта. Все статьи.",
            "cat_selected": 0,
            "content_type": 'website',
            "canonical_url": self.request.build_absolute_uri(reverse('home')),
        })
        context.update({
            "og_title": context["page_title"],
            "og_description": context["page_description"],
            "og_type": context["content_type"],
        })
        return self.get_paginator_context(context)


class AboutView(TemplateView):
    """
    Отображение страницы о проекте
    """
    template_name = "notes/about.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Choocha.ru | О сайте",
            "page_description": (
            "Данный сайт представляет собой полноценное веб-приложение, разработанное на Django"
            " с использованием современных DevOps-практик. Проект реализован как учебный, "
            "но с промышленным уровнем развертывания."),
            "article_title": "О сайте",
            "content_type": 'webpage',
            "canonical_url": self.request.build_absolute_uri(reverse('about')),
        })
        context.update({
            "og_title": context["page_title"],
            "og_description": context["page_description"],
            "og_type": context["content_type"],
        })
        return context


class ContactView(FormView):
    """
    Отображение страницы обратной связи
    """
    form_class = ContactForm
    success_url = reverse_lazy("home")
    template_name = "notes/contact.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Choocha.ru | Обратная связь",
            "page_description": "Choocha.ru | Обратная связь",
            "article_title": "Обратная связь",
            "content_type": 'webpage',
            "canonical_url": self.request.build_absolute_uri(reverse('contact')),
        })
        context.update({
            "og_title": context["page_title"],
            "og_description": context["page_description"],
            "og_type": context["content_type"],
        })
        return context

    def form_valid(self, form: ContactForm) -> HttpResponse:
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

    def form_invalid(self, form: ContactForm) -> HttpResponse:
        # Восстанавливаем значения полей name и email из скрытых полей
        if self.request.user.is_authenticated:
            form.data = form.data.copy()  # Делаем копию данных формы
            form.data["name"] = form.data.get("name_hidden", "")
            form.data["email"] = form.data.get("email_hidden", "")
        return super().form_invalid(form)

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


###############################
# Блок для работы со статьями #
###############################
class ShowPost(AddPageDescriptionMixin, DetailView):
    """
    Отображение статьи
    """
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
        escaped_post_title = escape(post.title.strip())

        context.update({
            "page_title": f"Choocha.ru | {escaped_post_title}" if post.title else "Choocha.ru | Статья без названия",
            "page_description": f"Просмотр статьи: {self.get_post_description(post)}",
            "article_title": escaped_post_title if post.title else "Статья без названия",
            "comment_form": CommentForm(),
            "content_type": 'article',
            "canonical_url": post.get_absolute_url(),
        })
        context.update({
            "og_title": context["page_title"],
            "og_description": context["page_description"],
            "og_type": context["content_type"],
        })
        return context


class ShowPostByCategory(PaginationMixin, ListView):
    """
    Вывод статей соответствующих указанной категории
    """

    template_name = "notes/index.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        """
        Возвращает список статей, соответствующих указанной категории.
        Данные сохраняются в Redis-кеше на один час.
        """
        try:
            return cache.get_or_set(
                f"notes:cat:{self.kwargs['cat_slug']}",
                lambda: Note.published.filter(cat__slug=self.kwargs["cat_slug"])
                .select_related(
                    "cat", "author"
                ),
                60 * 60 # Хранить в кеше 1 час
            )
        except RedisError:
            return (
                Note.published.filter(cat__slug=self.kwargs["cat_slug"])
                .select_related(
                    "cat", "author"
                )
            )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """
        Формирует контекст страницы с информацией о статье и категории.
        Проверяет наличие корректного slugs и производит переход, если обнаружено несоответствие.
        """
        context = super().get_context_data(**kwargs)
        slug = self.kwargs["cat_slug"]
        category = get_object_or_404(Category, slug=slug)

        # Если slug в URL не совпадает с текущим slug категории (например, после переименования)
        if category.slug != slug:
            return redirect('category', cat_slug=category.slug, permanent=True)

        # Формирование динамического контекста страницы
        context.update({
            "page_title": f"Choocha.ru | Статьи из категории {category.name}",
            "page_description": f"Все статьи из категории {category.name}",
            "article_title": f"Статьи из категории {category.name}",
            "content_type": "website",
            "canonical_url": self.request.build_absolute_uri(category.get_absolute_url()),
        })
        context.update({
            "og_title": context["page_title"],
            "og_description": context["page_description"],
            "og_type": context["content_type"],
        })
        return self.get_paginator_context(context)


class ShowPostByTag(PaginationMixin, ListView):
    """
    Вывод статей соответствующих определённому тегу
    """

    template_name = "notes/index.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        """
        Возвращает список статей, соответствующих указанному тегу.
        Данные сохраняются в Redis-кеше на один час.
        """
        try:
            return cache.get_or_set(
                f"notes:tag:{self.kwargs['tag_slug']}",
                lambda: Note.published.filter(tags__slug=self.kwargs["tag_slug"])
                .select_related("cat", "author")
                .prefetch_related("tags"),
                60 * 60  # Хранить в кеше 1 час
            )
        except RedisError:
            return (
                Note.published.filter(tags__slug=self.kwargs["tag_slug"])
                .select_related("cat", "author")
                .prefetch_related("tags")
            )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """
        Формирует контекст страницы с информацией о статье и теге.
        Проверяет наличие корректного slugs и производит переход, если обнаружено несоответствие.
        """
        context = super().get_context_data(**kwargs)
        slug = self.kwargs["tag_slug"]
        tag = get_object_or_404(TagPost, slug=slug)

        # Проверка корректности slug в URL
        if tag.slug != slug:
            return redirect('category', cat_slug=tag.slug, permanent=True)

        # Формирование динамического контекста страницы
        context.update({
            "page_title": f"Choocha.ru | Статьи с меткой {tag.name}",
            "page_description": f"Все статьи с меткой {tag.name}",
            "article_title": f"Статьи с меткой {tag.name}",
            "content_type": "website",
            "canonical_url": self.request.build_absolute_uri(tag.get_absolute_url()),
        })
        context.update({
            "og_title": context["page_title"],
            "og_description": context["page_description"],
            "og_type": context["content_type"],
        })
        return self.get_paginator_context(context)


class AddPost(PermissionRequiredMixin, CreateView):
    template_name = "notes/add_post.html"
    form_class = AddPostForm
    success_url = reverse_lazy("home")
    login_url = reverse_lazy("users:login")
    permission_required = ("notes.add_note",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "page_title": "Choocha.ru | Добавление новой статьи",
            "page_description": "Choocha.ru | Добавление новой статьи",
            "article_title": "Добавление статьи",
            "robots": 'noindex,nofollow',
        })
        return context

    def form_valid(self, form: AddPostForm) -> HttpResponse:
        post = form.save(commit=False)
        post.author = self.request.user
        return super().form_valid(form)


class DeletePost(ObjectOwnershipMixin, PermissionRequiredMixin, DeleteView):
    model = Note
    template_name = "notes/delete_post.html"
    context_object_name = "post"
    success_url = reverse_lazy("home")
    login_url = reverse_lazy("users:login")
    permission_required = ("notes.delete_note",)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        escaped_title = escape(self.object.title.strip())
        context.update({
            "page_title": f"Choocha.ru | Удаление статьи {escaped_title[:50]}…",
            "page_description": f"Удаление статьи {escaped_title[:100]}…",
            "article_title": "Удаление статьи",
            "robots": 'noindex,nofollow',
        })
        return context



class UpdatePost(ObjectOwnershipMixin, PermissionRequiredMixin, UpdateView):
    model = Note
    template_name = "notes/update_post.html"
    form_class = UpdatePostForm
    # Если не указывать, то идёт редирект на саму статью используя get_absolute_url
    # success_url = reverse_lazy("home")
    login_url = reverse_lazy("users:login")
    permission_required = ("notes.change_note",)
    context_object_name = "post"

    def form_valid(self, form: UpdatePostForm) -> HttpResponse:
        post = form.save(commit=False)
        post.author = self.request.user
        return super().form_valid(form)


    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        escaped_title = escape(self.object.title.strip())
        context.update({
            "page_title": f"Choocha.ru | Редактирование статьи {escaped_title[:50]}…",
            "page_description": f"Редактирование статьи {escaped_title[:100]}…",
            "article_title": "Редактирование статьи",
            "robots": 'noindex,nofollow',
        })
        return context


###################################
# Блок для работы с комментариями #
###################################

class AddCommentView(LoginRequiredMixin, CommentMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = "notes/show_post.html"  # Используем тот же шаблон

    def form_valid(self, form: CommentForm) -> HttpResponse:
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

    def get_success_url(self) -> str:
        return (
                reverse_lazy("post", kwargs={"post_slug": self.object.post.slug})
                + f"#comment-{self.object.id}"
        )


class ApproveComment(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self) -> bool:
        return self.request.user.is_staff or self.request.user.is_superuser

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        comment = get_object_or_404(Comment, pk=pk)
        comment.active = True
        comment.save()
        messages.success(request, "Комментарий одобрен")
        return HttpResponseRedirect(
            reverse("post", kwargs={"post_slug": comment.post.slug})
            + f"#comment-{comment.id}"
        )


class DeleteComment(ObjectOwnershipMixin, LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = "notes/delete_comment.html"
    context_object_name = "comment"

    def get_success_url(self) -> str:
        return reverse_lazy("post", kwargs={"post_slug": self.object.post.slug})


    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        escaped_text = escape(self.object.text.strip())
        context.update({
            "post": self.object.post,
            "page_title": f"Choocha.ru | Удаление комментария {escaped_text[:50]}…",
            "page_description": f"Удаление комментария {escaped_text[:100]}…",
            "article_title": "Удаление комментария",
            "robots": 'noindex,nofollow',
        })
        return context


class EditComment(ObjectOwnershipMixin, LoginRequiredMixin, CommentMixin, UpdateView):
    model = Comment
    form_class = CommentForm  # Указываем форму для редактирования
    template_name = "notes/edit_comment.html"
    context_object_name = "comment"

    def get_success_url(self) -> str:
        # Добавляем якорь к комментарию для удобства
        return (
                reverse_lazy("post", kwargs={"post_slug": self.object.post.slug})
                + f"#comment-{self.object.id}"
        )


    def form_valid(self, form: CommentForm) -> HttpResponse:
        # Автоматически обновляем дату редактирования
        form.instance.updated = timezone.now()

        self._handle_comment_status(form, self.request)

        send_notification_email(
            request=self.request,
            context=self._get_comment_notification_context(form, "изменён"),
        )

        return super().form_valid(form)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        escaped_text = escape(self.object.text.strip())
        context.update({
            "post": self.object.post,
            "page_title": f"Choocha.ru | Редактирование комментария {escaped_text[:50]}…",
            "page_description": f"Редактирование комментария {escaped_text[:100]}…",
            "article_title": "Редактирование комментария",
            "robots": 'noindex,nofollow',
        })
        return context

from typing import Any


from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, DeleteView, UpdateView, FormView
from .forms import AddPostForm, UpdatePostForm, ContactForm, CommentForm
from .models import Note, TagPost, Category, Comment
from .utils import PaginationMixin, send_notification_email, AddPageDescriptionMixin


###################################
#           Общий блок            #
###################################

class IndexView(PaginationMixin, ListView):
    template_name = "notes/index.html"
    context_object_name = "posts"
    paginate_by = 5

    def get_queryset(self) -> QuerySet:
        return Note.published.all().select_related("cat", "author")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "choocha.ru | Главная страница проекта"
        context["page_description"] = "choocha.ru | Главная страница проекта. Все статьи."
        context["cat_selected"] = 0
        context["content_type"] = 'website'
        context["canonical_url"] = self.request.build_absolute_uri(reverse('home'))
        context["og_title"] = context["page_title"]
        context["og_description"] = context["page_description"]
        context["og_type"] = context["content_type"]
        return self.get_paginator_context(context)


class AboutView(TemplateView):
    template_name = "notes/about.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "О сайте. Контакты. Ссылки."
        context["page_description"] = (
            "Данный сайт представляет собой полноценное веб-приложение, разработанное на Django"
            " с использованием современных DevOps-практик. Проект реализован как учебный, "
            "но с промышленным уровнем развертывания.")
        context["article_title"] = "О сайте"
        context["content_type"] = 'webpage'
        context["canonical_url"] = self.request.build_absolute_uri(reverse('about'))
        context["og_title"] = context["page_title"]
        context["og_description"] = context["page_description"]
        context["og_type"] = context["content_type"]
        return context


class ContactView(FormView):
    form_class = ContactForm
    success_url = reverse_lazy("home")
    template_name = "notes/contact.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Обратная связь"
        context["page_description"] = "Обратная связь"
        context["article_title"] = "Обратная связь"
        context["content_type"] = 'webpage'
        context["canonical_url"] = self.request.build_absolute_uri(reverse('contact'))
        context["og_title"] = context["page_title"]
        context["og_description"] = context["page_description"]
        context["og_type"] = context["content_type"]
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
        context["page_title"] = f"Choocha.ru | {post.title.strip()}" if post.title else "Choocha.ru | Статья без названия"
        context["page_description"] = f"Просмотр статьи: {self.get_post_description(post)}"
        context["article_title"] = post.title.strip() if post.title else "Статья без названия"
        context["comment_form"] = CommentForm()
        context["content_type"] = 'article'
        context["canonical_url"] = post.get_absolute_url()
        context["og_title"] = context["page_title"]
        context["og_description"] = context["page_description"]
        context["og_type"] = context["content_type"]
        return context


class ShowPostByCategory(PaginationMixin, ListView):
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
        slug = self.kwargs["cat_slug"]
        category = get_object_or_404(Category, slug=slug)

        # Если slug в URL не совпадает с текущим slug категории (например, после переименования)
        if category.slug != slug:
            return redirect('category', cat_slug=category.slug, permanent=True)

        context["page_title"] = "choocha.ru | Главная страница проекта"
        context["page_description"] = f"choocha.ru | Все статьи из категории {category.name}"
        context["article_title"] = f"Все статьи из категории {category.name}"
        context["cat_selected"] = category.pk
        context["content_type"] = 'website'
        context['canonical_url'] = self.request.build_absolute_uri(category.get_absolute_url())
        context["og_title"] = context["page_title"]
        context["og_description"] = context["page_description"]
        context["og_type"] = context["content_type"]
        return self.get_paginator_context(context)


class ShowPostByTag(PaginationMixin, ListView):
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
        slug = self.kwargs["tag_slug"]
        tag = get_object_or_404(TagPost, slug=slug)

        # Если slug в URL не совпадает с текущим slug категории (например, после переименования)
        if tag.slug != slug:
            return redirect('category', cat_slug=tag.slug, permanent=True)

        context["page_title"] = "choocha.ru | Главная страница проекта"
        context["page_description"] = f"choocha.ru | Все статьи с меткой {tag.tag}"
        context["article_title"] = f"Все статьи с меткой {tag.tag}"
        context["content_type"] = 'website'
        context['canonical_url'] = self.request.build_absolute_uri(tag.get_absolute_url())
        context["og_title"] = context["page_title"]
        context["og_description"] = context["page_description"]
        context["og_type"] = context["content_type"]
        return self.get_paginator_context(context)


class AddPost(PermissionRequiredMixin, CreateView):
    template_name = "notes/add_post.html"
    form_class = AddPostForm
    success_url = reverse_lazy("home")
    login_url = reverse_lazy("users:login")
    permission_required = ("notes.add_note",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "choocha.ru | Добавление новой статьи"
        context["article_title"] = "Добавление статьи"
        context["robots"] = 'noindex,nofollow'
        context["canonical_url"] = self.request.build_absolute_uri(reverse('add_post'))
        return context

    def form_valid(self, form: AddPostForm) -> HttpResponse:
        post = form.save(commit=False)
        post.author = self.request.user
        return super().form_valid(form)


class DeletePost(PermissionRequiredMixin, DeleteView):
    model = Note
    template_name = "notes/delete_post.html"
    context_object_name = "post"
    success_url = reverse_lazy("home")
    login_url = reverse_lazy("users:login")
    permission_required = ("notes.delete_note",)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        post = context["post"]
        context["page_title"] = f"choocha.ru | Удаление статьи {post.title.strip()}"
        context["article_title"] = "Удаление статьи"
        context["robots"] = 'noindex,nofollow'
        context["canonical_url"] = self.request.build_absolute_uri(
            reverse('delete_post', kwargs={'pk': self.get_object().pk})
        )
        return context

    def get_object(self, queryset: QuerySet = None) -> object:
        obj = super().get_object(queryset)
        if (
                obj.author == self.request.user
                or self.request.user.is_superuser
                or self.request.user.is_staff
        ):
            return obj
        else:
            raise PermissionDenied("У вас нет прав на удаление статьи")


class UpdatePost(PermissionRequiredMixin, UpdateView):
    template_name = "notes/update_post.html"
    form_class = UpdatePostForm
    success_url = reverse_lazy(
        "home"
    )  # Если не указывать, то идёт редирект на саму статью используя get_absolute_url
    login_url = reverse_lazy("users:login")
    permission_required = ("notes.change_note",)
    context_object_name = "post"

    def get_queryset(self) -> QuerySet:
        if self.request.user.is_superuser or self.request.user.is_staff:
            return Note.objects.all()  # Администраторы видят все статьи
        return Note.objects.filter(author=self.request.user)

    def form_valid(self, form: UpdatePostForm) -> HttpResponse:
        post = form.save(commit=False)
        post.author = self.request.user
        return super().form_valid(form)

    def get_object(self, queryset: QuerySet=None) -> object:
        obj = super().get_object(queryset)
        if (
                obj.author == self.request.user
                or self.request.user.is_superuser
                or self.request.user.is_staff
        ):
            return obj
        else:
            raise PermissionDenied("У вас нет прав на редактирование статьи")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        post = context["post"]  # получаем пост из контекста
        context["page_title"] = f"choocha.ru | Редактирование статьи: {post.title.strip()}"
        context["article_title"] = "Редактирование статьи"
        context["robots"] = 'noindex,nofollow'
        context["canonical_url"] = self.request.build_absolute_uri(
            reverse('update_post', kwargs={'pk': post.pk})
        )
        return context


###################################
# Блок для работы с комментариями #
###################################


class CommentMixin:
    """Общая логика для работы с комментариями"""

    def _get_comment_notification_context(self, form: CommentForm, action: str) -> dict[str, Any]:
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
    def _handle_comment_status(form: CommentForm, request: HttpRequest) -> bool:
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


class DeleteComment(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = "notes/delete_comment.html"
    context_object_name = "comment"

    def get_success_url(self) -> str:
        return reverse_lazy("post", kwargs={"post_slug": self.object.post.slug})

    def get_object(self, queryset: QuerySet=None) -> QuerySet:
        obj = super().get_object(queryset)
        # Проверяем права: автор, модератор или суперпользователь
        if (
                obj.user == self.request.user
                or self.request.user.is_staff
                or self.request.user.is_superuser
        ):
            return obj
        raise PermissionDenied("У вас нет прав на удаление этого комментария")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["post"] = self.object.post
        context["page_title"] = "choocha.ru | Удаление комментария"
        context["article_title"] = "Удаление комментария"
        context["robots"] = 'noindex,nofollow'
        context["canonical_url"] = self.request.build_absolute_uri(
            reverse('delete_comment', kwargs={'pk': self.object.pk})
        )
        return context


class EditComment(LoginRequiredMixin, CommentMixin, UpdateView):
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

    def get_object(self, queryset: QuerySet=None) -> QuerySet:
        obj = super().get_object(queryset)
        # Проверяем права: автор, модератор или суперпользователь
        if (
                obj.user == self.request.user
                or self.request.user.is_staff
                or self.request.user.is_superuser
        ):
            return obj

        raise PermissionDenied("У вас нет прав на редактирование этого комментария")

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
        context["post"] = self.object.post
        context["page_title"] = "choocha.ru | Редактирование комментария"
        context["article_title"] = "Редактирование комментария"
        context["robots"] = 'noindex,nofollow'
        context["canonical_url"] = self.request.build_absolute_uri(
            reverse('edit_comment', kwargs={'pk': self.object.pk})
        )
        return context

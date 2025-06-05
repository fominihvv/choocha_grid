from typing import Any

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpRequest
from django.urls import reverse
from notes.forms import CommentForm
from notes.models import Comment
import pytz
from bs4 import BeautifulSoup
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone

from choocha import settings
from django.utils.html import escape


class ObjectOwnershipMixin(AccessMixin):
    """
    Миксин для проверки владения объектом (автор статьи, комментарий и т.д.).
    Предоставляет доступ владельцу объекта, администраторам и сотрудникам.
    """

    def get_object(self, queryset: QuerySet = None) -> object:
        obj = super().get_object(queryset)
        user = self.request.user

        # Проверка доступа: автор, суперпользователь или staff
        if obj.author == user or user.is_superuser or user.is_staff:
            return obj
        else:
            raise PermissionDenied("У вас нет прав на выполнение этого действия.")


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


class PaginationMixin:
    """
    Базовый миксин для добавления пагинации в представление
    """
    extra_context = {}
    paginate_by = 2

    @staticmethod
    def get_paginator_context(context: dict, **kwargs) -> dict:
        if "paginator" in context and "page_obj" in context:
            context["page_range"] = context["paginator"].get_elided_page_range(
                context["page_obj"].number,
                on_each_side=2,
                on_ends=1,
            )
        return context


class AddPageDescriptionMixin:
    """
    Базовый миксин для добавления дополнительных данных в контекст
    """

    @staticmethod
    def get_post_description(post: Any) -> str:
        if post.meta_description and post.meta_description.strip():
            return post.meta_description
        else:
            soup = BeautifulSoup(
                post.content_short, features="html5lib"
            )
            clean_text = soup.get_text(
                strip=True
            )
        return clean_text[:160]


def format_additional_data(additional_data: dict, max_length: int = 100) -> str:
    """Безопасное форматирование дополнительных данных"""
    return '\n'.join(
        f"{escape(str(key))[:max_length]}{"...[кусь]" if len(escape(str(key))) > max_length else ''}"
        f": {escape(str(value))[:max_length]}{"...[кусь]" if len(escape(str(value))) > max_length else ''}"
        for key, value in additional_data.items()
    )


def send_notification_email(request: HttpRequest, context: dict, email_to: list = None, alert: bool = False) -> bool:
    """
    Универсальная функция отправки уведомлений

    :param request: HttpRequest
    :param context: {
        'subject': str - тема письма,
        'message': str - текст письма,
        'user': User - объект пользователя,
        'additional': dict - доп. данные
    }
    :param email_to: list - получатели (по умолчанию EMAIL_ADMIN)
    :param alert: bool - показывать уведомления пользователю
    """
    if email_to is None:
        email_to = [settings.EMAIL_ADMIN]

    # Базовые метаданные
    current_tz = pytz.timezone(settings.TIME_ZONE)
    base_context = {
        'ip': request.META.get('REMOTE_ADDR', 'неизвестен'),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'неизвестен'),
        'timestamp': timezone.now().astimezone(current_tz).strftime('%d.%m.%Y %H:%M'),
    }

    try:
        # Форматирование сообщения
        add_info = format_additional_data(context.get('additional', {}))

        full_message = f"""
        {context['message']}

        Техническая информация:
        - Время: {base_context['timestamp']}
        - IP-адрес: {base_context['ip']}
        - Устройство: {base_context['user_agent']}

*дополнительная информация:
{add_info if add_info else 'Отсутствует'}
        """

        send_mail(
            subject=f"Choocha.ru - {context['subject']}",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=email_to,
            fail_silently=False
        )

        if alert:
            messages.success(request, 'Уведомление отправлено')
        return True

    except Exception as e:
        if alert:
            messages.error(request, f'Ошибка отправки: {e}')
        return False

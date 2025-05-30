import pytz
from bs4 import BeautifulSoup
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone

from choocha import settings
from django.utils.html import escape


class PaginationMixin:
    """
    Базовый миксин для добавления пагинации в представление
    """
    extra_context = {}
    paginate_by = 2

    @staticmethod
    def get_paginator_context(context: dict, **kwargs) -> dict:
        if "paginator" in context and "page_obj" in context:
            context["page_range"] = context["paginator"].get_elided_page_range(context["page_obj"].number, on_each_side=2, on_ends=1)
        return context

class AddPageDescriptionMixin:
    """
    Базовый миксин для добавления дополнительных данных в контекст
    """
    @staticmethod
    def get_post_description(post) -> str:
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

def format_additional_data(additional_data, max_length=100) -> str:
    """Безопасное форматирование дополнительных данных"""
    return '\n'.join(
        f"{escape(str(key))[:max_length]}{"...[кусь]" if len(escape(str(key))) > max_length else ''}"
        f": {escape(str(value))[:max_length]}{"...[кусь]" if len(escape(str(value))) > max_length else ''}"
        for key, value in additional_data.items()
    )


def send_notification_email(request, context, email_to=None, alert=False) -> None:
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
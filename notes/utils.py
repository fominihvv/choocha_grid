from django.contrib import messages
from django.core.mail import send_mail

from choocha import settings


class DataMixin:
    extra_context = {}
    paginate_by = 2

    @staticmethod
    def get_mixin_context(context: dict, **kwargs) -> dict:
        if "paginator" in context and "page_obj" in context:
            context["page_range"] = context["paginator"].get_elided_page_range(context["page_obj"].number,
                                                                               on_each_side=2, on_ends=1)
        context.update({**kwargs})
        return context


def send_notification_email(request, subject_template, message_template, context, email_to=None, alert=True):
    """
    Универсальная функция для отправки уведомлений по email.

    :param request: HttpRequest объект для messages
    :param subject_template: Шаблон темы письма (используется .format(**context))
    :param message_template: Шаблон текста письма (используется .format(**context))
    :param context: Словарь с данными для подстановки в шаблоны
    :param email_to: Список email-адресов получателей (по умолчанию EMAIL_ADMIN)
    :param alert: True/ False показывать уведомление об отправке или нет
    """
    if email_to is None:
        email_to = [settings.EMAIL_ADMIN]

    try:
        subject = subject_template.format(**context)
        message = message_template.format(**context)

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=email_to,
            fail_silently=False,
        )
        if alert:
            messages.success(request, 'Уведомление успешно отправлено!')
        return True
    except Exception as e:
        if alert:
            messages.error(request, f'Ошибка при отправке письма: {e}')
        return False
from django import template
from django.db.models import Count, Q
from django.core.cache import cache
from redis import RedisError

from notes.models import Category, TagPost, Note

register = template.Library()


@register.inclusion_tag('notes/get_list_categories.html')
def show_categories(cat_selected: int = 0) -> dict[str, object]:
    """
    Возвращает список категорий, в которых есть опубликованные статьи.

    Параметры:
    - cat_selected (int): идентификатор выбранной категории.

    Возвращаемые значения:
    - all_categories (QuerySet/List): Список категорий.
    - cat_selected (int): Выбранная категория.
    """

    try:
        return {
            'all_categories': cache.get_or_set(
                f"notes:categories:{cat_selected}",
                lambda: Category.objects
                .annotate(total=Count('posts', filter=Q(posts__status=Note.Status.PUBLISHED)))
                .filter(total__gt=0)  # Исключили категории без опубликованных постов
                .order_by('name'),
                86400,
            ),
            'cat_selected': cat_selected
        }
    except RedisError:
        return {
            'all_categories': Category.objects
            .annotate(total=Count('posts', filter=Q(posts__status=Note.Status.PUBLISHED)))
            .filter(total__gt=0)
            .order_by('name'),
            'cat_selected': cat_selected
        }


@register.inclusion_tag('notes/get_list_tags.html')
def show_all_tags() -> dict[str, object]:
    """
    Возвращает список тэгов, в которых есть опубликованные статьи.

    Возвращаемые значения:
    - all_tags (QuerySet/List): Список тэгов.
    """
    try:
        return {
            'all_tags': cache.get_or_set(
                'notes:all_tags',
                lambda: TagPost.objects
                .annotate(total=Count('posts', filter=Q(posts__status=Note.Status.PUBLISHED)))
                .filter(total__gt=0)  # Исключили теги без опубликованных постов
                .order_by('name'),
                86400
            )
        }
    except RedisError:
        return {
            'all_tags': TagPost.objects
            .annotate(total=Count('posts', filter=Q(posts__status=Note.Status.PUBLISHED)))
            .filter(total__gt=0)
            .order_by('name')
        }


@register.inclusion_tag('notes/get_last_posts.html')
def show_last_posts(count: int = 5) -> dict[str, object]:
    """
    Возвращает список последних опубликованных статей.

    Параметры:
    - count (int): Количество статей.

    Возвращаемые значения:
    - last_posts (QuerySet/List): Список последних опубликованных статей.
    """
    try:
        return {
            'last_posts': cache.get_or_set(
                f'last_posts:{count}',
                lambda: Note.published.get_latest(count),
                3600,
            )
        }
    except RedisError:
        return {'last_posts': Note.published.get_latest(count)}

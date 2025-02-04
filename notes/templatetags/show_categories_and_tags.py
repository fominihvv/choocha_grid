from django import template
from django.db.models import Count, Q

from notes.models import Category, TagPost

register = template.Library()


@register.inclusion_tag('notes/list_categories.html')
def show_categories(cat_selected=0):
    cats = (
        Category.objects
        .annotate(total=Count('posts', filter=Q(posts__is_published=True)))
        .filter(total__gt=0)
        .order_by('name')  # Добавили сортировку по полю 'name'
    )
    return {'cats': cats, 'cat_selected': cat_selected}


@register.inclusion_tag('notes/list_tags.html')
def show_all_tags():
    tags = (
        TagPost.objects
        .annotate(total=Count('notes', filter=Q(notes__is_published=True)))
        .filter(total__gt=0)
        .order_by('tag')  # Добавили сортировку по полю 'name'
    )
    return {'tags': tags}

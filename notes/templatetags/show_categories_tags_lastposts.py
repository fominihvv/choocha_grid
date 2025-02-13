from django import template
from django.db.models import Count, Q

from notes.models import Category, TagPost, Note

register = template.Library()


@register.inclusion_tag('notes/get_list_categories.html')
def show_categories(cat_selected=0):
    cats = (
        Category.objects
        .annotate(total=Count('posts', filter=Q(posts__is_published=True)))
        .filter(total__gt=0) # Исключили категории без опубликованных постов
        .order_by('name')  # Добавили сортировку по полю 'name'
    )
    return {'cats': cats, 'cat_selected': cat_selected}


@register.inclusion_tag('notes/get_list_tags.html')
def show_all_tags():
    tags = (
        TagPost.objects
        .annotate(total=Count('notes', filter=Q(notes__is_published=True)))
        .filter(total__gt=0) # Исключили теги без опубликованных постов
        .order_by('tag')  # Добавили сортировку по полю 'name'
    )
    return {'tags': tags}


@register.inclusion_tag('notes/get_last_posts.html')
def show_last_posts():
    posts = (
        Note.objects
        .filter(is_published=True)
        .order_by('-time_update')[:5]
    )
    return {'posts': posts}
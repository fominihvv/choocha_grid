from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.safestring import mark_safe

from .models import Note, TagPost, Category, Comment


@admin.register(Note)
class NotesAdmin(admin.ModelAdmin):
    fields = (
        "title",
        "slug",
        "image",
        "post_image",
        "post_image_size",
        "content_short",
        "content_full",
        "time_create",
        "time_update",
        "cat",
        "tags",
        "status",
        "meta_description",
    )
    readonly_fields = (
        "time_create",
        "time_update",
        "slug",
        "post_image",
        "post_image_size",
    )
    list_display = (
        "title",
        "slug",
        "time_create",
        "time_update",
        "cat",
        "status",
        "post_image",
        "post_image_size",
    )
    list_display_links = (
        "title",
        "cat",
    )
    ordering = (
        "-time_update",
        "title",
    )
    search_fields = (
        "title",
        "content_short",
        "content_full",
        "cat__name",
    )
    list_editable = ("status",)
    list_per_page = 5
    actions = [
        "status",
        "set_draft",
    ]
    list_filter = [
        "cat__name",
        "status",
    ]
    save_on_top = True

    @staticmethod
    @admin.display(description="Изображение")
    def post_image(note: Note) -> str:
        if note.image:
            return mark_safe(
                f'<img src="{note.image.url}" alt="{note.title}" width="200">'
            )
        return "Нет фото"

    @staticmethod
    @admin.display(description="Размер изображения")
    def post_image_size(note: Note) -> str:
        if note.image:
            return f"{note.image.width}x{note.image.height}"
        return "Нет фото"

    @admin.action(description="Опубликовать выбранные записи")
    def set_published(self, request: HttpRequest, queryset: QuerySet) -> None:
        count = queryset.update(status=Note.Status.PUBLISHED)
        self.message_user(request, f"{count} записей опубликованы")

    @admin.action(description="Снять с публикации выбранные записи")
    def set_draft(self, request: HttpRequest, queryset: QuerySet) -> None:
        count = queryset.update(status=Note.Status.DRAFT)
        self.message_user(
            request, f"{count} записей сняты с публикации", messages.WARNING
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "slug",
    )
    list_display_links = (
        "id",
        "name",
    )
    search_fields = ("name",)


admin.site.register(TagPost)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "post",
        "created",
        "status",
    )
    list_filter = (
        "status",
        "created",
        "updated",
    )
    search_fields = (
        "user",
        "body",
    )

from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import reverse
from django_ckeditor_5.fields import CKEditor5Field
from django_extensions.db.fields import AutoSlugField
from slugify import slugify


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=Note.Status.PUBLISHED)


class TagPost(models.Model):
    class Meta:
        verbose_name = 'Метка'
        verbose_name_plural = 'Метки'

    tag = models.CharField(max_length=100, db_index=True)
    slug = AutoSlugField(
        populate_from='tag',
        slugify_function=slugify,
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Слаг'
    )

    def __str__(self) -> str:
        return self.tag

    def get_absolute_url(self) -> str:
        return reverse('tag', kwargs={'tag_slug': self.slug})


class Category(models.Model):
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    name = models.CharField(max_length=100, db_index=True, verbose_name='Категория')
    slug = AutoSlugField(
        populate_from='name',
        slugify_function=slugify,
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Слаг'
    )

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse('category', kwargs={'cat_slug': self.slug})


class Note(models.Model):
    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['title', '-time_create']
        indexes = [
            models.Index(fields=['title', '-time_create']),
        ]

    class Status(models.IntegerChoices):
        DRAFT = 0, 'Черновик'
        PUBLISHED = 1, 'Опубликовано'

    title = models.CharField(max_length=255, verbose_name='Заголовок')
    slug = AutoSlugField(
        populate_from='title',
        slugify_function=slugify,
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name='Слаг'
    )
    image = models.ImageField(
        upload_to='images/%Y/%m/%d/',
        default=None,
        blank=True,
        verbose_name='Изображение',
        null=True
    )
    content_short = CKEditor5Field(
        max_length=600,
        blank=True,
        null=True,
        verbose_name='Краткий текст статьи'
    )
    content_full = CKEditor5Field(
        blank=True,
        null=True,
        config_name='extends',
        verbose_name='Полный текст статьи'
    )
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    time_update = models.DateTimeField(auto_now=True, verbose_name='Дата последнего изменения')
    is_published = models.BooleanField(
        choices=tuple(map(lambda x: (bool(x[0]), x[1]), Status.choices)),
        default=Status.DRAFT,
        verbose_name='Опубликовано'
    )
    cat = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='posts', verbose_name='Категория')
    tags = models.ManyToManyField(TagPost, blank=True, related_name='notes', verbose_name='Метки')
    author = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        related_name='posts',
        null=True,
        default=None,
        verbose_name='Автор'
    )
    meta_description = models.TextField(
        max_length=160,
        blank=True,
        null=True,
        verbose_name='Метаописание'
    )


    objects = models.Manager()
    published = PublishedManager()

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse('post', kwargs={'post_slug': self.slug})

    def get_update_url(self) -> str:
        return reverse('update_post', kwargs={'pk': self.pk})

    def get_delete_url(self) -> str:
        return reverse('delete_post', kwargs={'pk': self.pk})


class UploadFiles(models.Model):
    file = models.FileField(upload_to='uploads_model/', verbose_name='Файл')

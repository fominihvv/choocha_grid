# Generated by Django 5.1 on 2025-01-23 07:35

import django_ckeditor_5.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0005_alter_note_content'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='note',
            name='content',
        ),
        migrations.AddField(
            model_name='note',
            name='content_full',
            field=django_ckeditor_5.fields.CKEditor5Field(blank=True, null=True, verbose_name='Полный текст статьи'),
        ),
        migrations.AddField(
            model_name='note',
            name='content_short',
            field=django_ckeditor_5.fields.CKEditor5Field(blank=True, max_length=500, null=True, verbose_name='Краткий текст статьи'),
        ),
    ]

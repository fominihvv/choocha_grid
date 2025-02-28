from django.contrib.sitemaps import Sitemap
from .models import Note, TagPost, Category


class NoteSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 1.0

    def items(self):
        return Note.published.all()


    def lastmod(self, obj):
        return obj.time_update

class TagSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return TagPost.objects.all().order_by('tag')

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Category.objects.all().order_by('name')


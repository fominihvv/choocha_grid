# choocha\robots.py
from django.http import HttpResponse
from django.views.decorators.http import require_GET

@require_GET
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Sitemap: https://choocha.ru/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
from django.shortcuts import render


def e_handler403(request, exception):
    return render(request, 'notes/403.html', status=403)


def e_handler404(request, exception):
    return render(request, 'notes/404.html', status=404)


def e_handler500(request):
    return render(request, 'notes/500.html', status=500)

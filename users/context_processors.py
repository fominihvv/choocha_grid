#choocha/users/context_processors.py
menu = [{'title': "О сайте", 'url_name': 'about', 'for_all': True, },
        {'title': "Добавить статью", 'url_name': 'add_post', 'for_moderator': True},
        {'title': "Обратная связь", 'url_name': 'contact', 'for_all': True},
        {'title': "Войти", 'url_name': 'users:login', 'title2': "Регистрация", 'url_name2': 'users:register',
         'for_anonymous': True},
        {'title': "", 'url_name': "users:profile", 'title2': "Выйти", 'url_name2': 'users:logout',
         'for_authorized': True},
        ]


def get_notes_menu_context(request):
    result_menu = []
    for item in menu:
        if 'for_all' in item:
            result_menu.append(item)
        elif 'for_moderator' in item and request.user.has_perm('notes.add_note'):
            result_menu.append(item)
        elif 'for_anonymous' in item and request.user.is_anonymous:
            result_menu.append(item)
        elif 'for_authorized' in item and request.user.is_authenticated:
            result_menu.append(item)
    if request.user.is_authenticated:
        result_menu[-1]['title'] = f'Добро пожаловать, {request.user.username}'
    return {'mainmenu': result_menu}

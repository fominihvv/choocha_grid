from django.urls import path

from . import views

urlpatterns = [
    path('', views.NoteHome.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('addpost/', views.AddPost.as_view(), name='add_post'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('post/<slug:post_slug>/', views.ShowPost.as_view(), name='post'),
    path('category/<slug:cat_slug>/', views.NotesCategory.as_view(), name='category'),
    path('tag/<slug:tag_slug>/', views.NotesTags.as_view(), name='tag'),
    path('update/<int:pk>/', views.UpdatePost.as_view(), name='update_post'),
    path('delete/<int:pk>/', views.DeletePost.as_view(), name='delete_post'),

]

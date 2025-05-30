from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('addpost/', views.AddPost.as_view(), name='add_post'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('post/<slug:post_slug>/', views.ShowPost.as_view(), name='post'),
    path('post/<slug:post_slug>/comment/', views.AddCommentView.as_view(), name='add_comment'),
    path('category/<slug:cat_slug>/', views.ShowPostByCategory.as_view(), name='category'),
    path('tag/<slug:tag_slug>/', views.ShowPostByTag.as_view(), name='tag'),
    path('update/<int:pk>/', views.UpdatePost.as_view(), name='update_post'),
    path('delete/<int:pk>/', views.DeletePost.as_view(), name='delete_post'),
    path('comments/<int:pk>/approve/', views.ApproveComment.as_view(), name='approve_comment'),
    path('comments/<int:pk>/edit/', views.EditComment.as_view(), name='edit_comment'),
    path('comments/<int:pk>/delete/', views.DeleteComment.as_view(), name='delete_comment'),
]

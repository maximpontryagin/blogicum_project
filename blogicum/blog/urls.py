from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('posts/create/', views.CreatePost.as_view(),
         name='create_post'),
    path('posts/<int:post_id>/edit/',
         views.PostUpdateView.as_view(), name='edit_post'),
    path('posts/<int:post_id>/edit_comment/<int:comment_id>',
         views.CommentsUpdateView.as_view(), name='edit_comment'),
    path('posts/<int:post_id>/delete_comment/<int:comment_id>',
         views.CommentDeleteView.as_view(), name='delete_comment'),
    path('posts/<int:post_id>/comment/',
         views.add_comment, name='add_comment'),
    path('posts/<int:post_id>/delete/',
         views.PostDeleteView.as_view(), name='delete_post'),
    path('posts/<int:post_id>/',
         views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:category>/', views.CategoryShowView.as_view(),
         name='category_posts'),
    path('edit_profile/', views.ProfileUpadateView.as_view(),
         name='edit_profile'),
    path('profile/<slug:username>/', views.ProfileView.as_view(),
         name='profile'),
]

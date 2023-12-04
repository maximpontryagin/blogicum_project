from django.forms.models import BaseModelForm
from django.http import Http404, HttpResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView, CreateView,
    UpdateView, DetailView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model

from blog.models import Post, Category
from .forms import CommentsForm, PostForm
from .config import DATETIME_NOW, PAGINATE_POST
from .mixins import CommentMixin, PostMixin
from .utils import select, anotate

User = get_user_model()


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentsForm()
        context['profile'] = select(Post).filter(pk=self.kwargs['post_id'])
        context['comments'] = self.object.comments.select_related('author')
        return context

    def dispatch(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['post_id'])
        if post.author != request.user and (
            post.is_published is False
            or post.category.is_published is False
                or post.pub_date > DATETIME_NOW):
            raise Http404()
        return super().dispatch(self.request, *args, **kwargs)


class CategoryShowView(ListView):
    template_name = 'blog/category.html'
    paginate_by = PAGINATE_POST

    def get_queryset(self):
        return anotate(select(Post).filter(
            category__slug=self.kwargs['category']))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category, slug=self.kwargs['category'], is_published=True)
        return context


class IndexView(ListView):
    template_name = 'blog/index.html'
    paginate_by = PAGINATE_POST

    def get_queryset(self):
        return anotate(select(Post))


class ProfileView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = PAGINATE_POST

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User, username=self.kwargs['username'])
        return context

    def get_queryset(self):
        user_detail = get_object_or_404(User.objects.all(),
                                        username=self.kwargs['username'])
        return anotate(Post.objects.select_related(
            'author', 'location', 'category').filter(
            author=user_detail.id).prefetch_related(
            'comments'))


class ProfileUpadateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ('first_name', 'last_name', 'username', 'email')
    template_name = 'blog/user.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostDeleteView(PostMixin, DeleteView):
    pass


class PostUpdateView(PostMixin, UpdateView):
    fields = (
        'is_published', 'title', 'text', 'pub_date',
        'location', 'category', 'image'
    )


class CreatePost(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CommentDeleteView(CommentMixin, DeleteView):
    pass


class CommentsUpdateView(CommentMixin, UpdateView):
    form_class = CommentsForm


class AddCommentView(LoginRequiredMixin, CreateView):
    form_class = CommentsForm
    template_name = 'blog/detail.html'

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={
            'post_id': self.kwargs['post_id']}
        )

    def form_valid(self, form):
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['post_id']
        )
        form.instance.author = self.request.user
        return super().form_valid(form)

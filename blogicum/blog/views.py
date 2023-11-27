from django.forms.models import BaseModelForm
from django.http import Http404, HttpResponse
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView, CreateView,
    UpdateView, DetailView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count

from blog.models import Post, Category, Comments
from .forms import CommentsForm, PostForm


User = get_user_model()

DATETIME_NOW = timezone.now()

PAGINATE_POST = 10


class CommentMixin(LoginRequiredMixin):
    model = Comments
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = get_object_or_404(self.model,
                                               id=self.kwargs['comment_id'])
        return context

    def get_success_url(self):
        return reverse_lazy('blog:post_detail',
                            kwargs={'post_id': self.kwargs['post_id']})

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class PostMixin(LoginRequiredMixin):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse('blog:profile', kwargs={'username': self.request.user})


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_count'] = self.object.comment.select_related(
            'author').count()
        context['form'] = CommentsForm()
        context['profile'] = Post.objects.select_related(
            'author', 'location', 'category').filter(
            is_published__exact=True, pub_date__lte=DATETIME_NOW,
            category__is_published__exact=True,
            pk__exact=self.kwargs['post_id'])
        context['comments'] = self.object.comment.select_related('author')
        return context

    def dispatch(self, request, *args, **kwargs):
        posts = get_object_or_404(Post, pk=kwargs['post_id'])
        if posts.author != request.user and (
            posts.is_published is False
            or posts.category.is_published is False
                or posts.pub_date > DATETIME_NOW):
            raise Http404()
        return super().dispatch(self.request, *args, **kwargs)


class CategoryShowView(ListView):
    template_name = 'blog/category.html'
    paginate_by = PAGINATE_POST

    def get_queryset(self):
        return Post.objects.select_related(
            'author', 'location', 'category').filter(
                is_published__exact=True, category__is_published__exact=True,
                category__slug__exact=self.kwargs['category'],
                pub_date__lte=DATETIME_NOW)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category.objects.all().filter(is_published__exact=True),
            slug=self.kwargs['category'])
        return context


class IndexView(ListView):
    template_name = 'blog/index.html'
    paginate_by = PAGINATE_POST

    def get_queryset(self):
        queryset = Post.objects.select_related(
            'author', 'location', 'category').filter(
                is_published__exact=True, category__is_published__exact=True,
                pub_date__lte=DATETIME_NOW)
        queryset = queryset.prefetch_related('comment').annotate(
            comment_count=Count('comment')).order_by('-pub_date')
        return queryset


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
        post_list = Post.objects.select_related(
            'author', 'location', 'category').filter(
                author__exact=user_detail.id).prefetch_related(
                    'comment').annotate(comment_count=Count(
                        'comment')).order_by('-pub_date')
        return post_list


class ProfileUpadateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ('first_name', 'last_name', 'username', 'email')
    template_name = 'blog/user.html'
    pk_url_kwarg = 'post_id'

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        if self.request.user.is_authenticated:
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
        if self.request.user.is_authenticated:
            return reverse(
                'blog:profile',
                kwargs={'username': self.request.user.username}
            )


class CommentDeleteView(CommentMixin, DeleteView):
    pass


class CommentsUpdateView(CommentMixin, UpdateView):
    form_class = CommentsForm


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentsForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=post_id)

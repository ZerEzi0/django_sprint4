from django.http import Http404  # Для выброса исключения Http404
from django.utils import timezone  # Для работы с временем

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DeleteView,
    DetailView
)

from .forms import CommentForm, PostForm, CustomUserChangeForm
from .models import Category, Comment, Post

User = get_user_model()

NUMBER_OF_POSTS = 10


class AuthorMixin(UserPassesTestMixin):
    """Mixin для проверки, что пользователь является автором поста."""

    def test_func(self):
        return self.get_object().author == self.request.user

    def handle_no_permission(self):
        post_id = self.kwargs.get('post_id')
        return redirect('blog:post_detail', post_id=post_id)


class CommentAuthorMixin(UserPassesTestMixin):
    """
    Mixin для проверки, что пользователь
    является автором комментария или суперпользователем.
    """

    def test_func(self):
        comment = self.get_object()
        return (
            comment.author == self.request.user
            or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        post_id = self.kwargs.get('post_id')
        return redirect('blog:post_detail', post_id=post_id)


class IndexListView(ListView):
    template_name = 'blog/index.html'
    paginate_by = NUMBER_OF_POSTS
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.optimized_filter(
            apply_filters=True,
            apply_annotations=True
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    context_object_name = 'post'
    queryset = Post.objects.select_related('author', 'category', 'location')
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = super().get_object(queryset)

        if self.request.user != post.author and (
            not post.is_published
            or (post.category and not post.category.is_published)
            or post.pub_date > timezone.now()
        ):
            raise Http404("Пост не найден")

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        comments = post.comments.select_related('author').all()
        context['comments'] = comments
        context['form'] = CommentForm()
        return context


class CreatePostView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, AuthorMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostDeleteView(LoginRequiredMixin, AuthorMixin, DeleteView):
    model = Post
    template_name = 'blog/post_confirm_delete.html'
    success_url = reverse_lazy('blog:post_list')
    pk_url_kwarg = 'post_id'

    def get_success_url(self):
        return reverse_lazy('blog:post_list')


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class CommentUpdateView(LoginRequiredMixin, CommentAuthorMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post__id=self.kwargs['post_id']
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )


class CommentDeleteView(LoginRequiredMixin, CommentAuthorMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
            post__id=self.kwargs['post_id']
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )


class CategoryDetailView(ListView):
    template_name = 'blog/category.html'
    paginate_by = NUMBER_OF_POSTS
    context_object_name = 'posts'
    slug_url_kwarg = 'category_slug'

    def get_category(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs[self.slug_url_kwarg],
            is_published=True
        )

    def get_queryset(self):
        return self.get_category().posts.optimized_filter(
            apply_filters=True,
            apply_annotations=True
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context


class ProfileView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS
    context_object_name = 'posts'
    slug_url_kwarg = 'username'

    def get_profile(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        author = self.get_profile()
        apply_filters = author != self.request.user
        return Post.objects.optimized_filter(
            apply_filters=apply_filters,
            apply_annotations=True
        ).filter(author=author)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_profile()
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostListView(ListView):
    template_name = 'blog/index.html'
    paginate_by = NUMBER_OF_POSTS
    context_object_name = 'posts'
    queryset = Post.objects.optimized_filter(
        apply_filters=True,
        apply_annotations=True
    )

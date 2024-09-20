from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from .forms import CommentForm, PostForm, CustomUserChangeForm
from .models import Category, Comment, Post

User = get_user_model()

NUMBER_OF_POSTS = 10


class AuthorView(UserPassesTestMixin):
    def test_func(self):
        return self.get_object().author == self.request.user

    def handle_no_permission(self):
        post_id = self.get_object().id
        return redirect('blog:post_detail', post_id=post_id)


class CommentAuthorMixin(UserPassesTestMixin):
    def test_func(self):
        comment = self.get_object()
        return (
            comment.author == self.request.user
            or self.request.user.is_superuser
        )

    def handle_no_permission(self):
        post_id = self.get_object().post.id
        return redirect('blog:post_detail', post_id=post_id)


class IndexListView(ListView):
    template_name = 'blog/index.html'
    paginate_by = NUMBER_OF_POSTS
    queryset = Post.objects.filter_posts_for_publication().count_comments()
    context_object_name = 'posts'


class PostDetailView(ListView):
    template_name = 'blog/detail.html'
    paginate_by = NUMBER_OF_POSTS
    context_object_name = 'comments'

    def get_object(self):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if self.request.user == post.author:
            return post
        return get_object_or_404(
            Post.objects.filter_posts_for_publication(),
            pk=self.kwargs['post_id']
        )

    def get_queryset(self):
        return self.get_object().comments.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['post'] = self.get_object()
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


class PostUpdateView(LoginRequiredMixin, AuthorView, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class PostDeleteView(LoginRequiredMixin, AuthorView, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:post_list')
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        return get_object_or_404(Post, pk=self.kwargs['post_id'])


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post.objects.filter_posts_for_publication(),
            pk=self.kwargs['post_id']
        )
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
            Comment, pk=self.kwargs['comment_id'],
            post__id=self.kwargs['post_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'edit'
        context['comment'] = self.get_object()
        return context

    def get_success_url(self):
        post_id = self.get_object().post.id
        return reverse('blog:post_detail', kwargs={'post_id': post_id})


class CommentDeleteView(LoginRequiredMixin, CommentAuthorMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Comment, pk=self.kwargs['comment_id'],
            post__id=self.kwargs['post_id']
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'delete'
        context['comment'] = self.get_object()
        return context

    def get_success_url(self):
        post_id = self.get_object().post.id
        return reverse('blog:post_detail', kwargs={'post_id': post_id})


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.get_category()
        return context

    def get_queryset(self):
        return self.get_category().posts.filter_posts_for_publication()


class ProfileView(ListView):
    template_name = 'blog/profile.html'
    paginate_by = NUMBER_OF_POSTS
    context_object_name = 'posts'
    slug_url_kwarg = 'username'

    def get_profile(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        author = self.get_profile()
        posts = author.posts.count_comments()
        if author == self.request.user:
            return posts
        return posts.filter_posts_for_publication()

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
    queryset = Post.objects.filter_posts_for_publication().count_comments()
    context_object_name = 'posts'

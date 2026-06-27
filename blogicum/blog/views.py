from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post

User = get_user_model()

PAGINATION_PAGES_COUNT = 10


class ProfileDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    ordering = ['-pub_date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        posts = Post.objects.filter(
            author=user
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

        paginator = Paginator(posts, PAGINATION_PAGES_COUNT)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context['profile'] = user
        context['page_obj'] = page_obj
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = (
        'username', 'first_name', 'last_name', 'email'
    )
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={
            'username': self.object.username
        })


class PostListView(ListView):
    model = Post
    paginate_by = PAGINATION_PAGES_COUNT
    template_name = 'blog/index.html'
    ordering = ['-pub_date']

    def get_queryset(self):
        return Post.objects.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        ).annotate(
            comment_count=Count('comments')
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={
            'username': self.request.user.username
        })


class PostDetailView(DetailView):
    model = Post
    form_class = CommentForm
    pk_url_kwarg = 'pk'
    template_name = 'blog/detail.html'
    ordering = ['-pub_date']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.object
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.filter(
            post=self.object)
        return context

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Post.objects.filter(
                Q(
                    category__is_published=True,
                    is_published=True,
                    pub_date__lte=timezone.now()
                )
                | Q(author=user)
            )

        return Post.objects.filter(
            category__is_published=True,
            is_published=True,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def handle_no_permission(self):
        post = self.get_object()
        return redirect('blog:post_detail', pk=post.pk)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={
            'pk': self.object.id
        })


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    pk_url_kwarg = 'pk'

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={
            'username': self.request.user.username
        })


class CategoryListView(ListView):
    model = Post
    paginate_by = PAGINATION_PAGES_COUNT
    template_name = 'blog/category.html'
    ordering = ['-pub_date']

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        return Post.objects.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__slug=category_slug
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('category_slug')
        context['category'] = get_object_or_404(
            Category, slug=category_slug, is_published=True)
        return context


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST or None)

    if not form.is_valid():
        return redirect('blog:post_detail', pk=pk)

    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()

    return redirect('blog:post_detail', pk=pk)


class CommentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    pk_url_kwarg = 'comment_pk'
    fields = ('text',)
    template_name = 'blog/comment.html'

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={
            'pk': self.object.post.id
        })


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    pk_url_kwarg = 'comment_pk'
    fields = ('text',)
    template_name = 'blog/comment.html'

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={
            'pk': self.object.post.id
        })


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)

        send_mail(
            subject='Пароль изменен',
            message=f'Здравствуйте, {self.request.user.username}!\n\n'
                    f'Ваш пароль на сайте Blogicum был успешно изменен.\n\n'
                    f'Если вы не меняли пароль, '
                    f'немедленно свяжитесь с администрацией.',
            from_email='blogicum@yandex.ru',
            recipient_list=[self.request.user.email],
            fail_silently=False,
        )

        return response

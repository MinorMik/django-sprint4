from django.shortcuts import get_object_or_404
# from django.http import Http404
from .models import Post, Comment, Category
from django.db.models import Q
from django.utils import timezone
from django.views.generic import (
    CreateView, UpdateView, DetailView, DeleteView, ListView
)
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import send_mail


# Create your views here.

User = get_user_model()


class CustomParinator:

    def __init__(self, request, queryset, page_size=10):
        self.paginator = Paginator(queryset, page_size)
        self.page_number = request.GET.get('page')
        self.page_obj = self.paginator.get_page(self.page_number)

    def get_paginator(self):
        return self.page_obj


class ProfileDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        posts = Post.objects.filter(
            author=user
        ).order_by(
            '-pub_date'
        ).annotate(
            comment_count=Count('comment')
        )

        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
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
    paginate_by = 10
    template_name = 'blog/index.html'

    def get_queryset(self):
        return Post.objects.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        ).order_by(
            '-pub_date'
        ).annotate(
            comment_count=Count('comment')
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post'] = self.object
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.filter(
            post=self.object).order_by('created_at')
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
        )


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
    paginate_by = 10
    template_name = 'blog/category.html'

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        return Post.objects.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__slug=category_slug
        ).order_by(
            '-pub_date'
        ).annotate(
            comment_count=Count('comment')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs.get('category_slug')
        context['category'] = get_object_or_404(
            Category, slug=category_slug, is_published=True)
        return context


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
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
        # Сохраняем пароль
        response = super().form_valid(form)

        # Отправляем письмо об изменении пароля
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

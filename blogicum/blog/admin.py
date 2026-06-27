from django.contrib import admin

from blog.models import Category, Comment, Location, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title',
                    'slug',
                    'is_published',
                    'created_at')

    search_fields = ('title',
                     'slug',
                     'is_published',
                     'created_at')

    list_filter = ('title',
                   'slug',
                   'is_published',
                   'created_at')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',
                    'is_published',
                    'created_at')

    search_fields = ('name',
                     'is_published',
                     'created_at')

    list_filter = ('name',
                   'is_published',
                   'created_at')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title',
                    'pub_date',
                    'location',
                    'category',
                    'is_published',
                    'created_at')

    search_fields = ('title',
                     'pub_date',
                     'location',
                     'category',
                     'is_published',
                     'created_at')

    list_filter = ('title',
                   'pub_date',
                   'location',
                   'category',
                   'is_published',
                   'created_at')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('text',
                    'post',
                    'author',
                    'created_at')

    search_fields = ('text',
                     'post',
                     'author',
                     'created_at')

    list_filter = ('text',
                   'post',
                   'author',
                   'created_at')

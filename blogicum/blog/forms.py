from django import forms
from .models import Post, Comment
# from django.core.exceptions import ValidationError
# from django.core.mail import send_mail


class PostForm(forms.ModelForm):
    class Meta:
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},   
                format='%Y-%m-%dT%H:%M'
            )
        }
        model = Post
        fields = (
            'title',
            'category',
            'location',
            'pub_date',
            'text',
            'image',
        )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'text',
        )

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Comment, Post

User = get_user_model()


class CustomUserChangeForm(forms.ModelForm):
    """
    Форма для изменения профиля пользователя.
    Включает поля: username, first_name, last_name, email.
    """

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class PostForm(forms.ModelForm):
    pub_date = forms.DateTimeField(
        label='Дата и время публикации',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        initial=timezone.now
    )

    class Meta:
        model = Post
        exclude = ('author',)
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class CommentForm(forms.ModelForm):
    text = forms.CharField(
        label='Текст комментария',
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}),
        help_text='Введите ваш комментарий здесь.'
    )

    class Meta:
        model = Comment
        fields = ('text',)

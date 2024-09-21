from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django.utils import timezone

from core.models import CreatedAt, IsPublished

LENGTH_STRING = 20
MAX_LENGTH = 256

User = get_user_model()


class PublishedQuerySet(models.QuerySet):
    def optimized_filter(self, apply_filters=False, apply_annotations=False):
        """
        Оптимизированный метод для получения постов
        с учетом фильтров и аннотаций.

        :param apply_filters:
        Если True, применяются фильтры для публикации.
        :param apply_annotations:
        Если True, применяются аннотации и сортировка.
        :return:
        Отфильтрованный и/или аннотированный QuerySet.
        """
        queryset = self.select_related('category', 'location', 'author')

        if apply_filters:
            queryset = queryset.filter(
                pub_date__lte=timezone.now(),
                is_published=True,
                category__is_published=True,
            )

        if apply_annotations:
            queryset = queryset.annotate(
                comment_count=Count('comments')
            ).order_by('-pub_date')

        return queryset


class Category(CreatedAt, IsPublished):
    title = models.CharField('Заголовок', max_length=MAX_LENGTH)
    description = models.TextField('Описание')
    slug = models.SlugField(
        'Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; \
            разрешены символы латиницы, цифры, дефис и подчёркивание.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:LENGTH_STRING]


class Location(CreatedAt, IsPublished):
    name = models.CharField('Название места', max_length=MAX_LENGTH)

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:LENGTH_STRING]


class Post(CreatedAt, IsPublished):
    title = models.CharField('Заголовок', max_length=MAX_LENGTH)
    text = models.TextField('Текст')
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        help_text='Если установить дату и время в будущем \
             — можно делать отложенные публикации.'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts',
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Местоположение',
        related_name='posts'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
        related_name='posts'
    )
    image = models.ImageField(
        'Фото', blank=True, upload_to='posts_images/', null=True
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ('-pub_date',)

    objects = PublishedQuerySet.as_manager()

    def __str__(self):
        return self.title[:LENGTH_STRING]


class Comment(CreatedAt):
    text = models.TextField('Текст')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост',
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор комментария',
        related_name='comments'
    )

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:LENGTH_STRING]

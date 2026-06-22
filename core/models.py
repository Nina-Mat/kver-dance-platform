from django.conf import settings
from django.db import models


class InfoPost(models.Model):
    """Информационный пост администрации KVER."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='info_posts',
        verbose_name='Автор',
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    body = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')

    class Meta:
        verbose_name = 'Информационный пост'
        verbose_name_plural = 'Информационные посты'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

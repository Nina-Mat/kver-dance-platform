from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import CustomUser, Team


class CoverMedia(models.Model):
    SOURCE_CHOICES = [
        ('upload', ' Загрузка файла'),
        ('youtube', ' Ссылка YouTube'),
    ]

    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploads', verbose_name="Автор")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='covers',
                             verbose_name="Команда")

    source_type = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='upload',
                                   verbose_name="Источник видео")
    video_file = models.FileField(upload_to='covers/videos/', blank=True, null=True, verbose_name="Видеофайл")
    cover_image = models.ImageField(upload_to='covers/images/', blank=True, null=True,
                                    verbose_name="Обложка")  # 🔥 Добавили!

    youtube_id = models.CharField(max_length=20, blank=True, verbose_name="YouTube Video ID")
    youtube_url = models.URLField(blank=True, verbose_name="Ссылка на YouTube")

    title = models.CharField(max_length=150, verbose_name="Название кавера")
    thumbnail_url = models.URLField(blank=True, verbose_name="Ссылка на превью")
    duration = models.CharField(max_length=10, blank=True, verbose_name="Длительность")
    description = models.TextField(blank=True, verbose_name="Описание")

    tags = models.CharField(max_length=200, blank=True, verbose_name="Теги (через запятую)")

    mentioned_users = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name='mentioned_in_covers',
        verbose_name='Упомянутые пользователи',
    )

    views_kver = models.PositiveIntegerField(default=0, verbose_name="Просмотры на KVER")
    likes_kver = models.PositiveIntegerField(default=0, verbose_name="Лайки на KVER")
    youtube_views = models.PositiveIntegerField(default=0, verbose_name="Просмотры на YouTube")
    youtube_likes = models.PositiveIntegerField(default=0, verbose_name="Лайки на YouTube")

    is_approved = models.BooleanField(default=False, verbose_name="Прошёл модерацию")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    def clean(self):
        if self.source_type == 'upload' and not self.video_file:
            raise ValidationError("Загрузите видеофайл")
        if self.source_type == 'youtube' and not self.youtube_id:
            raise ValidationError("Укажите ссылку на YouTube")

    def __str__(self):
        return f"{self.title} ({self.get_source_type_display()})"

    class Meta:
        verbose_name = "Видео-кавер"
        verbose_name_plural = "Видео-каверы"
        ordering = ['-created_at']


class Comment(models.Model):
    media = models.ForeignKey(CoverMedia, on_delete=models.CASCADE, related_name='comments', verbose_name="К каверу")
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, verbose_name="Автор")
    text = models.TextField(verbose_name="Текст комментария")
    is_anonymous = models.BooleanField(default=False, verbose_name="Анонимно")
    is_approved = models.BooleanField(default=False, verbose_name="Прошел модерацию")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата")

    def __str__(self):
        author_name = "Аноним" if self.is_anonymous else (self.user.username if self.user else "Удален")
        return f"Комментарий к {self.media.title} от {author_name}"

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ['-created_at']
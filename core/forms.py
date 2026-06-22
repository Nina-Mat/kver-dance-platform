from django import forms

from .models import InfoPost

BOOTSTRAP_TEXT = {'class': 'form-control'}
BOOTSTRAP_TEXTAREA = {'class': 'form-control', 'rows': 5}


class InfoPostForm(forms.ModelForm):
    class Meta:
        model = InfoPost
        fields = ['title', 'body']
        widgets = {
            'title': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Заголовок новости',
            }),
            'body': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'placeholder': 'Текст информационного поста...',
            }),
        }
        labels = {
            'title': 'Заголовок',
            'body': 'Текст',
        }

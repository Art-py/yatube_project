from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        widgets = {
            "text": forms.Textarea(attrs={
                'class': 'form-control',
                'cols': '40',
                'rows': '10'
            }),
            "group": forms.Select(attrs={
                'class': 'form-control'
            })
        }

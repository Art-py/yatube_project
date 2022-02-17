from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, CHAR_CUT


User = get_user_model()


class PostGroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=('Сделаем длинную строку,'
                  ' чтобы можно было отрезать первые 15 символов!'),
        )

    def test_models_have_correct_object_names(self):
        """Правильное формирование имени поста, группы."""
        self.assertEqual(self.group.__str__(), self.group.title)
        self.assertEqual(self.post.__str__(), self.post.text[:CHAR_CUT])

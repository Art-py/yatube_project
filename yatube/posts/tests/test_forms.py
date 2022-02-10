from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group


User = get_user_model()


class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Jack')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись."""
        context = {
            'text': 'Тестовый пост',
            'group': self.group.pk,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            context)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ))
        # Проверяем, что создалась запись
        self.assertTrue(Post.objects.filter(
            author=self.user,
            text='Тестовый пост',
            group=self.group.pk
        ).exists())

    def test_edit_post(self):
        """Валидная форма изменяет запись."""
        post = Post.objects.create(
            author=self.user,
            text='Очередной тестовый текст который я изменю.',
            group=self.group
        )
        context = {
            'text': 'А вот изменённый текст',
            'group': self.group.pk,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            context)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': post.pk}
        ))
        # Проверяем, что запись изменилась
        self.assertEqual(
            Post.objects.get(author=self.user).text,
            'А вот изменённый текст'
        )

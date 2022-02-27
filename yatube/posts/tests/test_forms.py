import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Post, Group, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


def ret_image():
    small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x02\x00'
        b'\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        b'\x0A\x00\x3B'
    )
    uploaded = SimpleUploadedFile(
        name='small.gif',
        content=small_gif,
        content_type='image/gif'
    )
    return uploaded


def ret_test_context_comment(self):
    post = Post.objects.create(
        author=self.user,
        text='Тестовый текст поста!',
    )
    context = {
        'post': post,
        'author': self.user,
        'text': 'Тестовый комментарий',
    }
    return context


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторзованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись."""
        context = {
            'text': 'Тестовый пост',
            'group': self.group.pk,
            'image': ret_image(),
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            context,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        ))
        # Проверяем, что создалась запись
        self.assertTrue(Post.objects.filter(
            author=self.user,
            text='Тестовый пост',
            group=self.group.pk,
            image='posts/small.gif'
        ).exists())

    def test_edit_post(self):
        """Валидная форма изменяет запись."""
        post = Post.objects.create(
            author=self.user,
            text='Очередной тестовый текст который я изменю.',
            group=self.group,
            image=ret_image(),
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

    def test_create_comment(self):
        """Форма комментария создает комментарий"""
        context = ret_test_context_comment(self)
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': context['post'].pk
            }),
            context)
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': context['post'].pk}
        ))
        # Проверяем, что создалась запись
        self.assertTrue(Comment.objects.filter(
            author=self.user,
            text='Тестовый комментарий',
            post=context['post'],
        ).exists())

    def test_no_add_nonauthorised_user_comment(self):
        """Неавторизованный пользователь не добавит комментарий"""
        context = ret_test_context_comment(self)
        comment_count = Post.objects.count()
        # Отправляем POST-запрос
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': context['post'].pk
            }),
            context)
        # Проверим что количество комментариев не изменилось.
        self.assertEqual(Post.objects.count(), comment_count)

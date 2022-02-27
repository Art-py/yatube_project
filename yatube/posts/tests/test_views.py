import shutil
import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Post, Group
from ..views import POSTS_CUT


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


COUNT_POSTS = 15


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


def create_posts(cls, count):
    image = ret_image()
    obj = [
        Post(
            pk=i,
            author=cls.user,
            text=f'Тестовый пост {i}',
            group=cls.group,
            image=image
        )
        for i in range(count)
    ]
    cls.post = Post.objects.bulk_create(obj)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Jack')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test-slug',
            description='Тестовое описание',
        )
        create_posts(cls, COUNT_POSTS)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post[0].id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post[0].id}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_context(self):
        """Тестирование страниц на наличие правильного контекста
         + паджинатор"""
        page_2 = '?page=2'
        second = COUNT_POSTS - POSTS_CUT
        response_tuple = (
            (POSTS_CUT, reverse('posts:index')),
            (second, reverse('posts:index') + page_2),
            (POSTS_CUT, reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            )),
            (second, reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ) + page_2),
            (POSTS_CUT, reverse(
                'posts:profile', kwargs={'username': self.user.username}
            )),
            (second, reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ) + page_2),
        )
        for count, template in response_tuple:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                self.assertEqual(len(response.context['page_obj']), count)

        template = reverse(
            'posts:post_detail', kwargs={'post_id': self.post[0].id}
        )
        response = self.authorized_client.get(template)
        self.assertEqual(response.context['post'].pk, self.post[0].id)

    def test_data_types_form(self):
        """Проверка страниц на наличие верных типов данных"""
        template_list = [reverse(
            'posts:post_edit', kwargs={'post_id': self.post[0].id}
        ),
            reverse('posts:post_create'),
        ]
        for template in template_list:
            response = self.authorized_client.get(template)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField
            }

            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_form_context(self):
        """Тестирование создания поста"""
        page = reverse(
            'posts:post_edit', kwargs={'post_id': self.post[0].id}
        )
        response = self.authorized_client.get(page)
        first_object = response.context['form'].initial['text']
        self.assertEqual(first_object, 'Тестовый пост 0')

    def test_pages_context_image(self):
        """Тестирование страниц на наличие картинки в постах"""
        last_post = 14
        response_list = (
            reverse('posts:index'),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            )
        )
        for template in response_list:
            with self.subTest(template=template):
                response = self.authorized_client.get(template)
                image_object = response.context['page_obj'][0].image
                self.assertEqual(image_object, self.post[last_post].image)
        # Отдельная страница поста
        template = reverse(
            'posts:post_detail', kwargs={'post_id': self.post[0].id}
        )
        response = self.authorized_client.get(template)
        self.assertEqual(response.context['post'].image, self.post[0].image)

    def tests_follow_unfollow(self):
        """Тест на подписку пользователя."""
        user_fol = User.objects.create_user(username='User_follow')
        authorized_client_follow = Client()
        authorized_client_follow.force_login(user_fol)
        # Подписались
        page_follow = reverse(
            'posts:profile_follow', kwargs={'username': self.user.username}
        )
        response = authorized_client_follow.get(page_follow)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def tests_unfollow(self):
        """Тест на отписку пользователя."""
        user_unfol = User.objects.create_user(username='User_unfollow')
        authorized_client_follow = Client()
        authorized_client_follow.force_login(user_unfol)
        # Отписались
        page_unfollow = reverse(
            'posts:profile_unfollow', kwargs={'username': self.user.username}
        )
        response = authorized_client_follow.get(page_unfollow)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def tests_add_follow_post(self):
        """Тест количества постов для пользователей"""
        # Количество постов у неподписанного пользователя.
        zero = 0
        num_new_post = 1
        # Создадим теперь двух авторизованных пользователей.
        # Этот подпишется
        user_fol = User.objects.create_user(username='User_follow')
        authorized_client_follow = Client()
        authorized_client_follow.force_login(user_fol)
        # А этот нет
        user_dont_fol = User.objects.create_user(username='User_unfollow')
        authorized_client_dont_follow = Client()
        authorized_client_dont_follow.force_login(user_dont_fol)
        # Тестируем сразу подписку на пользователя джека
        # Подписались
        page_follow = reverse(
            'posts:profile_follow', kwargs={'username': self.user.username}
        )
        authorized_client_follow.get(page_follow)
        # Создаем пост джеку
        Post.objects.create(
            author=self.user,
            text='Новый пост опубликованный после подписки на Джека.',
            group=self.group,
        )
        # Проверим что количество постов стало побольше у
        # подписанного пользователя и не изменилось у не подписанного.
        page_2 = '?page=2'
        second = COUNT_POSTS - POSTS_CUT + num_new_post
        response_tuple = (
            (POSTS_CUT, reverse('posts:follow_index')),
            (second, reverse('posts:follow_index') + page_2),
        )
        for count, template in response_tuple:
            with self.subTest(template=template):
                response = authorized_client_follow.get(template)
                self.assertEqual(len(response.context['page_obj']), count)

        response = authorized_client_dont_follow.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), zero)

    def test_cache_index_page(self):
        """Тестирование кэша"""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        cache_check = response.content
        post = Post.objects.get(pk=1)
        post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_check)

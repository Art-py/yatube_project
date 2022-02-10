from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group
from ..views import POSTS_CUT

User = get_user_model()


COUNT_POSTS = 15


def create_posts(cls, count):
    obj = [
        Post(
            pk=i,
            author=cls.user,
            text=f'Тестовый пост {i}',
            group=cls.group
        )
        for i in range(count)
    ]
    cls.post = Post.objects.bulk_create(obj)


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
        """Тестирование страниц на наличие правильного контекста"""
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
        page = reverse(
            'posts:post_edit', kwargs={'post_id': self.post[0].id}
        )
        response = self.authorized_client.get(page)
        first_object = response.context['form'].initial['text']
        self.assertEqual(first_object, 'Тестовый пост 0')

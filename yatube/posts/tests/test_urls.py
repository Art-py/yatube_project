from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()

        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_page(self):
        static_page = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.pk}/',
        ]

        for page in static_page:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_privat_page(self):
        static_page = [
            f'/posts/{self.post.pk}/edit/',
            '/create/',
        ]
        for page in static_page:
            with self.subTest(page=page):
                # Не авторизованный пользователь, гость
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_authorized_user_create(self):
        # Авторизованный пользователь, проверяем только страницу создания.
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_page_author(self):
        # Проверим что страница редактирования доступна только автору
        user = User.objects.create_user(username='Jack_Den')
        post = Post.objects.create(
            author=user,
            text='Текст который писали долго и упорно',
        )
        # Авторизуем Джека:
        authorized_author = Client()
        authorized_author.force_login(user)
        # Проверяем страницу на доступность
        page = f'/posts/{post.pk}/edit/'
        # для автора
        response = authorized_author.get(page)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # для авторизованного пользователя
        response = self.authorized_client.get(page)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unknown_page(self):
        page = '/unknown/'
        response = self.guest_client.get(page)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template_public_page(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/Test-slug/',
            'posts/profile.html': '/profile/HasNoName/',
            'posts/post_detail.html': f'/posts/{self.post.pk}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_privat_page(self):
        templates_url_names = {
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
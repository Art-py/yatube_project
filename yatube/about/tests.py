from http import HTTPStatus

from django.test import TestCase


class StaticURLTests(TestCase):

    def test_static_page(self):
        static_page = [
            '/about/author/',
            '/about/tech/'
        ]
        for page in static_page:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

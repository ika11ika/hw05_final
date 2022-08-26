# about/tests.py
from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()

        self.access_names = {
            reverse('about:author'): 'about/about.html',
            reverse('about:tech'): 'about/tech.html',
        }

    def test_access(self):
        for url in self.access_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_template_access(self):
        for url, template in self.access_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

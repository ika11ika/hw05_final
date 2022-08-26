# users/tests/test_urls.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from http import HTTPStatus
from users.forms import CreationForm
User = get_user_model()


class PostsURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.uidb64 = 'Wb'
        self.token = 'h234jkh2-j3h4'

        self.access_guest_names = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_reset_form'):
            'users/password_reset_form.html',
            reverse('users:password_reset_done'):
            'users/password_reset_done.html',
            reverse('users:password_reset_confirm',
                    kwargs={'uidb64': self.uidb64, 'token': self.token}):
            'users/password_reset_confirm.html',
            reverse('users:password_reset_complete'):
            'users/password_reset_complete.html',
        }

        self.access_authorised_names = {
            reverse('users:password_change'):
            'users/password_change_form.html',
            reverse('users:password_change_done'):
            'users/password_change_done.html',
        }

    def test_guest_access(self):
        """Доступность страниц неавторизованного пользователя"""
        for url in self.access_guest_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_template(self):
        """Доступность шаблонов страниц неавторизованного пользователя"""
        for url, template in self.access_guest_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_authorised_access(self):
        """Доступность страниц авторизованного пользователя"""
        for url in self.access_authorised_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorised_logout(self):
        """Доступность страницы выхода из ЛК"""
        response = self.authorized_client.get(reverse('users:logout'))
        self.assertTemplateUsed(response, 'users/logged_out.html')

    def test_authorised_password_change_done(self):
        """Доступность страницы успешной смены пароля"""
        response = self.authorized_client.get(
            reverse('users:password_change_done'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_signup_context(self):
        """Корректные данные в контексте страницы регистрации"""
        response = self.guest_client.get(reverse('users:signup'))
        form_field = response.context.get('form')
        self.assertIsInstance(form_field, CreationForm)

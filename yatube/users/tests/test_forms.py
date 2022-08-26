# users/tests/test_forms.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class SuccessfulPasswordChangeTests(TestCase):
    def setUp(self):
        self.data = {
            'old_password': 'old_password',
            'new_password1': 'new_password',
            'new_password2': 'new_password',
        }
        self.user2 = User.objects.create_user(
            username='john',
            email='john@doe.com',
            password='old_password'
        )

        self.guest_client = Client()
        self.url = reverse('users:password_change')
        self.guest_client.login(username='john', password='old_password')

    def test_authorised_password_change(self):
        """Редирект после отправки формы смены пароля"""
        response = self.guest_client.post(self.url, self.data)
        self.assertRedirects(response, reverse('users:password_change_done'))


class SuccessfulSignUpTests(TestCase):
    def setUp(self):
        url = reverse('users:signup')
        data = {
            'first_name': 'first_name',
            'second_name': 'second_name',
            'username': 'test-username',
            'email': 'email@email.ru',
            'password1': 'Sercret123',
            'password2': 'Sercret123',
        }
        guest_client = Client()
        self.users_count = User.objects.count()
        self.response = guest_client.post(url, data)
        self.redirect_url = reverse('posts:index')

    def test_client_create_account(self):
        """Редирект после отправки формы регистрации"""
        self.assertRedirects(self.response, self.redirect_url)

    def test_user_created(self):
        """Созданный пользователь появился в базе"""
        self.assertEqual(User.objects.count(), self.users_count + 1)
        self.assertTrue(
            User.objects.filter(
                first_name='first_name',
                username='test-username',
                email='email@email.ru'
            ).exists()
        )

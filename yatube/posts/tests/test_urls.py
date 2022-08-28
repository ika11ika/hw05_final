# posts/tests/test_urls.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=User.objects.create_user(username='hasNoName')
        )
        cls.group = Group.objects.create(
            description='Описание',
            title='Имя',
            slug='test-slug'
        )

    def setUp(self):
        self.guest_client = Client()

        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.authorized_author = Client()
        self.authorized_author.force_login(PostsURLTests.post.author)

        self.post = PostsURLTests.post
        self.group = PostsURLTests.group
        cache.clear()

        self.access_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk}):
            'posts/post_detail.html',
        }

    def test_access(self):
        """Проверка доступности страниц неавторизованных пользователей"""
        for url in self.access_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_template_access(self):
        """Проверка доступности шаблонов"""
        for url, template in self.access_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Проверка ошибки для неуществующих страниц"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_create_page(self):
        """Проверка доступности страницы создания поста"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_page(self):
        """Проверка доступности страницы редактирования поста"""
        response = self.authorized_author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

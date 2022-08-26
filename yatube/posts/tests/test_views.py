# posts/tests/test_views.py
import shutil
import tempfile
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from datetime import datetime
from posts.models import Post, Group, User, Follow
from posts.forms import PostForm
from django.core.paginator import Page
from django.conf import settings


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()
POSTS_PER_PAGE = 10


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            description='Описание',
            title='Имя',
            slug='test-slug'
        )
        cls.author_user = User.objects.create_user(username='hasNoName')
        cls.follower_user = User.objects.create_user(username='Follower')
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
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=PostsViewsTests.author_user,
            image=uploaded,
            group=PostsViewsTests.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()

        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTests.post.author)

        self.authorized_client2 = Client()
        self.authorized_client2.force_login(PostsViewsTests.follower_user)

        cache.clear()

    def check_form_fields_list(self, response, form_fields):
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',

            reverse('posts:group_list',
                    kwargs={'slug': PostsViewsTests.group.slug}):
                        'posts/group_list.html',

            reverse('posts:profile',
                    kwargs={'username': PostsViewsTests.post.author}):
                        'posts/profile.html',

            reverse('posts:post_detail',
                    kwargs={'post_id': PostsViewsTests.post.pk}):
                        'posts/post_detail.html',

            reverse('posts:post_create'): 'posts/create_post.html',

            reverse('posts:post_edit',
                    kwargs={'post_id': PostsViewsTests.post.pk}):
                        'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Корректные данные в контексте главой страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        form_field = response.context.get('page_obj')
        self.assertIsInstance(form_field, Page)

    def test_group_list_show_correct_context(self):
        """Корректные данные в контексте страницы повтов группы"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostsViewsTests.group.slug})
        )
        form_fields = {
            'group': Group,
            'page_obj': Page,
        }

        self.check_form_fields_list(response, form_fields)

    def test_profile_show_correct_context(self):
        """Корректные данные в контексте страницы постов автора"""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostsViewsTests.post.author})
        )
        form_fields = {
            'page_obj': Page,
            'author': User,
            'posts_amount': int,
        }

        self.check_form_fields_list(response, form_fields)

    def test_post_detail_show_correct_context(self):
        """Корректные данные в контексте страницы поста"""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostsViewsTests.post.pk})
        )
        form_fields = {
            "post": Post,
            "post_title": str,
            "pub_date": datetime,
            "author": User,
            "author_posts_amount": int,
        }

        self.check_form_fields_list(response, form_fields)

    def test_post_edit_show_correct_context(self):
        """Корректные данные в контексте страницы редактирования поста"""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsViewsTests.post.pk})
        )
        form_fields = {
            "is_edit": bool,
            "form": PostForm,
        }

        self.check_form_fields_list(response, form_fields)

    def test_post_create_show_correct_context(self):
        """Корректные данные в контексте страницы создания поста"""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        form_field = response.context.get('form')
        self.assertIsInstance(form_field, PostForm)

    def test_created_post_not_in_other_group(self):
        """Созданный пост с группой не попал в другую группу"""
        fake_group = Group.objects.create(
            description='fake_group',
            title='fake_group',
            slug='test-fake-slug'
        )
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': fake_group.slug})
        )
        self.assertTrue(self.post not in response.context['page_obj'])

    def test_post_appeared_on_pages_after_create(self):
        """Созданный пост появился на всех нужных страницах"""
        pages = {
            'index': self.authorized_client.get(reverse('posts:index')),
            'group_list': self.authorized_client.get(
                reverse('posts:group_list',
                        kwargs={'slug': PostsViewsTests.group.slug})
            ),
            'profile': self.authorized_client.get(
                reverse('posts:profile',
                        kwargs={'username': PostsViewsTests.post.author})
            )
        }
        for _, response in pages.items():
            with self.subTest(response=response):
                self.assertTrue(self.post in response.context['page_obj'])

    def test_index_context_posts_have_images(self):
        """Проверяем что в постах контекта главной страницы есть картинки"""
        response = self.guest_client.get(
            reverse('posts:index')
        )
        post_image = response.context['page_obj'][0].image
        self.assertEqual(post_image, PostsViewsTests.post.image)

    def test_profile_context_posts_have_images(self):
        """Проверяем что в постах контекта страницы профиля есть картинки"""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': PostsViewsTests.post.author})
        )
        post_image = response.context['page_obj'][0].image
        self.assertEqual(post_image, PostsViewsTests.post.image)

    def test_group_list_context_posts_have_images(self):
        """Проверяем что в постах контекта страницы группы есть картинки"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostsViewsTests.group.slug})
        )
        post_image = response.context['page_obj'][0].image
        self.assertEqual(post_image, PostsViewsTests.post.image)

    def test_post_detail_context_has_image(self):
        """Проверяем что в контекст страницы поста есть картинка"""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostsViewsTests.post.pk})
        )
        post_image = response.context['post'].image
        self.assertEqual(post_image, PostsViewsTests.post.image)

    def test_cache_index_page(self):
        """Проверяем работу кеширования главной страницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(
            text='Пост, который появится не сразу',
            pub_date='Дата, которая тоже появится не сразу',
            author=PostsViewsTests.author_user,
        )
        update_response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, update_response.content)

    def test_autherised_can_follow(self):
        """Проверяем возможность подписки авторизованного пользователя"""
        followers_count = Follow.objects.count()
        response = self.authorized_client2.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostsViewsTests.author_user}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': PostsViewsTests.author_user})
        )
        self.assertEqual(Follow.objects.count(), followers_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=PostsViewsTests.follower_user,
                author=PostsViewsTests.author_user,
            ).exists()
        )

    def test_autherised_can_unfollow(self):
        """Проверяем возможность отписки авторизованного пользователя"""
        Follow.objects.create(
            user=PostsViewsTests.follower_user,
            author=PostsViewsTests.author_user,
        )
        followers_count = Follow.objects.count()
        response = self.authorized_client2.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostsViewsTests.author_user}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': PostsViewsTests.author_user})
        )
        self.assertEqual(Follow.objects.count(), followers_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=PostsViewsTests.follower_user,
                author=PostsViewsTests.author_user,
            ).exists()
        )

    def test_created_post_on_follow_page(self):
        """Созданный пост добавлен на страницу подписок"""
        Follow.objects.create(
            user=PostsViewsTests.follower_user,
            author=PostsViewsTests.author_user,
        )
        response = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        self.assertTrue(self.post in response.context['page_obj'])

    def test_created_post_on_follow_page(self):
        """Пост неотслеживаемого автора не появляется на страницу подписок"""
        Follow.objects.create(
            user=PostsViewsTests.follower_user,
            author=PostsViewsTests.author_user,
        )
        unfollowed_author_user = User.objects.create_user(username='Scribbler')
        unfollowed_author_post = Post.objects.create(
            text='Пост, который никому не нужен',
            pub_date='Тестовая дата, на которую никто не посмотрит',
            author=unfollowed_author_user,
        )
        response = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        self.assertTrue(
            unfollowed_author_post not in response.context['page_obj']
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            description='Описание',
            title='Имя',
            slug='test-slug'
        )

        cls.author_user = User.objects.create_user(username='hasNoName')
        posts_list = [
            Post(
                text='Тест. текст ' + str(i),
                pub_date='Тестовая дата ' + str(i),
                author=PaginatorViewsTest.author_user,
                group=PaginatorViewsTest.group
            )
            for i in range(POSTS_PER_PAGE)
        ]
        Post.objects.bulk_create(posts_list)
        cls.posts = Post.objects.all()
        cls.post = PaginatorViewsTest.posts[0]

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def page_contain_ten_records(self, response):
        """На странице доступно заданное число постов"""
        self.assertEqual(len(response.context['page_obj']), POSTS_PER_PAGE)

    def test_index_pagination(self):
        """Правильная пагинация на главной странице"""
        response = self.guest_client.get(reverse('posts:index'))
        self.page_contain_ten_records(
            response=response
        )

    def test_group_list_pagination(self):
        """Правильная пагинация на странице группы"""
        response = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': PaginatorViewsTest.group.slug})
        )
        self.page_contain_ten_records(
            response=response
        )

    def test_profile_pagination(self):
        """Правильная пагинация на странице пользователя"""
        response = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.post.author})
        )
        self.page_contain_ten_records(
            response=response
        )

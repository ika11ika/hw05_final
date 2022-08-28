# posts/tests/test_forms.py
import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            description='Описание',
            title='Имя',
            slug='test-slug'
        )

        cls.author_user = User.objects.create_user(
            username='hasNoName',
            password='test'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.img_uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.guest_client.force_login(PostCreateFormTests.author_user)

    def test_create_post(self):
        """Форма создания поста добавляет пост"""
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Я не люблю тестирование!',
            'group': PostCreateFormTests.group.pk,
            'image': PostCreateFormTests.img_uploaded
        }

        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': PostCreateFormTests.author_user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostCreateFormTests.author_user,
                group=form_data['group'],
                image=f"posts/{form_data['image']}"
            ).exists()
        )
        self.assertTrue(
            Post.objects.latest('pub_date') in
            Post.objects.filter(
                text=form_data['text'],
                author=PostCreateFormTests.author_user,
                group=form_data['group'],
                image=f"posts/{form_data['image']}"
            )
        )
        latest_object = Post.objects.latest('pub_date')
        self.assertTrue(
            (
                latest_object.text == form_data['text']
                and latest_object.group.pk == form_data['group']
                and latest_object.image == f"posts/{form_data['image']}")
        )


class PostEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.group = Group.objects.create(
            description='Описание',
            title='Имя',
            slug='test-slug'
        )

        cls.author_user = User.objects.create_user(
            username='hasNoName',
            password='test'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=PostEditFormTests.author_user,
            group=PostEditFormTests.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.guest_client.force_login(PostEditFormTests.author_user)

    def test_edit_post(self):
        """Форма редактирования поста изменяет пост"""
        posts_count = Post.objects.count()
        fake_group = Group.objects.create(
            description='Описание2',
            title='Имя2',
            slug='test-slug2'
        )

        form_data = {
            'text': 'Я терпеть не могу тестирование!',
            'group': fake_group.pk
        }

        response = self.guest_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostEditFormTests.post.pk}
            ),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                "posts:post_detail",
                kwargs={'post_id': PostEditFormTests.post.pk}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostEditFormTests.author_user,
                group=fake_group
            ).exists()
        )
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый текст',
                author=PostCreateFormTests.author_user,
                group=PostEditFormTests.group
            ).exists()
        )


class PostCommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            description='Описание',
            title='Имя',
            slug='test-slug'
        )
        cls.author_user = User.objects.create_user(
            username='hasNoName',
            password='test'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=PostCommentFormTests.author_user,
            group=PostCommentFormTests.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCommentFormTests.author_user)

    def test_comment_login_required(self):
        """Проверяем что попытка комментария анонима отправляет на логин"""
        form_data = {'text': 'Я терпеть не могу тестирование!'}
        url = reverse(
            'posts:add_comment',
            kwargs={'post_id': PostCommentFormTests.post.pk}
        )
        response = self.guest_client.post(url, data=form_data)
        login_url = reverse('users:login')
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            len(Comment.objects.filter(post=PostCommentFormTests.post)) == 0
        )
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_comment_appeared_after_create(self):
        """Проверяем что коммент появился"""
        form_data = {'text': 'Я терпеть не могу тестирование!'}
        comments_count = Comment.objects.count()

        add_comment_url = reverse(
            'posts:add_comment',
            kwargs={'post_id': PostCommentFormTests.post.pk}
        )

        post_detail_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCommentFormTests.post.pk}
        )

        response = self.authorized_client.post(add_comment_url, data=form_data)
        latest_comment = Comment.objects.latest('created')

        page_comments = self.authorized_client.get(
            post_detail_url
        ).context.get('comments')

        self.assertRedirects(
            response,
            post_detail_url
        )
        self.assertTrue(
            (
                latest_comment.text == form_data['text']
                and latest_comment.author == PostCommentFormTests.author_user)
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(latest_comment in page_comments)

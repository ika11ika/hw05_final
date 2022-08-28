from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

POSTS_AMOUNT = 10


@cache_page(20, key_prefix="index_page")
def index(request):
    posts = Post.objects.all()
    page_obj = paginate_posts(request, posts)
    template = 'posts/index.html'

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = paginate_posts(request, posts)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'

    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    posts_amount = author.posts.count()

    page_obj = paginate_posts(request, posts)
    following = False
    if request.user.is_authenticated:
        following = (Follow.objects.filter(
            user=request.user,
            author=User.objects.filter(username=username)[0]).exists)
    context = {
        'page_obj': page_obj,
        'author': author,
        'posts_amount': posts_amount,
        'following': following,
    }
    return render(request, template, context)


def paginate_posts(request, posts):
    paginator = Paginator(posts, POSTS_AMOUNT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


def post_detail(request, post_id):
    template = 'posts/post_detail.html'

    post = get_object_or_404(Post, pk=post_id)
    post_title = post.text[:30]
    post_pub_date = post.pub_date
    author = post.author
    author_posts_amount = author.posts.all().count()
    comment_form = CommentForm(request.POST or None)
    post_comments = post.comments.all()

    context = {
        "post": post,
        "post_title": post_title,
        "pub_date": post_pub_date,
        "author": author,
        "author_posts_amount": author_posts_amount,
        "comment_form": comment_form,
        "comments": post_comments,
    }

    return render(request, template, context)


@login_required
def post_create(request):

    template = "posts/create_post.html"
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)

    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:profile", post.author)

    context = {
        "form": form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):

    template = "posts/create_post.html"

    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )

    if request.user == author:
        if request.method == "POST" and form.is_valid:
            post = form.save()
            return redirect("posts:post_detail", post_id)

        context = {
            "is_edit": is_edit,
            "form": form,
        }

        return render(request, template, context)
    return redirect("posts:post_detail", post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    authors = Follow.objects.filter(user=request.user)
    posts = []
    for note in authors:
        posts.extend(Post.objects.filter(author=note.author))
    page_obj = paginate_posts(request, posts)
    template = 'posts/follow.html'

    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    redirect_page = reverse('posts:profile', kwargs={'username': username})
    try:
        Follow.objects.create(
            user=request.user,
            author=User.objects.filter(username=username)[0]
        )
    except IntegrityError:
        return redirect(redirect_page)
    return redirect(redirect_page)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author=User.objects.filter(username=username)[0]
    ).delete()
    print(
        Follow.objects.filter(
            user=request.user,
            author=User.objects.filter(username=username)[0]
        )
    )
    redirect_page = reverse('posts:profile', kwargs={'username': username})
    return redirect(redirect_page)

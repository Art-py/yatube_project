from django.shortcuts import (render,
                              get_object_or_404,
                              redirect,
                              get_list_or_404)
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Follow
from .utils import get_pagi
from .forms import PostForm, CommentForm


POSTS_CUT = 10


def index(request):
    page_obj = get_pagi(Post.objects.all(), POSTS_CUT)
    title = 'Последние обновления на сайте'
    context = {
        'page_obj': page_obj.get_page(request.GET.get('page')),
        'title': title,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = get_pagi(get_list_or_404(Post, group=group), POSTS_CUT)
    context = {
        'group': group,
        'page_obj': page_obj.get_page(request.GET.get('page')),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    page_obj = get_pagi(author.posts.all(), POSTS_CUT)
    following = (request.user.is_authenticated and author.following.filter(
        user=request.user).exists())

    context = {
        'author': author,
        'page_obj': page_obj.get_page(request.GET.get('page')),
        'page_count': page_obj.count,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    cut_str = 30
    post = get_object_or_404(Post, id=post_id)
    count_posts = post.author.posts.count()
    context = {
        'cut_str': cut_str,
        'post': post,
        'count_posts': count_posts,
        'comments': post.comments.all(),
        'form': CommentForm()
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('posts:profile', username=request.user.username)
    context = {
        'form': form,
        'header': 'Добавить запись',
        'is_edit': False,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)
    if edit_post.author == request.user:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=edit_post
        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
        context = {
            'form': form,
            'header': 'Редактировать запись',
            'is_edit': True,
        }
        return render(request, 'posts/create_post.html', context)

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = Post.objects.get(id=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    page_obj = get_pagi(Post.objects.filter(
        author__following__user=request.user
    ), POSTS_CUT)
    title = 'Подписки'
    context = {
        'page_obj': page_obj.get_page(request.GET.get('page')),
        'title': title,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)

from django.shortcuts import render, get_object_or_404
from .models import Post, Group

SLICE = 10


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group')[:SLICE]
    title = 'Последние обновления на сайте'
    context = {
        'posts': posts,
        'title': title,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group).select_related('group')[:SLICE]
    context = {
        'group': group,
        'posts': posts,
    }
    return render(request, template, context)

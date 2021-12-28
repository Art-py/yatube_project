from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse(f'Понеслась!')

def group_posts(request, slug):
    return HttpResponse(f'Привет! {slug}')

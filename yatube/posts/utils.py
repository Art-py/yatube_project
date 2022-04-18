from django.core.paginator import Paginator


def get_pagi(in_list, cut):
    return Paginator(in_list, cut)

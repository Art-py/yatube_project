from django.core.paginator import Paginator


def ret_pagi(in_list, cut):
    return Paginator(in_list, cut)

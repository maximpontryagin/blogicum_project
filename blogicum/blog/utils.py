from django.db.models import Count

from .config import DATETIME_NOW


def select(model):
    return model.objects.select_related(
        'author', 'location', 'category').filter(
            is_published=True, pub_date__lte=DATETIME_NOW,
            category__is_published=True)


def anotate(queryset):
    return queryset.prefetch_related('comments').annotate(
        comment_count=Count('comments')).order_by('-pub_date')

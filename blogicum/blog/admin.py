from django.contrib import admin

from .models import Category, Location, Post, Comment


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'text',
        'pub_date',
        'author',
        'location',
        'is_published',
        'created_at',
    )
    list_editable = (
        'is_published',
    )
    search_fields = (
        'title',
        'location',
        'text',
        'author',
    )
    list_filter = (
        'is_published',
        'location',
        'author',
    )


admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Location)
admin.site.register(Comment)

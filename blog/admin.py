from django.contrib import admin
from .models import Post, Tag


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}  # Auto-generate slug from title
    list_display = ('title', 'author', 'published_date', 'is_published', 'tag_list')  # Include tags
    search_fields = ('title', 'content')
    list_filter = ('is_published', 'author', 'tags')  # Filter by tags
    autocomplete_fields = ['tags']  # Enable tag autocomplete
    ordering = ('-published_date',)  # Default ordering

    def tag_list(self, obj):
        """Display tags as a comma-separated list in the admin."""
        return ", ".join(tag.name for tag in obj.tags.all())
    tag_list.short_description = 'Tags'  # Set column header in the admin


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)  # Allow searching for tags in the admin
    list_display = ('name',)  # Display tag name in list view
    ordering = ('name',)  # Order tags alphabetically

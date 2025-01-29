from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views

urlpatterns = [
    path('test-blog-post/', views.test_blog_post, name='test_blog_post'),
    path('', views.post_list, name='post_list'),  # Blog homepage
    path('<slug:slug>/', views.blog_post, name='blog_post'),  # Individual post page
    path('email_signup/', views.email_signup, name='email_signup'),  # Route for form processing
    path('tinymce/', include('tinymce.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

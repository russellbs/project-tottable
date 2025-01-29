from django.shortcuts import render, get_object_or_404, redirect
from .models import Post
from .forms import EmailSignupForm

def post_list(request):
    posts = Post.objects.filter(is_published=True).order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})

def blog_post(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    page_title = f"{post.title} | Tottable"

    # Split content into paragraphs
    paragraphs = [p.strip() for p in post.content.split("\n") if p.strip()]

    # Handle the form submission for email signup
    if request.method == 'POST':
        form = EmailSignupForm(request.POST)
        if form.is_valid():
            # Process form data
            day = form.cleaned_data['day']
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            email = form.cleaned_data['email']
            # Here you could save the data, send a welcome email, etc.
            return redirect('success_page')  # Adjust as needed, e.g., redirect to a thank-you page
    else:
        form = EmailSignupForm()

    return render(request, 'blog/blog_post.html', {
        'post': post,
        'page_title': page_title,
        'form': form,
        'paragraphs': paragraphs,  # Add paragraphs to the context
    })


def test_blog_post(request):
    # Sample data to simulate a blog post for testing layout
    sample_post = {
        'title': 'Why Skin-to-Skin Time Isn’t Just for the Hospital',
        'content': [
            "Skin-to-skin time might feel most natural right after your baby is born...",
            "The incredible physiological benefits for babies include helping their digestive systems...",
            "If you’re feeling down, worried, or anxious—and what new parent isn’t...",
        ],
        'image_url': 'https://via.placeholder.com/800x500',
        'author': 'Team Tottable',
        'tags': ['Bonding', 'Playtime & Activities', 'Child Development'],
        'related_posts': [
            {
                'title': 'Our award-winning Play Gym just got an update—see what’s new',
                'image_url': 'https://via.placeholder.com/300x200',
                'tag': 'Playtime & Activities'
            },
            {
                'title': 'Newborn safety basics for new parents',
                'image_url': 'https://via.placeholder.com/300x200',
                'tag': '0 - 12 Weeks'
            },
            {
                'title': 'Your newborn knows you by scent and sound',
                'image_url': 'https://via.placeholder.com/300x200',
                'tag': '0 - 12 Weeks'
            }
        ]
    }
    return render(request, 'blog/blog_post.html', {'post': sample_post, 'page_title': "Sample Blog Post | Tottable"})

def email_signup(request):
    if request.method == "POST":
        form = EmailSignupForm(request.POST)
        if form.is_valid():
            # Process form data (e.g., save it, send an email, etc.)
            form.save()
            # Redirect back to the current page or a success page
            return redirect('success_page')  # Define this route for success
    else:
        form = EmailSignupForm()

    # If GET or form invalid, reload the form (optional)
    return render(request, 'blog/email_signup.html', {'form': form})

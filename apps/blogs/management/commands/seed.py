from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Populate the database with test data"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database...")

        self._create_superuser()
        self._create_users()
        self._create_categories()
        self._create_tags()
        self._create_posts_and_comments()

        self.stdout.write(self.style.SUCCESS("Setup completed!"))
        self.stdout.write("")
        self.stdout.write("Superuser:")
        self.stdout.write("  Email: admin@admin.com")
        self.stdout.write("  Password: admin123")
        self.stdout.write("")
        self.stdout.write("Test users:")
        self.stdout.write("  user1@test.com - user5@test.com")
        self.stdout.write("  Password: testtest123")

    def _create_superuser(self):
        if not User.objects.filter(email="admin@admin.com").exists():
            User.objects.create_superuser(
                email="admin@admin.com",
                password="admin123",
                first_name="Admin",
                last_name="Adminovich",
            )
            self.stdout.write(self.style.SUCCESS("Superuser created"))
        else:
            self.stdout.write("Superuser already exists, skipping")

    def _create_users(self):
        self.users = []
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                email=f"user{i}@test.com",
                defaults={
                    "first_name": f"User{i}",
                    "last_name": "Test",
                },
            )
            if created:
                user.set_password("testtest123")
                user.save()
            self.users.append(user)
        self.stdout.write(self.style.SUCCESS("Users ready"))

    def _create_categories(self):
        from apps.blogs.models import Category, CategoryTranslation

        self.categories = []

        data = [
            ("Technology", "tech", [("en", "Technology"), ("ru", "Технологии"), ("kk", "Технологиялар")]),
            ("Lifestyle", "lifestyle", [("en", "Lifestyle"), ("ru", "Образ жизни"), ("kk", "Өмір салты")]),
            ("News", "news", [("en", "News"), ("ru", "Новости"), ("kk", "Жаңалықтар")]),
        ]

        for name, slug, translations in data:
            cat, created = Category.objects.get_or_create(
                slug=slug,
                defaults={"name": name},
            )
            for language, translation_name in translations:
                CategoryTranslation.objects.get_or_create(
                    category=cat,
                    language=language,
                    defaults={"name": translation_name},
                )
            self.categories.append(cat)

        self.stdout.write(self.style.SUCCESS("Categories ready"))
    def _create_tags(self):
        from apps.blogs.models import Tag

        self.tags = []
        tags_data = ["python", "django", "kbtu", "news", "review"]
    
        for name in tags_data:
            tag, _ = Tag.objects.get_or_create(
                slug=name,
                defaults={"name": name},
            )
            self.tags.append(tag)

        self.stdout.write(self.style.SUCCESS("Tags ready"))

    def _create_posts_and_comments(self):
        from apps.blogs.models import Post, Comment
        from django.utils.text import slugify

        if Post.objects.exists():
            self.stdout.write("Posts already exist, skipping")
            return

        for i in range(15):
            title = f"Post {i + 1}"
            post = Post.objects.create(
                title=title,
                slug=slugify(title),  
                body=f"This is the content of post {i + 1}. " * 20,
                author=self.users[i % 5],
                category_id=self.categories[i % 3],
                status="published" if i % 4 != 0 else "draft",
            )
            post.tags.set([self.tags[i % 5]])

        for post in Post.objects.all():
            for j in range(2):
                Comment.objects.create(
                    post=post,
                    author=self.users[j % 5],
                    body=f"Comment {j + 1} on {post.title}",
                )

        self.stdout.write(self.style.SUCCESS("Created 15 posts and 30 comments"))
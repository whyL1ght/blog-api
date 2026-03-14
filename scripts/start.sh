#!/bin/bash

set -e

echo "============================================="

echo "Starting script for advanced django project"

echo "============================================="

echo ""
echo "Checking env variables.."

if [ ! -f ".env"]; then
    echo "Error: .env file not found"
    echo "Please create it: cp .env.example .env"
    exit 1
fi

source .env

if [ -z "$REDIS_HOST" ]; then
    echo "Error: Missing variable: REDIS_HOST"
    exit 1
fi

if [ -z "$REDIS_PORT"]; then
    echo "Errod: Missing variable: REDIS_PORT"
    exit 1
fi

echo "Env variables OK"

echo ""
echo "Setting up virtual env"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Venv created"
else
    echo "Venv already exists"
fi

source venv/bin/activate
pip3 install -r requirements/base.txt
echo "Dependencies installed"

echo ""
echo "Running migrations"
python3 manage.py migrate
echo "Migrations complete"

echo ""
echo "Collecting static files"
python3 manage.py collectstatic --noinput --clear > /dev/null 2>&1 || echo "Static files skipped"

echo ""
echo "Compliting translations"
if command -v msgfmt > /dev/null 2>&1; then
    python3 manage.py compilemessages > /dev/null 2>&1
    echo "Translations complied"
else
    echo "gettext not found, skipping translations"
fi

echo ""
echo "Creating superuser"

python3 manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@admin.com').exists():
    User.objects.create_superuser(
        email = 'admin@admin.com',
        password = 'admin123',
        first_name = 'Admin',
        last_name = 'Adminovich'
    )
    print('Superuser created')
else:
    print('Superuser already exists)
EOF

echo ""
echo "Seeding test data.."

python3 manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from apps.blogs.models import Category, CategoryTranslation, Tag, Post, Comment

User = get_user_model()

if Post.objects.exists():
    print('Test data already exists')
else:
    # Create 5 test users
    users = []
    for i in range(1, 6):
        user = User.objects.create_user(
            email=f'user{i}@test.com,
            password=testtest123,
            first_name=f'User{i}',
            last_name='Test'
        )
        users.append(user)

    # Create 3 categories with translations
    cat1 = Category.objects.create(slug='tech')
    CategoryTranslation.objects.create(category=cat1, language="en", name="Technology")
    CategoryTranslation.objects.create(category=cat1, language="ru", name="Технологии")
    CategoryTranslation.objects.create(category=cat1, language="kk", name="Технологиялар")

    cat2 = Category.objects.create(slug="lifestyle")
    CategoryTranslation.objects.create(category=cat2, language="en", name="Lifestyle")
    CategoryTranslation.objects.create(category=cat2, language="ru", name="Образ жизни")
    CategoryTranslation.objects.create(category=cat2, language="kk", name="Өмір салты")

    cat3 = Category.objects.create(slug="news")
    CategoryTranslation.objects.create(category=cat3, language="en", name="News")
    CategoryTranslation.objects.create(category=cat3, anguage="ru",name="Новости")
    CategoryTranslation.objects.create(category=cat3, language="kk", name="Жаңалықтар")

    categories = [cat1, cat2, cat3]

    # Create 5 tags
    tag1 = Tag.objects.create(name='python')
    tag2 = Tag.objects.create(name='django')
    tag3 = Tag.objects.create(name='kbtu')
    tag4 = Tag.objects.create(name='news')
    tag5 = Tag.objects.create(name='review')
    tags = [tag1, tag2, tag3, tag4, tag5]

    # Create 15 posts
    for i in range(15):
        post = Post.objects.create(
            title=f'Post{i+1}',
            body=f'This is the content of post {i+1}' * 20,
            author=users[i % 5],
            category=categories[i % 3]
            status='published' if i % 4 != 0 else 'draft'
        )
        post.tags.set([tags[i % 5]])

        # Create 30 comments (2 per first 15 posts)
        for post in Post.objects.all():
            for j in range(2):
                Comment.objects.create(
                    post=post,
                    author=users[j % 5],
                    body=f'Comment {j+1} on {post.title}'
                    )
        
        print('Test data created')
        print(' - 5 users')
        print(' - 3 categories')
        print(' - 5 tags')
        pront(' - 15 posts')
        print(' - 30 comments')
EOF

echo ""
echo "Setup complited"
echo ""
echo "URLs:"
echo " API: http://127.0.0.1:8000/api/"
echo " ReDoc: http://127.0.0.1:8000/api/docs/redoc/"
echo " Swagger: http://127.0.0.1:800/api/dosc/swagger-ui/"
echo ""
echo "Superuser"
echo "Email: admin@admin.com"
echo "Password: admin123"
echo ""
echo "Test users"
echo " user1@test.com - user5@test.com"
echo " Password: testtest123"
echo ""

python3 manage.py runserver


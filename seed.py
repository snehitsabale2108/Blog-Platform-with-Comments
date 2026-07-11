"""
Inkwell Blog Platform – Database Seed Script
Run: python seed.py
Creates sample users, categories, tags, posts, comments
"""
import os
import sys

# Ensure we're in the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
from app.models import User, Post, Comment, Category, Tag, Like, Follow, Bookmark
from datetime import datetime, timedelta
import random

app = create_app("development")

CATEGORIES = [
    {"name": "Technology",   "slug": "technology",   "color": "#3b82f6", "icon": "bi-cpu",          "description": "All things tech"},
    {"name": "Design",       "slug": "design",       "color": "#8b5cf6", "icon": "bi-pen",           "description": "UI/UX and visual design"},
    {"name": "Science",      "slug": "science",      "color": "#10b981", "icon": "bi-flask",         "description": "Scientific discoveries"},
    {"name": "Business",     "slug": "business",     "color": "#f59e0b", "icon": "bi-briefcase",     "description": "Startups, finance, leadership"},
    {"name": "Health",       "slug": "health",       "color": "#ef4444", "icon": "bi-heart-pulse",   "description": "Wellness and fitness"},
    {"name": "Culture",      "slug": "culture",      "color": "#ec4899", "icon": "bi-music-note",    "description": "Arts, books, movies"},
]

TAGS = ["python", "flask", "javascript", "react", "ai", "machinelearning", "productivity",
        "webdev", "design", "ux", "startup", "writing", "motivation", "travel", "photography"]

LOREM = """<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
<h2>The Challenge</h2>
<p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
<blockquote>The best way to predict the future is to invent it. — Alan Kay</blockquote>
<h2>The Solution</h2>
<p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.</p>
<h3>Implementation Details</h3>
<ul>
<li>First important point about the implementation</li>
<li>Second consideration that matters a lot</li>
<li>Third detail about performance and scalability</li>
</ul>
<p>Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.</p>
<pre><code>def hello_world():
    return "Hello, Inkwell!"

print(hello_world())</code></pre>
<p>At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium voluptatum deleniti atque corrupti quos dolores et quas molestias.</p>
<h2>Conclusion</h2>
<p>Nam libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus.</p>"""

POSTS_DATA = [
    ("Building a Modern Blog with Flask and Bootstrap 5",           "technology", ["python","flask","webdev"]),
    ("The Future of AI: What Every Developer Should Know in 2024",  "technology", ["ai","machinelearning"]),
    ("10 UX Principles That Will Transform Your Products",          "design",     ["ux","design"]),
    ("From Zero to $1M ARR: Lessons from My Startup Journey",       "business",   ["startup","motivation"]),
    ("How to Write Code That Your Future Self Will Thank You For",  "technology", ["python","productivity"]),
    ("The Science of Deep Focus: A Developer's Guide",              "science",    ["productivity"]),
    ("Designing for Dark Mode: A Complete Guide",                   "design",     ["design","ux"]),
    ("TypeScript vs JavaScript: Which Should You Choose?",          "technology", ["javascript","webdev"]),
    ("The Minimalist Developer: Doing More with Less",              "culture",    ["productivity","writing"]),
    ("Machine Learning in Healthcare: Promise and Peril",           "health",     ["machinelearning","ai"]),
    ("Building Accessible Web Apps: The Complete Checklist",        "technology", ["webdev","design"]),
    ("Photography Composition Masterclass for Beginners",           "culture",    ["photography"]),
]

def seed():
    with app.app_context():
        print("Dropping and recreating tables...")
        db.drop_all()
        db.create_all()

        # ── Categories ──
        cats = {}
        for c in CATEGORIES:
            cat = Category(**c)
            db.session.add(cat)
            cats[c["slug"]] = cat

        # ── Tags ──
        tags = {}
        for t in TAGS:
            tag = Tag(name=t, slug=t.lower().replace(" ", "-"))
            db.session.add(tag)
            tags[t] = tag

        db.session.flush()

        # ── Users ──
        admin = User(
            username="admin",
            email="admin@inkwell.com",
            display_name="Inkwell Admin",
            bio="Platform administrator and avid reader.",
            role="admin",
            is_active=True,
            is_email_verified=True,
            created_at=datetime.utcnow() - timedelta(days=120),
        )
        admin.set_password("Admin1234!")

        alice = User(
            username="alice",
            email="alice@inkwell.com",
            display_name="Alice Chen",
            bio="Senior software engineer. Writes about Python, distributed systems, and coffee.",
            role="author",
            is_active=True,
            is_email_verified=True,
            created_at=datetime.utcnow() - timedelta(days=90),
            twitter="alicechen",
            github="alicechen",
        )
        alice.set_password("Alice1234!")

        bob = User(
            username="bob",
            email="bob@inkwell.com",
            display_name="Bob Martinez",
            bio="Designer and UX researcher. Passionate about clean, accessible interfaces.",
            role="author",
            is_active=True,
            is_email_verified=True,
            created_at=datetime.utcnow() - timedelta(days=75),
            twitter="bobmartinez",
        )
        bob.set_password("Bob12345!")

        carol = User(
            username="carol",
            email="carol@inkwell.com",
            display_name="Carol Park",
            bio="Startup founder and product thinker. Writing about building things that matter.",
            role="author",
            is_active=True,
            is_email_verified=True,
            created_at=datetime.utcnow() - timedelta(days=60),
        )
        carol.set_password("Carol123!")

        users = [admin, alice, bob, carol]
        for u in users:
            db.session.add(u)
        db.session.flush()

        # ── Follows ──
        alice.follow(bob); alice.follow(carol)
        bob.follow(alice); carol.follow(alice); carol.follow(bob)

        # ── Posts ──
        authors = [alice, alice, bob, carol, alice, bob, bob, carol, alice, carol, bob, carol]
        created_posts = []

        for i, (title, cat_slug, tag_names) in enumerate(POSTS_DATA):
            author = authors[i % len(authors)]
            pub_date = datetime.utcnow() - timedelta(days=random.randint(1, 80))
            post = Post(
                title=title,
                content=LOREM,
                excerpt=f"An in-depth exploration of {title.lower()}. This article covers everything you need to know.",
                author_id=author.id,
                category_id=cats[cat_slug].id,
                status="published",
                is_featured=(i < 2),
                view_count=random.randint(50, 2000),
                published_at=pub_date,
                created_at=pub_date,
            )
            post.generate_slug()
            post.calculate_reading_time()
            post.tags = [tags[t] for t in tag_names if t in tags]
            db.session.add(post)
            created_posts.append(post)

        db.session.flush()

        # ── Comments ──
        comment_texts = [
            "This is a fantastic article! Really helped me understand the topic better.",
            "Great writeup. I especially liked the part about the implementation details.",
            "I've been looking for exactly this explanation. Thank you so much!",
            "Interesting perspective. Have you considered the edge cases mentioned in RFC 7231?",
            "This changed how I think about this problem. Sharing with my team!",
            "Well written and easy to follow. Bookmarking for later reference.",
        ]

        for post in created_posts[:8]:
            for j in range(random.randint(2, 5)):
                commenter = random.choice([alice, bob, carol])
                c = Comment(
                    content=random.choice(comment_texts),
                    post_id=post.id,
                    author_id=commenter.id,
                    is_approved=True,
                    created_at=post.created_at + timedelta(hours=random.randint(1, 48)),
                )
                db.session.add(c)
                db.session.flush()
                # One nested reply
                if j == 0:
                    reply = Comment(
                        content="Thanks for the feedback! Really appreciate it.",
                        post_id=post.id,
                        author_id=post.author_id,
                        parent_id=c.id,
                        is_approved=True,
                        created_at=c.created_at + timedelta(hours=1),
                    )
                    db.session.add(reply)

        # ── Likes ──
        for post in created_posts:
            for liker in random.sample([alice, bob, carol], random.randint(0, 3)):
                like = Like(user_id=liker.id, target_type="post", target_id=post.id)
                db.session.add(like)

        # ── Bookmarks ──
        for post in random.sample(created_posts, 4):
            bm = Bookmark(user_id=alice.id, post_id=post.id)
            db.session.add(bm)

        db.session.commit()
        print("Seed complete! Sample accounts:")
        print("   Admin:  admin@inkwell.com  / Admin1234!")
        print("   Author: alice@inkwell.com  / Alice1234!")
        print("   Author: bob@inkwell.com    / Bob12345!")
        print("   Author: carol@inkwell.com  / Carol123!")

if __name__ == "__main__":
    seed()

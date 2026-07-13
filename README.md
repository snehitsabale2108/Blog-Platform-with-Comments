# Inkwell – Professional Blog Platform

A full-stack, production-quality blogging platform built with **Python Flask** and **Bootstrap 5**. Featuring a Medium/Dev.to style UI, REST API, JWT authentication, rich text editing, and an admin dashboard.

---

## Table of Contents
1. [Features](#features)
2. [Folder Structure](#folder-structure)
3. [Quick Start (Local)](#quick-start)
4. [Environment Variables](#environment-variables)
5. [Database](#database)
6. [API Documentation](#api-documentation)
7. [Deployment](#deployment)

---

## Features

| Category | Features |
|---|---|
| **Auth** | Register/login/logout, bcrypt password hashing, JWT access+refresh tokens, email verification, password reset |
| **Posts** | Create/edit/delete, rich text editor (Quill.js), cover image upload, draft/publish states, autosave, tags & categories |
| **Discovery** | Homepage with featured post hero, category filters, search, sort (latest / popular / trending), pagination |
| **Social** | Like posts & comments, follow authors, personalized feed, bookmark posts |
| **Comments** | Threaded nested replies, edit/delete own comments, flag inappropriate content |
| **User Profiles** | Bio, avatar, social links, post list, follower stats |
| **Admin** | Dashboard with stats, user management (block/promote), post moderation (flag/approve/delete), category/tag management |
| **API** | Versioned REST API `/api/v1/...`, JWT auth, role-based access, consistent JSON responses |
| **UI/UX** | Dark mode (persisted), AOS animations, reading progress bar, table of contents, responsive mobile-first |

---

## Folder Structure

```
blogplatform/
├── app/
│   ├── __init__.py          # App factory
│   ├── config.py            # Dev / Test / Prod configs
│   ├── extensions.py        # Flask extensions (db, jwt, mail…)
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── post.py          # includes post_tags many-to-many
│   │   ├── comment.py       # threaded via parent_id
│   │   ├── category.py
│   │   ├── tag.py
│   │   ├── like.py          # polymorphic (post/comment)
│   │   ├── bookmark.py
│   │   ├── follow.py
│   │   ├── notification.py
│   │   └── token_blocklist.py
│   ├── blueprints/
│   │   ├── main/            # Homepage route
│   │   ├── auth/            # Web auth (login/register/verify)
│   │   ├── posts/           # Post CRUD web views
│   │   ├── comments/        # Comment web views
│   │   ├── users/           # Profile / follow / bookmarks
│   │   ├── admin/           # Admin dashboard & moderation
│   │   └── api/             # REST API (v1)
│   │       ├── auth.py
│   │       ├── posts.py
│   │       ├── comments.py
│   │       ├── users.py
│   │       └── admin.py
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── main/
│   │   ├── posts/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── admin/
│   │   ├── partials/
│   │   └── errors/
│   ├── static/
│   │   ├── css/             # main.css, post.css, editor.css, admin.css
│   │   ├── js/              # main.js, post.js, editor.js
│   │   ├── images/          # default_avatar.png, og-default.png
│   │   └── uploads/         # user-uploaded files (gitignored)
│   └── utils/
│       ├── errors.py        # API response helpers + error handlers
│       ├── email.py         # Verification / reset emails
│       ├── image_handler.py # PIL image resize & save
│       ├── jwt_callbacks.py
│       └── decorators.py
├── instance/                # SQLite DB lives here (gitignored)
├── migrations/              # Flask-Migrate Alembic files
├── run.py                   # Entry point
├── seed.py                  # Database seeder
├── requirements.txt
├── .env.example
└── Procfile                 # Heroku / Render deployment
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# 1. Navigate to the project folder
cd blogplatform

# 2. Create & activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env from example
copy .env.example .env       # Windows
cp .env.example .env          # macOS/Linux

# 5. Edit .env – set SECRET_KEY and JWT_SECRET_KEY at minimum

# 6. Initialize the database
flask db init
flask db migrate -m "initial"
flask db upgrade

# 7. Seed with sample data
python seed.py

# 8. Run the dev server
python run.py
```

Open http://localhost:5000

**Sample accounts (after seeding):**
| Email | Password | Role |
|---|---|---|
| admin@inkwell.com | Admin@123 | admin |
| alice@inkwell.com | Alice@123 | author |
| bob@inkwell.com | Bob@123 | author |
| carol@inkwell.com | Carol@123 | author |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Flask secret key (min 32 chars) |
| `JWT_SECRET_KEY` | ✅ | JWT signing secret |
| `FLASK_ENV` | — | `development` / `production` |
| `DATABASE_URL` | — | SQLite by default; PostgreSQL for prod |
| `APP_URL` | — | Full URL for email links |
| `MAIL_SERVER` | — | SMTP host |
| `MAIL_PORT` | — | SMTP port (587 default) |
| `MAIL_USE_TLS` | — | `true` / `false` |
| `MAIL_USERNAME` | — | SMTP username |
| `MAIL_PASSWORD` | — | SMTP password or app password |
| `MAIL_DEFAULT_SENDER` | — | From address |

---

## Database

- **Development:** SQLite (`instance/dev.db`) — zero config
- **Production:** PostgreSQL — set `DATABASE_URL=postgresql://...`
- **ORM:** SQLAlchemy with Flask-Migrate (Alembic)

### Key schema relationships

```
User ──< Post ──< Comment ──< Comment (self-referential replies)
User ──< Like  (polymorphic: target_type=post|comment)
User ──< Bookmark ──> Post
User >──< User (followers, via followers table)
Post >──< Tag  (via post_tags)
Post >── Category
```

### Migrations

```bash
flask db migrate -m "description"
flask db upgrade
flask db downgrade
```

---

## API Documentation

All API endpoints are prefixed `/api/v1/`. Responses follow:

```json
{
  "success": true,
  "message": "...",
  "data": { ... }
}
```

Error responses:
```json
{
  "success": false,
  "message": "...",
  "errors": { "field": "message" }
}
```

Paginated responses include:
```json
{
  "pagination": {
    "page": 1, "per_page": 12, "total": 100,
    "pages": 9, "has_next": true, "has_prev": false
  }
}
```

### Authentication

#### `POST /api/v1/auth/register`
```json
// Request
{ "username": "alice", "email": "alice@example.com", "password": "Secret1234", "display_name": "Alice" }

// Response 201
{ "success": true, "message": "Registration successful. Please verify your email.", "data": { ...user } }
```

#### `POST /api/v1/auth/login`
```json
// Request
{ "identifier": "alice@example.com", "password": "Secret1234" }

// Response 200
{ "data": { "access_token": "eyJ...", "refresh_token": "eyJ...", "user": { ...user } } }
```

#### `POST /api/v1/auth/refresh`
Requires `Authorization: Bearer <refresh_token>`
```json
// Response 200
{ "data": { "access_token": "eyJ..." } }
```

#### `DELETE /api/v1/auth/logout`
Requires `Authorization: Bearer <access_token>` — revokes token.

#### `GET /api/v1/auth/me`
Returns current user profile.

#### `POST /api/v1/auth/forgot-password`
```json
{ "email": "alice@example.com" }
```

#### `POST /api/v1/auth/reset-password`
```json
{ "token": "...", "password": "NewSecret1234" }
```

---

### Posts

#### `GET /api/v1/posts/`
Query params: `page`, `per_page`, `q`, `category`, `tag`, `author`, `sort` (latest|popular|trending)

#### `GET /api/v1/posts/<slug>`
Returns full post with content.

#### `POST /api/v1/posts/` 🔒
```json
{
  "title": "My Post",
  "content": "<p>HTML content</p>",
  "excerpt": "Short summary",
  "category_id": 1,
  "tag_ids": [1, 3],
  "action": "publish"  // or "draft"
}
```

#### `PUT /api/v1/posts/<slug>` 🔒
Partial update of any fields listed above.

#### `DELETE /api/v1/posts/<slug>` 🔒
Author or admin only.

#### `POST /api/v1/posts/<slug>/like` 🔒
Toggle like. Returns `{ "liked": true, "count": 42 }`.

#### `POST /api/v1/posts/<slug>/bookmark` 🔒
Toggle bookmark. Returns `{ "bookmarked": true }`.

---

### Comments

#### `GET /api/v1/comments/post/<post_id>`
Query: `page`, `per_page`. Returns top-level comments with nested replies.

#### `POST /api/v1/comments/post/<post_id>` 🔒
```json
{ "content": "Great post!", "parent_id": null }
```

#### `PUT /api/v1/comments/<comment_id>` 🔒 (own comment only)
```json
{ "content": "Updated comment text" }
```

#### `DELETE /api/v1/comments/<comment_id>` 🔒 (own or admin)

#### `POST /api/v1/comments/<comment_id>/like` 🔒
Toggle like.

#### `POST /api/v1/comments/<comment_id>/flag` 🔒
Flag for moderation.

---

### Users

#### `GET /api/v1/users/<username>`
Public profile.

#### `GET /api/v1/users/<username>/posts`
Published posts for the user.

#### `PUT /api/v1/users/me` 🔒
Update profile fields: `display_name`, `bio`, `website`, `twitter`, `github`, `linkedin`.

#### `POST /api/v1/users/<username>/follow` 🔒
Toggle follow.

#### `GET /api/v1/users/me/bookmarks` 🔒
Paginated saved posts.

#### `GET /api/v1/users/me/feed` 🔒
Posts from followed authors.

#### `GET /api/v1/users/me/notifications` 🔒
Last 30 notifications.

#### `POST /api/v1/users/me/notifications/read` 🔒
Mark all notifications as read.

---

### Admin (admin role required)

#### `GET /api/v1/admin/stats` 🔒👑
Platform-wide stats.

#### `GET /api/v1/admin/users` 🔒👑
Paginated user list with email visible.

#### `POST /api/v1/admin/users/<id>/block` 🔒👑
Toggle user active state.

#### `POST /api/v1/admin/posts/<id>/flag` 🔒👑
Flag a post for review.

#### `POST /api/v1/admin/posts/<id>/approve` 🔒👑
Approve / re-publish a flagged post.

#### `GET /api/v1/admin/categories`
Public list.

#### `POST /api/v1/admin/categories` 🔒👑
Create category.

#### `GET /api/v1/admin/tags`
Public list.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Flask 3.0, SQLAlchemy 2.0, Flask-Migrate |
| Authentication | Flask-JWT-Extended, Flask-Bcrypt, itsdangerous |
| Email | Flask-Mail |
| Rate Limiting | Flask-Limiter |
| Frontend | Bootstrap 5.3, Bootstrap Icons, AOS, Quill.js |
| Fonts | Inter (UI), Merriweather (reading) |
| Database | SQLite (dev), PostgreSQL (prod) |
| Deployment | Gunicorn, Render / Railway / IBM Cloud |

---

*Made with ❤️ by Inkwell*

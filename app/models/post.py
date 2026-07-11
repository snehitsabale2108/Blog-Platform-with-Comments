from datetime import datetime
import math
import re
from ..extensions import db
from slugify import slugify


post_tags = db.Table(
    "post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("posts.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("tags.id"), primary_key=True),
)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.String(500))
    content = db.Column(db.Text, nullable=False)
    cover_image = db.Column(db.String(255))
    status = db.Column(db.String(20), default="draft")  # draft | published | flagged
    is_featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    reading_time = db.Column(db.Integer, default=1)  # minutes

    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)

    # Relationships
    comments = db.relationship("Comment", backref="post", lazy="dynamic",
                                cascade="all, delete-orphan")
    bookmarks = db.relationship("Bookmark", backref="post", lazy="dynamic",
                                 cascade="all, delete-orphan")
    tags = db.relationship("Tag", secondary=post_tags, backref=db.backref("posts", lazy="dynamic"))

    def generate_slug(self):
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while Post.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug

    def calculate_reading_time(self):
        words = len(re.findall(r"\w+", self.content or ""))
        self.reading_time = max(1, math.ceil(words / 200))

    def increment_views(self):
        self.view_count = (self.view_count or 0) + 1

    def is_liked_by(self, user) -> bool:
        from .like import Like
        return Like.query.filter_by(user_id=user.id, target_type="post", target_id=self.id).first() is not None

    def is_bookmarked_by(self, user) -> bool:
        from .bookmark import Bookmark
        return Bookmark.query.filter_by(user_id=user.id, post_id=self.id).first() is not None

    @property
    def like_count(self):
        from .like import Like
        return Like.query.filter_by(target_type="post", target_id=self.id).count()

    @property
    def comment_count(self):
        return self.comments.filter_by(parent_id=None).count()

    def to_dict(self, include_content=False, current_user=None):
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "excerpt": self.excerpt,
            "cover_image": self.cover_image,
            "status": self.status,
            "is_featured": self.is_featured,
            "view_count": self.view_count,
            "reading_time": self.reading_time,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "author": self.author.to_dict() if self.author else None,
            "category": self.category.to_dict() if self.category else None,
            "tags": [t.to_dict() for t in self.tags],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
        if include_content:
            data["content"] = self.content
        if current_user:
            from .like import Like as _Like
            from .bookmark import Bookmark as _Bookmark
            data["is_liked"] = _Like.query.filter_by(
                user_id=current_user.id, target_type="post", target_id=self.id
            ).first() is not None
            data["is_bookmarked"] = _Bookmark.query.filter_by(
                user_id=current_user.id, post_id=self.id
            ).first() is not None
        return data

    def __repr__(self):
        return f"<Post {self.slug}>"

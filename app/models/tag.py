from ..extensions import db
from .post import post_tags


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "post_count": self.posts.filter_by(status="published").count(),
        }

    def __repr__(self):
        return f"<Tag {self.name}>"

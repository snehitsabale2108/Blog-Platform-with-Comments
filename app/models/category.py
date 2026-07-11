from ..extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    color = db.Column(db.String(7), default="#3b82d4")
    icon = db.Column(db.String(50), default="bi-journal")

    posts = db.relationship("Post", backref="category", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "post_count": self.posts.filter_by(status="published").count(),
        }

    def __repr__(self):
        return f"<Category {self.name}>"

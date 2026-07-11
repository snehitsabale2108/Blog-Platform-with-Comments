from datetime import datetime
from ..extensions import db


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True)
    is_flagged = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    replies = db.relationship("Comment", backref=db.backref("parent", remote_side=[id]),
                               lazy="dynamic", cascade="all, delete-orphan")

    @property
    def like_count(self):
        from .like import Like
        return Like.query.filter_by(target_type="comment", target_id=self.id).count()

    def to_dict(self, current_user=None, include_replies=False):
        data = {
            "id": self.id,
            "content": self.content,
            "post_id": self.post_id,
            "parent_id": self.parent_id,
            "is_flagged": self.is_flagged,
            "like_count": self.like_count,
            "reply_count": self.replies.count(),
            "author": self.author.to_dict() if self.author else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if current_user:
            from .like import Like
            data["is_liked"] = Like.query.filter_by(
                user_id=current_user.id, target_type="comment", target_id=self.id
            ).first() is not None
        if include_replies:
            data["replies"] = [r.to_dict(current_user=current_user) for r in self.replies.filter_by(is_approved=True).all()]
        return data

    def __repr__(self):
        return f"<Comment {self.id}>"

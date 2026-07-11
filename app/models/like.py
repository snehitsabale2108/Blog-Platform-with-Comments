from datetime import datetime
from ..extensions import db


class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_type = db.Column(db.String(20), nullable=False)   # 'post' | 'comment'
    target_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "target_type", "target_id", name="uq_like"),
    )

    def __repr__(self):
        return f"<Like user={self.user_id} {self.target_type}={self.target_id}>"

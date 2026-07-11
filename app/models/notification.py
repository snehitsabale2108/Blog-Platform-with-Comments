from datetime import datetime
from ..extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    notification_type = db.Column(db.String(50))  # like, comment, follow, reply
    target_type = db.Column(db.String(20))         # post | comment
    target_id = db.Column(db.Integer)
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    actor = db.relationship("User", foreign_keys=[actor_id])

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.notification_type,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "message": self.message,
            "is_read": self.is_read,
            "actor": self.actor.to_dict() if self.actor else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

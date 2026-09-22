from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ProductMonitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(512), nullable=False)
    size = db.Column(db.String(50), nullable=True)
    color = db.Column(db.String(50), nullable=True)
    target_discount_percent = db.Column(db.Float, nullable=False, default=0.0)

    is_on_sale = db.Column(db.Boolean, default=False)
    current_price = db.Column(db.Float, nullable=True)
    original_price = db.Column(db.Float, nullable=True)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ProductMonitor {self.name} - {self.size} - {self.color}>"

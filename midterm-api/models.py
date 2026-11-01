import sqlite3

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, event
from sqlalchemy.engine import Engine

db = SQLAlchemy()

ITEM_STATUSES = ("in_stock", "out_of_stock", "discontinued")


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    """SQLite ignores FOREIGN KEY constraints unless this pragma is set per connection."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


class Category(db.Model):
    """Parent resource (1 category -> N items)."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))

    items = db.relationship(
        "Item", backref="category", cascade="all, delete-orphan", lazy=True
    )

    def to_dict(self, include_items=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "item_count": len(self.items),
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class Item(db.Model):
    """Child resource; every item belongs to exactly one category."""

    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("price >= 0", name="ck_items_price_non_negative"),
        CheckConstraint("quantity >= 0", name="ck_items_quantity_non_negative"),
        CheckConstraint(f"status IN {ITEM_STATUSES}", name="ck_items_status_valid"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(40), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="in_stock")
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id"), nullable=False
    )

    def to_dict(self, include_category=False):
        data = {
            "id": self.id,
            "name": self.name,
            "sku": self.sku,
            "price": self.price,
            "quantity": self.quantity,
            "status": self.status,
            "category_id": self.category_id,
        }
        if include_category:
            data["category"] = {"id": self.category.id, "name": self.category.name}
        return data

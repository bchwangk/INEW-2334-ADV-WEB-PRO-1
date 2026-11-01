from app import app
from models import Category, Item, db

CATEGORIES = [
    {"name": "Electronics", "description": "Computer peripherals and gadgets"},
    {"name": "Home Office", "description": "Furniture and desk accessories"},
    {"name": "Accessories", "description": "Cases, stands, and small add-ons"},
]

ITEMS = [
    ("Wireless Mouse", "WM-100", 24.99, 50, "in_stock", "Electronics"),
    ("Mechanical Keyboard", "KB-200", 79.99, 20, "in_stock", "Electronics"),
    ("USB-C Hub", "HB-300", 39.50, 0, "out_of_stock", "Electronics"),
    ("Desk Lamp", "DL-400", 29.00, 15, "in_stock", "Home Office"),
    ("Ergonomic Chair", "EC-500", 249.99, 5, "in_stock", "Home Office"),
    ("Desk Mat", "SM-600", 19.99, 0, "discontinued", "Home Office"),
    ("Laptop Sleeve", "LS-700", 22.50, 40, "in_stock", "Accessories"),
    ("Phone Stand", "PS-800", 12.99, 0, "out_of_stock", "Accessories"),
]


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()

        categories = {}
        for data in CATEGORIES:
            category = Category(**data)
            db.session.add(category)
            categories[category.name] = category

        for name, sku, price, quantity, status, category_name in ITEMS:
            db.session.add(
                Item(
                    name=name,
                    sku=sku,
                    price=price,
                    quantity=quantity,
                    status=status,
                    category=categories[category_name],
                )
            )

        db.session.commit()
        print(
            f"Seeded {Category.query.count()} categories and {Item.query.count()} items "
            f"into {app.config['SQLALCHEMY_DATABASE_URI']}"
        )


if __name__ == "__main__":
    seed()

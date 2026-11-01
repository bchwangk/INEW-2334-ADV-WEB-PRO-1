import math
import os

from flask import Flask, jsonify, request
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from models import ITEM_STATUSES, Category, Item, db

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "midterm.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

API = "/api/v1"

STATUS_LABELS = {
    400: "Bad Request",
    404: "Not Found",
    405: "Method Not Allowed",
    409: "Conflict",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}


def error_response(status, message):
    body = {"status": status, "error": STATUS_LABELS.get(status, "Error"), "message": message}
    return jsonify(body), status


@app.errorhandler(HTTPException)
def handle_http_exception(exc):
    # Unknown route (404), wrong method (405), etc. -> JSON instead of an HTML page
    return error_response(exc.code or 500, exc.description)


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    db.session.rollback()
    app.logger.exception("Unhandled error")
    return error_response(500, "An unexpected server error occurred")


def get_json_object():
    """Returns (data, None) for a JSON object body, otherwise (None, 400 response)."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, error_response(400, "Request body must be a valid JSON object")
    return data, None


def commit_session(conflict_message):
    """Commit; a unique-constraint race becomes a 409 instead of a crash."""
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error_response(409, conflict_message)
    return None


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def is_text(value, max_length):
    return isinstance(value, str) and 0 < len(value.strip()) <= max_length


def name_taken(name, exclude_id=None):
    query = Category.query.filter_by(name=name)
    if exclude_id is not None:
        query = query.filter(Category.id != exclude_id)
    return query.first() is not None


def sku_taken(sku, exclude_id=None):
    query = Item.query.filter_by(sku=sku)
    if exclude_id is not None:
        query = query.filter(Item.id != exclude_id)
    return query.first() is not None


def validate_category(data, partial):
    fields = {}

    if "name" in data:
        if not is_text(data["name"], 100):
            return None, error_response(422, "'name' must be a non-empty string up to 100 characters")
        fields["name"] = data["name"].strip()
    elif not partial:
        return None, error_response(400, "Missing required field(s): name")

    if "description" in data:
        description = data["description"]
        if description is not None and (not isinstance(description, str) or len(description) > 255):
            return None, error_response(422, "'description' must be a string up to 255 characters or null")
        fields["description"] = description

    if partial and not fields:
        return None, error_response(400, "Provide at least one field to update: name, description")
    return fields, None


ITEM_REQUIRED = ("name", "sku", "price", "category_id")


def validate_item(data, partial):
    if not partial:
        missing = [key for key in ITEM_REQUIRED if key not in data]
        if missing:
            return None, error_response(400, "Missing required field(s): " + ", ".join(missing))

    fields = {}

    if "name" in data:
        if not is_text(data["name"], 120):
            return None, error_response(422, "'name' must be a non-empty string up to 120 characters")
        fields["name"] = data["name"].strip()

    if "sku" in data:
        if not is_text(data["sku"], 40):
            return None, error_response(422, "'sku' must be a non-empty string up to 40 characters")
        fields["sku"] = data["sku"].strip()

    if "price" in data:
        if not is_number(data["price"]) or data["price"] < 0:
            return None, error_response(422, "'price' must be a number greater than or equal to 0")
        fields["price"] = float(data["price"])

    if "quantity" in data:
        if not is_int(data["quantity"]) or data["quantity"] < 0:
            return None, error_response(422, "'quantity' must be an integer greater than or equal to 0")
        fields["quantity"] = data["quantity"]

    if "status" in data:
        if data["status"] not in ITEM_STATUSES:
            return None, error_response(422, "'status' must be one of: " + ", ".join(ITEM_STATUSES))
        fields["status"] = data["status"]

    if "category_id" in data:
        if not is_int(data["category_id"]):
            return None, error_response(422, "'category_id' must be an integer")
        category = db.session.get(Category, data["category_id"])
        if category is None:
            return None, error_response(404, f"Category {data['category_id']} not found")
        fields["category_id"] = category.id

    if partial and not fields:
        return None, error_response(
            400, "Provide at least one field to update: name, sku, price, quantity, status, category_id"
        )
    return fields, None


@app.route(f"{API}/categories", methods=["GET"])
def list_categories():
    categories = Category.query.order_by(Category.id).all()
    return jsonify({
        "count": len(categories),
        "categories": [category.to_dict() for category in categories],
    }), 200


@app.route(f"{API}/categories/<int:category_id>", methods=["GET"])
def get_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        return error_response(404, f"Category {category_id} not found")
    return jsonify(category.to_dict(include_items=True)), 200


@app.route(f"{API}/categories", methods=["POST"])
def create_category():
    data, problem = get_json_object()
    if problem:
        return problem
    fields, problem = validate_category(data, partial=False)
    if problem:
        return problem

    if name_taken(fields["name"]):
        return error_response(409, f"Category '{fields['name']}' already exists")

    category = Category(**fields)
    db.session.add(category)
    conflict = commit_session(f"Category '{fields['name']}' already exists")
    if conflict:
        return conflict
    return jsonify(category.to_dict()), 201


@app.route(f"{API}/categories/<int:category_id>", methods=["PUT"])
def update_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        return error_response(404, f"Category {category_id} not found")

    data, problem = get_json_object()
    if problem:
        return problem
    fields, problem = validate_category(data, partial=True)
    if problem:
        return problem

    if "name" in fields and name_taken(fields["name"], exclude_id=category.id):
        return error_response(409, f"Category '{fields['name']}' already exists")

    for key, value in fields.items():
        setattr(category, key, value)
    conflict = commit_session("Category name already exists")
    if conflict:
        return conflict
    return jsonify(category.to_dict(include_items=True)), 200


@app.route(f"{API}/categories/<int:category_id>", methods=["DELETE"])
def delete_category(category_id):
    category = db.session.get(Category, category_id)
    if category is None:
        return error_response(404, f"Category {category_id} not found")

    removed = len(category.items)
    db.session.delete(category)  # ORM delete -> cascade removes the child items
    db.session.commit()
    return jsonify({
        "message": f"Category {category_id} deleted",
        "items_deleted": removed,
    }), 200



@app.route(f"{API}/items", methods=["GET"])
def list_items():
    query = Item.query

    category_id = request.args.get("category_id")
    if category_id is not None:
        try:
            category_id = int(category_id)
        except ValueError:
            return error_response(422, "'category_id' query parameter must be an integer")
        query = query.filter_by(category_id=category_id)

    status = request.args.get("status")
    if status is not None:
        if status not in ITEM_STATUSES:
            return error_response(422, "'status' query parameter must be one of: " + ", ".join(ITEM_STATUSES))
        query = query.filter_by(status=status)

    items = query.order_by(Item.id).all()
    return jsonify({"count": len(items), "items": [item.to_dict() for item in items]}), 200


@app.route(f"{API}/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        return error_response(404, f"Item {item_id} not found")
    return jsonify(item.to_dict(include_category=True)), 200


@app.route(f"{API}/items", methods=["POST"])
def create_item():
    data, problem = get_json_object()
    if problem:
        return problem
    fields, problem = validate_item(data, partial=False)
    if problem:
        return problem

    if sku_taken(fields["sku"]):
        return error_response(409, f"SKU '{fields['sku']}' already exists")

    item = Item(**fields)
    db.session.add(item)
    conflict = commit_session(f"SKU '{fields['sku']}' already exists")
    if conflict:
        return conflict
    return jsonify(item.to_dict(include_category=True)), 201


@app.route(f"{API}/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        return error_response(404, f"Item {item_id} not found")

    data, problem = get_json_object()
    if problem:
        return problem
    fields, problem = validate_item(data, partial=True)
    if problem:
        return problem

    if "sku" in fields and sku_taken(fields["sku"], exclude_id=item.id):
        return error_response(409, f"SKU '{fields['sku']}' already exists")

    for key, value in fields.items():
        setattr(item, key, value)
    conflict = commit_session("SKU already exists")
    if conflict:
        return conflict
    return jsonify(item.to_dict(include_category=True)), 200


@app.route(f"{API}/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    item = db.session.get(Item, item_id)
    if item is None:
        return error_response(404, f"Item {item_id} not found")

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": f"Item {item_id} deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True)

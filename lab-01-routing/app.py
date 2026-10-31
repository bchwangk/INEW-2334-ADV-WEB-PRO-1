from flask import Flask, jsonify, request

app = Flask(__name__)

items = [
    {"id":1, "title": "Clean Code"},
    {"id":2, "title": "The Pragmatic Coder"},
    {"id":3, "title": "Design Patterns"},
]

next_id = 4

REQUIRED_FIELDS = {"title"}

@app.route("/api/status", methods=["GET"])
def status():
    return jsonify({"status": "healthy", "version": "1.0.0"}), 200

@app.route("/api/items", methods=["GET"])
def get_item():
    return jsonify({"items": items, "count": len(items)}), 200

@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_items(item_id):
    item = next((i for i in items if i["id"] == item_id), None)
    if item is None:
        return jsonify({"error": f"item with ID {item_id} not found"}), 404
    return jsonify(item), 200

@app.route("/api/items", methods=["POST"])
def create_items():
    global next_id
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be VALID JSON"}), 400

    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(sorted(missing))}"}), 400

    new_item = {
        "id": next_id,
        "title": data["title"]
    }
    items.append(new_item)
    next_id += 1

    return jsonify(new_item), 201

if __name__ == "__main__":
    app.run(debug=True)


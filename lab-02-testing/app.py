from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory data store
tasks = [
    {"id": 1, "title": "Write project proposal", "priority": "high", "completed": False, "due_date": "2026-09-25"},
    {"id": 2, "title": "Review pull requests", "priority": "medium", "completed": False, "due_date": "2026-09-22"},
    {"id": 3, "title": "Update documentation", "priority": "low", "completed": True, "due_date": "2026-09-20"},
]
next_id = 4

VALID_PRIORITIES = ["low", "medium", "high"]
REQUIRED_FIELDS = {"title", "priority", "completed", "due_date"}


def find_task(task_id):
    return next((t for t in tasks if t["id"] == task_id), None)


def validate_task_payload(data, require_all=True):
    if not isinstance(data, dict):
        return "Request body must be a JSON object", 400

    if require_all:
        missing = REQUIRED_FIELDS - data.keys()
        if missing:
            return f"Missing required field(s): {', '.join(sorted(missing))}", 400

    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return "Field 'title' must be a non-empty string", 422

    if "priority" in data:
        if data["priority"] not in VALID_PRIORITIES:
            return f"Field 'priority' must be one of {VALID_PRIORITIES}", 422

    if "completed" in data:
        if not isinstance(data["completed"], bool):
            return "Field 'completed' must be a boolean", 422

    if "due_date" in data:
        if not isinstance(data["due_date"], str) or not data["due_date"].strip():
            return "Field 'due_date' must be a non-empty string", 422

    return None, None


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Not found", "message": "The requested resource does not exist"}), 404


@app.errorhandler(400)
def handle_400(e):
    return jsonify({"error": "Bad request", "message": "The request could not be understood or was missing required parameters"}), 400


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    priority_filter = request.args.get("priority")
    result = tasks
    if priority_filter:
        result = [t for t in tasks if t["priority"] == priority_filter]
    return jsonify({"tasks": result, "count": len(result)}), 200


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    task = find_task(task_id)
    if task is None:
        return jsonify({"error": f"Task with id {task_id} not found"}), 404
    return jsonify(task), 200


@app.route("/api/tasks", methods=["POST"])
def create_task():
    global next_id
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    # Missing required keys -> 400
    missing = {"title", "priority"} - data.keys()
    if missing:
        return jsonify({"error": f"Missing required field(s): {', '.join(sorted(missing))}"}), 400

    # Present but invalid values -> 422
    if not isinstance(data["title"], str) or not data["title"].strip():
        return jsonify({"error": "Field 'title' must be a non-empty string"}), 422

    if data["priority"] not in VALID_PRIORITIES:
        return jsonify({"error": f"Field 'priority' must be one of {VALID_PRIORITIES}"}), 422

    new_task = {
        "id": next_id,
        "title": data["title"],
        "priority": data["priority"],
        "completed": data.get("completed", False),
        "due_date": data.get("due_date", ""),
    }
    tasks.append(new_task)
    next_id += 1

    return jsonify(new_task), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = find_task(task_id)
    if task is None:
        return jsonify({"error": f"Task with id {task_id} not found"}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    error_message, status_code = validate_task_payload(data, require_all=True)
    if error_message:
        return jsonify({"error": error_message}), status_code

    task["title"] = data["title"]
    task["priority"] = data["priority"]
    task["completed"] = data["completed"]
    task["due_date"] = data["due_date"]

    return jsonify(task), 200


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = find_task(task_id)
    if task is None:
        return jsonify({"error": f"Task with id {task_id} not found"}), 404

    tasks.remove(task)
    return jsonify({"message": f"Task with id {task_id} deleted successfully"}), 200


if __name__ == "__main__":
    app.run(debug=True)

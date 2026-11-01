import os
import sys
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "smoke.db")

from app import app  # noqa: E402
from seed import seed  # noqa: E402

seed()
client = app.test_client()
results = []


def check(label, response, expected_status, **expected_body):
    body = response.get_json(silent=True) or {}
    ok = response.status_code == expected_status and response.is_json
    for key, value in expected_body.items():
        ok = ok and body.get(key) == value
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {response.status_code} (want {expected_status})  {label}")

check("list categories", client.get("/api/v1/categories"), 200, count=3)
check("get category 1", client.get("/api/v1/categories/1"), 200, name="Electronics", item_count=3)
check("get missing category", client.get("/api/v1/categories/999"), 404)
check("create category", client.post("/api/v1/categories", json={"name": "Toys"}), 201, name="Toys")
check("create duplicate category", client.post("/api/v1/categories", json={"name": "Toys"}), 409)
check("create category, no name", client.post("/api/v1/categories", json={"description": "x"}), 400)
check("create category, bad name type", client.post("/api/v1/categories", json={"name": 123}), 422)
check("create category, not JSON", client.post("/api/v1/categories", data="nope"), 400)
check("update category", client.put("/api/v1/categories/4", json={"description": "Games"}), 200, description="Games")
check("update category, duplicate name", client.put("/api/v1/categories/4", json={"name": "Electronics"}), 409)
check("update category, empty body", client.put("/api/v1/categories/4", json={}), 400)
check("update missing category", client.put("/api/v1/categories/999", json={"name": "X"}), 404)

check("list items", client.get("/api/v1/items"), 200, count=8)
check("filter by category_id", client.get("/api/v1/items?category_id=1"), 200, count=3)
check("filter by status", client.get("/api/v1/items?status=out_of_stock"), 200, count=2)
check("filter by both", client.get("/api/v1/items?category_id=1&status=in_stock"), 200, count=2)
check("filter, bad status", client.get("/api/v1/items?status=bogus"), 422)
check("filter, bad category_id", client.get("/api/v1/items?category_id=abc"), 422)
check("get item 1", client.get("/api/v1/items/1"), 200, sku="WM-100")
check("get missing item", client.get("/api/v1/items/999"), 404)

new_item = {"name": "Board Game", "sku": "BG-900", "price": 34.5, "quantity": 10, "category_id": 4}
check("create item", client.post("/api/v1/items", json=new_item), 201, sku="BG-900")
check("create item, duplicate sku", client.post("/api/v1/items", json=new_item), 409)
check("create item, missing fields", client.post("/api/v1/items", json={"name": "No SKU"}), 400)
check("create item, negative price", client.post("/api/v1/items", json={**new_item, "sku": "X-1", "price": -5}), 422)
check("create item, bad status", client.post("/api/v1/items", json={**new_item, "sku": "X-2", "status": "gone"}), 422)
check("create item, unknown category", client.post("/api/v1/items", json={**new_item, "sku": "X-3", "category_id": 999}), 404)
check("update item", client.put("/api/v1/items/9", json={"price": 29.99}), 200, price=29.99)
check("update item, bad quantity", client.put("/api/v1/items/9", json={"quantity": -3}), 422)
check("update item, empty body", client.put("/api/v1/items/9", json={}), 400)
check("update item, duplicate sku", client.put("/api/v1/items/9", json={"sku": "WM-100"}), 409)
check("update missing item", client.put("/api/v1/items/999", json={"price": 1}), 404)
check("delete item", client.delete("/api/v1/items/9"), 200)
check("deleted item is gone", client.get("/api/v1/items/9"), 404)

check("delete category", client.delete("/api/v1/categories/2"), 200, items_deleted=3)
check("cascade removed its items", client.get("/api/v1/items?category_id=2"), 200, count=0)
check("delete missing category", client.delete("/api/v1/categories/999"), 404)

check("unknown route", client.get("/api/v1/nope"), 404)
check("wrong method", client.patch("/api/v1/categories"), 405)

passed = sum(results)
print(f"\n{passed}/{len(results)} checks passed")
sys.exit(0 if passed == len(results) else 1)

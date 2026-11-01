A RESTful web service built with Flask and Flask-SQLAlchemy (SQLite). It models a one-to-many relationship. Deleting a category cascades to its items.

Data Model
| Table | Column | Type | Constraints |
|---|---|---|---| 
| categories | id | Integer | primary key | 
| | name | String(100) | unique, not null | 
| | description | String(255) | nullable | 
| | items | id | Integer | primary key | 
| | name | String(120) | not null | 
| | sku |String(40) | unique, not null | 
| | price | Float | not null, `>= 0` | 
| | quantity | Integer | not null, `>= 0`, default 0 | 
| | status |String(20) | not null, one of `in_stock`, `out_of_stock`, `discontinued`, default`in_stock`| 
| | category_id | Integer | foreign key to `categories.id`, not null |

Endpoints
Base path: `/api/v1`. All responses are JSON.

Categories
| Method | Path | Description | Success | 
|---|---|---|---| 
| GET | `/categories` | List all categories with `item_count` | 200 | 
| GET | `/categories/<id>` | One category with its `items` array | 200 | 
| POST | `/categories` | Create a category (name must be unique) | 201 | 
| PUT | `/categories/<id>` | Update `name` and/or `description` | 200 | 
| DELETE |`/categories/<id>` | Delete the category and cascade to its items | 200 | 

Items
| Method | Path | Description | Success | 
|---|---|---|---| 
| GET | `/items` | List items. Filters: 'category_id=1`, `?status=in_stock` (combinable) | 200 | 
| GET |`/items/<id>` | One item, including its parent category | 200 | 
| POST | `/items` | Create an item linked to an existing `category_id` | 201 | 
| PUT | `/items/<id>` | Update any subset of item fields (at least one) | 200 | 
| DELETE | `/items/<id>`| Delete one item | 200 |

Payload Examples
Create a category (`POST /api/v1/categories`): 

```json 
{ "name": "Toys", "description": "Games and toys" } 
``` 

Response, 201: 

```json 
{ "id": 4, "name": "Toys", "description": "Games and toys", "item_count": 0 } 
```

Create an item (`POST /api/v1/items`). `name`, `sku`, `price`, and `category_id` are required. `quantity` defaults to 0 and `status`to `in_stock`. 

```json 
{ "name": "Board Game", "sku": "BG-900", "price": 34.5, "quantity": 10, "category_id": 4 }
 ```

Response, 201: 

```json 
{ 
   "id": 9, "name": "Board Game", "sku": "BG-900", "price": 34.5, 
   "quantity": 10, "status":"in_stock", 
   "category_id": 4, "category": { "id": 4, "name": "Toys" } 
} 
``` 

Update an item (`PUT /api/v1/items/9`). Send only the fields that change: 

```json 
{ "price": 29.99, "status": "out_of_stock" } 
``` 

Filter items: `GET /api/v1/items?category_id=1&status=in_stock` 

Delete a category (`DELETE /api/v1/categories/3`), 200: 

```json 
{ "message": "Category 3 deleted", "items_deleted": 2 } 
```

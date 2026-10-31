import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "company.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Relational Data Models
class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    employees = db.relationship("Employee", backref="department", cascade="all, delete-orphan", lazy=True)

    def to_dict(self, include_employees=False):
        data = {"id": self.id, "name": self.name, "location": self.location}
        if include_employees:
            data["employees"] = [e.to_dict() for e in self.employees]
        return data

class Employee(db.Model):
    __tablename__ = "employees"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(80), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "department_id": self.department_id
        }

with app.app_context():
    db.create_all()

# Department Endpoints
@app.route("/api/departments", methods=["GET"])
def get_departments():
    depts = Department.query.all()
    return jsonify({"count": len(depts), "data": [d.to_dict(include_employees=True) for d in depts]}), 200

@app.route("/api/departments", methods=["POST"])
def create_department():
    data = request.get_json()
    if not data or "name" not in data or "location" not in data:
        return jsonify({"error": "Missing name or location"}), 400
    if Department.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Department already exists"}), 409
    
    dept = Department(name=data["name"], location=data["location"])
    db.session.add(dept)
    db.session.commit()
    return jsonify({"message": "Department created", "data": dept.to_dict()}), 201

# Employee Endpoints (Nested / Relational)
@app.route("/api/departments/<int:dept_id>/employees", methods=["POST"])
def add_employee_to_dept(dept_id):
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({"error": f"Department {dept_id} not found"}), 404
    
    data = request.get_json()
    if not data or "name" not in data or "email" not in data or "role" not in data:
        return jsonify({"error": "Missing employee fields (name, email, role)"}), 400
    if Employee.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 409

    emp = Employee(name=data["name"], email=data["email"], role=data["role"], department_id=dept.id)
    db.session.add(emp)
    db.session.commit()
    return jsonify({"message": "Employee added", "data": emp.to_dict()}), 201

@app.route("/api/departments/<int:dept_id>", methods=["DELETE"])
def delete_department(dept_id):
    dept = Department.query.get(dept_id)
    if not dept:
        return jsonify({"error": f"Department {dept_id} not found"}), 404
    db.session.delete(dept)
    db.session.commit()
    return jsonify({"message": f"Department {dept_id} and associated employees deleted"}), 200

@app.route("/api/departments/<int:dept_id>", methods=["GET"]) 
def get_department(dept_id): 
    dept = db.session.get(Department, dept_id) 
    if not dept: 
        return jsonify({"error": f"Department {dept_id} not found"}), 404
    return jsonify({"data": dept.to_dict(include_employees=True)}), 200 

@app.route("/api/employees", methods=["GET"]) 
def get_employees(): 
    emps = Employee.query.all() 
    return jsonify({"count": len(emps), "data": [e.to_dict() for e in emps]}), 200 

@app.route("/api/employees/<int:emp_id>", methods=["GET"]) 
def get_employee(emp_id):
    emp = db.session.get(Employee, emp_id)
    if not emp:
        return jsonify({"error": f"Employee {emp_id} not found"}), 404 
    return jsonify({"data": emp.to_dict()}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)


import os
import json

from flask import Flask, jsonify, request, abort, make_response
from flask_sqlalchemy import SQLAlchemy
import dotenv
from sqlalchemy import create_engine, exc
from sqlalchemy_utils import database_exists, create_database
from marshmallow import Schema, ValidationError, fields

dotenv.load_dotenv()

db_user = os.environ.get('DB_USERNAME')
db_pass = os.environ.get('DB_PASSWORD')
db_hostname = os.environ.get('DB_HOSTNAME')
db_name = os.environ.get('DB_NAME')

DB_URI = 'mysql+pymysql://{db_username}:{db_password}@{db_host}/{database}'.format(db_username=db_user,
                                                                                   db_password=db_pass,
                                                                                   db_host=db_hostname,
                                                                                   database=db_name)

engine = create_engine(DB_URI, echo=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    cellphone = db.Column(db.String(13), unique=True, nullable=False)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_by_id(cls, id):
        return cls.query.get_or_404(id)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update(self):
        try:
            db.session.commit()
        except exc.IntegrityError as e:
            db.session.rollback()
            abort(make_response(jsonify({'message': 'email or cellphone fields should be unique'}), 400))


class StudentSchema(Schema):
    id = fields.Integer()
    name = fields.Str(required=True)
    email = fields.Str(required=True)
    age = fields.Integer(required=True)
    cellphone = fields.Str(required=True)


@app.route('/', methods=['GET'])
def home():
    return '<p>Hello from students API!</p>', 200


@app.route('/api', methods=['GET'])
def api_main():
    with open('doc.json', 'r') as f:
        doc = json.loads(f.read())
    return jsonify(doc), 200


@app.route('/api/students', methods=['GET'])
def get_all_students():
    students = Student.get_all()
    student_list = StudentSchema(many=True)
    response = student_list.dump(students)
    return jsonify(response), 200


@app.route('/api/students/get/<int:id>', methods=['GET'])
def get_student(id):
    student_info = Student.get_by_id(id)
    serializer = StudentSchema()
    response = serializer.dump(student_info)
    return jsonify(response), 200


@app.route('/api/students/add', methods=['POST'])
def add_student():
    json_data = request.get_json()
    new_student = Student(
        name=json_data.get('name'),
        email=json_data.get('email'),
        age=json_data.get('age'),
        cellphone=json_data.get('cellphone')
    )
    new_student.save()
    serializer = StudentSchema()
    data = serializer.dump(new_student)
    return jsonify(data), 201


@app.route('/api/deleteStudent/<int:id>', methods=['DELETE'])
def delete_student(id):
    student = Student.get_by_id(id)
    student.delete()
    return jsonify({'result': True}), 200


@app.route('/api/students/modify/<int:id>', methods=['PATCH'])
def modify_student(id):
    json_data = request.get_json()

    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400

    student = Student.get_by_id(id)
    if 'name' in json_data:
        student.name = json_data.get('name')
    if 'email' in request.json:
        student.email = json_data.get('email')
    if 'age' in request.json:
        student.age = json_data.get('age')
    if 'cellphone' in json_data:
        student.cellphone = json_data.get('cellphone')
    student.update()
    serializer = StudentSchema()
    data = serializer.dump(student)
    return jsonify(data), 200


@app.route('/api/students/change/<int:id>', methods=['PUT'])
def change_student(id):
    json_data = request.get_json()

    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    try:
        StudentSchema().load(json_data)
    except ValidationError as err:
        return err.messages, 422

    student = Student.get_by_id(id)
    student.name = json_data.get('name')
    student.email = json_data.get('email')
    student.age = json_data.get('age')
    student.cellphone = json_data.get('cellphone')
    student.update()
    serializer = StudentSchema()
    data = serializer.dump(student)
    return jsonify(data), 200


@app.route('/api/health-check/ok', methods=['GET'])
def health_check_pass():
    return jsonify({'message': 'Server is up'}), 200


@app.route('/api/health-check/bad', methods=['GET'])
def health_check_fail():
    return jsonify({'message': 'Server is down'}), 500


if __name__ == '__main__':
    if not database_exists(engine.url):
        create_database(engine.url)
    db.create_all()
    app.run(debug=True)

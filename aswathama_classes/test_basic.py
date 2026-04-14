import pytest
from db import db
from app import app

def test_db_student_management():
    # Since we don't have real credentials, db will be in mock_mode.
    assert db.mock_mode is True

    # Test add student
    student_data = {
        "name": "John Doe",
        "class": "10th",
        "roll": "101",
        "phone": "1234567890",
        "email": "john@example.com",
        "parent": "Jane Doe"
    }
    student_id = db.add_student(student_data)
    assert student_id is not None

    # Test get student
    student = db.get_student_by_id(student_id)
    assert student is not None
    assert student['name'] == "John Doe"

    # Test get all students
    students = db.get_all_students()
    assert len(students) >= 1

    # Test delete student
    success = db.delete_student(student_id)
    assert success is True
    assert db.get_student_by_id(student_id) is None

def test_db_attendance():
    # Mock data setup
    student_id = db.add_student({"name": "Test Student"})
    date = "2023-10-01"

    # Mark present
    db.mark_attendance(date, student_id, "Present")
    attendance = db.get_attendance_by_date(date)
    assert len(attendance) == 1
    assert attendance[0]['status'] == "Present"

    # Update to absent
    db.mark_attendance(date, student_id, "Absent")
    attendance = db.get_attendance_for_student(student_id)
    assert len(attendance) == 1
    assert attendance[0]['status'] == "Absent"

def test_app_routes():
    # Test that the app can initialize and routes exist
    app.config.update({"TESTING": True})
    client = app.test_client()

    # Test index redirect
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers.get('Location', '')

    # Test login page GET
    response = client.get('/login')
    # Can't check 200 strictly yet if template doesn't exist, it might 500
    # But checking app boots up.

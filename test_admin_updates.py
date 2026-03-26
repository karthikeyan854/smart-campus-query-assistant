import unittest
import json
import sqlite3
from app import app, get_db_connection

class AdminUpdateTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Create a test admin session
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1 # Assuming 1 is admin or I should check
            sess['role'] = 'admin'
            
        # Create a test student
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        
        # Insert test student
        self.cursor.execute("INSERT INTO users (username, password, role, roll_no, course, year) VALUES (?, ?, ?, ?, ?, ?)",
                       ("test_updater", "pass", "student", "TEST001", "BCA", "Year 1"))
        self.test_user_id = self.cursor.lastrowid
        
        # Init related tables
        self.cursor.execute("INSERT INTO academics (user_id, gpa, subjects) VALUES (?, ?, ?)", (self.test_user_id, 0.0, "None"))
        self.cursor.execute("INSERT INTO attendance (user_id, total_classes, attended_classes, percentage) VALUES (?, ?, ?, ?)", (self.test_user_id, 0, 0, 0.0))
        self.cursor.execute("INSERT INTO fees (user_id, total_fee, paid, due) VALUES (?, ?, ?, ?)", (self.test_user_id, 0, 0, 0))
        self.cursor.execute("INSERT INTO exams (user_id, exam_name, score, result) VALUES (?, ?, ?, ?)", (self.test_user_id, "None", 0, "None"))
        self.cursor.execute("INSERT INTO library (user_id, books_issued, fine) VALUES (?, ?, ?)", (self.test_user_id, "None", 0))
        
        self.conn.commit()

    def tearDown(self):
        # Cleanup
        try:
            self.cursor.execute("DELETE FROM users WHERE id = ?", (self.test_user_id,))
            self.cursor.execute("DELETE FROM academics WHERE user_id = ?", (self.test_user_id,))
            self.cursor.execute("DELETE FROM attendance WHERE user_id = ?", (self.test_user_id,))
            self.cursor.execute("DELETE FROM fees WHERE user_id = ?", (self.test_user_id,))
            self.cursor.execute("DELETE FROM exams WHERE user_id = ?", (self.test_user_id,))
            self.cursor.execute("DELETE FROM library WHERE user_id = ?", (self.test_user_id,))
            self.conn.commit()
            self.conn.close()
        except:
            pass

    def test_update_academics(self):
        response = self.client.post('/admin/update_academics', json={
            'user_id': self.test_user_id,
            'gpa': 9.5,
            'subjects': 'AI, ML'
        })
        self.assertEqual(response.status_code, 200)
        
        # Verify DB
        row = self.conn.execute("SELECT * FROM academics WHERE user_id = ?", (self.test_user_id,)).fetchone()
        self.assertEqual(row['gpa'], 9.5)
        self.assertEqual(row['subjects'], 'AI, ML')

    def test_update_attendance(self):
        response = self.client.post('/admin/update_attendance', json={
            'user_id': self.test_user_id,
            'total_classes': 100,
            'attended_classes': 90,
            'percentage': 90.0
        })
        self.assertEqual(response.status_code, 200)
        
        row = self.conn.execute("SELECT * FROM attendance WHERE user_id = ?", (self.test_user_id,)).fetchone()
        self.assertEqual(row['total_classes'], 100)
        self.assertEqual(row['percentage'], 90.0)

    def test_update_fees(self):
        response = self.client.post('/admin/update_fees', json={
            'user_id': self.test_user_id,
            'total_fee': 50000,
            'paid': 25000,
            'due': 25000
        })
        self.assertEqual(response.status_code, 200)
        
        row = self.conn.execute("SELECT * FROM fees WHERE user_id = ?", (self.test_user_id,)).fetchone()
        self.assertEqual(row['due'], 25000)

    def test_update_exams(self):
        response = self.client.post('/admin/update_exams', json={
            'user_id': self.test_user_id,
            'exam_name': 'Finals',
            'score': 95,
            'result': 'Pass'
        })
        self.assertEqual(response.status_code, 200)
        
        row = self.conn.execute("SELECT * FROM exams WHERE user_id = ?", (self.test_user_id,)).fetchone()
        self.assertEqual(row['exam_name'], 'Finals')
        self.assertEqual(row['score'], 95)

    def test_update_library(self):
        response = self.client.post('/admin/update_library', json={
            'user_id': self.test_user_id,
            'books_issued': 'Physics III',
            'fine': 50
        })
        self.assertEqual(response.status_code, 200)
        
        row = self.conn.execute("SELECT * FROM library WHERE user_id = ?", (self.test_user_id,)).fetchone()
        self.assertEqual(row['books_issued'], 'Physics III')
        self.assertEqual(row['fine'], 50)

if __name__ == '__main__':
    unittest.main()

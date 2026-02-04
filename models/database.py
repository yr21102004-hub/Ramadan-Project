"""
Database Models (SQLite Version)
Handles all database operations using SQL for better reliability.
"""
import sqlite3
import os
from datetime import datetime

class Database:
    """SQLite Database singleton class"""
    _instance = None
    DB_NAME = 'ramadan_company.db'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        """Initialize SQLite database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Users Table (Comprehensive)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                role TEXT DEFAULT 'user',
                profile_image TEXT,
                project_location TEXT,
                project_description TEXT,
                project_percentage INTEGER DEFAULT 0,
                two_factor_enabled BOOLEAN DEFAULT 0,
                two_factor_secret TEXT,
                specialization TEXT,
                experience_years INTEGER,
                status TEXT,
                created_at TEXT
            )
        ''')
        
        # 2. Chat Logs Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                user_name TEXT,
                message TEXT,
                response TEXT,
                timestamp TEXT,
                is_deleted_by_user INTEGER DEFAULT 0
            )
        ''')
        
        # Check and migrate columns if they don't exist (Migration Shim)
        try:
            cursor.execute("SELECT is_deleted_by_user FROM chat_logs LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE chat_logs ADD COLUMN is_deleted_by_user INTEGER DEFAULT 0")

        try:
            cursor.execute("SELECT chat_memory_enabled FROM users LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE users ADD COLUMN chat_memory_enabled BOOLEAN DEFAULT 1")
        
        # 3. Contacts Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                message TEXT,
                user_id TEXT,
                service TEXT,
                created_at TEXT,
                status TEXT DEFAULT 'pending',
                admin_response TEXT
            )
        ''')
        
        try:
             cursor.execute("SELECT status FROM contacts LIMIT 1")
        except sqlite3.OperationalError:
             cursor.execute("ALTER TABLE contacts ADD COLUMN status TEXT DEFAULT 'pending'")

        try:
             cursor.execute("SELECT admin_response FROM contacts LIMIT 1")
        except sqlite3.OperationalError:
             cursor.execute("ALTER TABLE contacts ADD COLUMN admin_response TEXT")
        
        # 4. Unanswered Questions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS unanswered_questions (
                question TEXT PRIMARY KEY,
                user_id TEXT,
                timestamp TEXT,
                admin_response TEXT
            )
        ''')
        
        # 5. Security Audit Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT,
                details TEXT,
                severity TEXT,
                timestamp TEXT
            )
        ''')
        
        # 6. Payments Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                full_name TEXT,
                amount REAL,
                method TEXT,
                timestamp TEXT,
                status TEXT DEFAULT 'Pending'
            )
        ''')
        
        # 7. Learned Answers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT UNIQUE,
                answer TEXT,
                learned_at TEXT
            )
        ''')
        
        # 8. Subscriptions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                email TEXT,
                created_at TEXT
            )
        ''')
        
        # 9. Ratings Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                worker_id TEXT,
                user_id TEXT,
                quality_rating INTEGER,
                behavior_rating INTEGER,
                comment TEXT,
                timestamp TEXT,
                created_at TEXT
            )
        ''')
        
        # 10. Complaints Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                subject TEXT,
                message TEXT,
                status TEXT DEFAULT 'قيد المراجعة',
                admin_notes TEXT,
                contact_phone TEXT,
                contact_email TEXT,
                admin_response TEXT,
                created_at TEXT
            )
        ''')
        
        # Migration for complaints table
        try:
            cursor.execute("SELECT contact_phone FROM complaints LIMIT 1")
        except sqlite3.OperationalError:
             cursor.execute("ALTER TABLE complaints ADD COLUMN contact_phone TEXT")
             
        try:
            cursor.execute("SELECT contact_email FROM complaints LIMIT 1")
        except sqlite3.OperationalError:
             cursor.execute("ALTER TABLE complaints ADD COLUMN contact_email TEXT")

        try:
            cursor.execute("SELECT admin_response FROM complaints LIMIT 1")
        except sqlite3.OperationalError:
             cursor.execute("ALTER TABLE complaints ADD COLUMN admin_response TEXT")

        # 11. Inspection Requests
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inspection_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                location TEXT,
                date TEXT,
                status TEXT DEFAULT 'new_request',
                worker_id TEXT,
                admin_notes TEXT,
                created_at TEXT
            )
        ''')

        # 12. Tickets Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                subject TEXT,
                category TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Open',
                created_at TEXT,
                last_updated TEXT
            )
        ''')

        # 13. Ticket Messages (Sub-table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                sender_id TEXT,
                message TEXT,
                attachment_path TEXT,
                timestamp TEXT,
                is_admin_reply BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_connection(self):
        conn = sqlite3.connect(self.DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    @property
    def users(self): return UserModel()

    def table(self, name):
        """Proxy for TinyDB table() method"""
        return GenericSQLiteModel(name)
    
    @property
    def chats(self): return ChatModel()
    
    @property
    def contacts(self): return ContactModel()
    
    @property
    def unanswered(self): return UnansweredQuestionsModel()
    
    @property
    def security_logs(self): return SecurityLogModel()
    
    @property
    def payments(self): return PaymentModel()
    
    @property
    def learned_answers(self): return LearnedAnswersModel()
    
    @property
    def subscriptions(self): return SubscriptionModel()
    
    @property
    def ratings(self): return GenericSQLiteModel('ratings')
    
    @property
    def complaints(self): return ComplaintModel()
    
    @property
    def inspection_requests(self): return GenericSQLiteModel('inspection_requests')

class SQLiteModel:
    """Base SQL Model"""
    def __init__(self, table):
        self.db_mgr = Database()
        self.table = table

    def _dict_from_row(self, row):
        if row is None: return None
        d = dict(row)
        if 'id' in d:
             d['doc_id'] = d['id']
        return d

    def _get_columns(self):
        conn = self.db_mgr.get_connection()
        try:
            cursor = conn.execute(f"PRAGMA table_info({self.table})")
            cols = [col[1] for col in cursor.fetchall()]
            return cols
        finally:
            conn.close()

    def _filter_data(self, data):
        """Filter input dict to only include keys that are columns in the table"""
        cols = self._get_columns()
        return {k: v for k, v in data.items() if k in cols}

class GenericSQLiteModel(SQLiteModel):
    """Fallback for tables without dedicated model classes yet"""
    def __init__(self, table):
        super().__init__(table)
    
    def all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table}").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def insert(self, data):
        filtered_data = self._filter_data(data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        conn = self.db_mgr.get_connection()
        try:
            cursor = conn.execute(sql, list(filtered_data.values()))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def search(self, query=None):
        # Very basic search shim for TinyDB compatibility
        # Supports simple equality checks if query is a dictionary {col: val}
        conn = self.db_mgr.get_connection()
        if isinstance(query, dict):
            conditions = []
            values = []
            for k, v in query.items():
                conditions.append(f"{k} = ?")
                values.append(v)
            if conditions:
                sql = f"SELECT * FROM {self.table} WHERE {' AND '.join(conditions)}"
                rows = conn.execute(sql, values).fetchall()
            else:
                rows = conn.execute(f"SELECT * FROM {self.table}").fetchall()
        else:
            # Fallback for complex queries (not supported) return all and let python filter if possible?
            # Or just return all as before (unsafe but keeps existing behavior)
            rows = conn.execute(f"SELECT * FROM {self.table}").fetchall()
        
        conn.close()
        return [self._dict_from_row(r) for r in rows]

    def get(self, doc_id=None, **kwargs):
        conn = self.db_mgr.get_connection()
        if doc_id:
            row = conn.execute(f"SELECT * FROM {self.table} WHERE id = ?", (doc_id,)).fetchone()
        elif kwargs:
            conditions = []
            values = []
            for k, v in kwargs.items():
                conditions.append(f"{k} = ?")
                values.append(v)
            row = conn.execute(f"SELECT * FROM {self.table} WHERE {' AND '.join(conditions)}", values).fetchone()
        else:
            row = None
        
        conn.close()
        return self._dict_from_row(row)

    def update(self, data, doc_ids=None, query=None):
        filtered_data = self._filter_data(data)
        if not filtered_data: return
        
        set_clause = ', '.join([f"{k} = ?" for k in filtered_data.keys()])
        values = list(filtered_data.values())
        
        sql = f"UPDATE {self.table} SET {set_clause}"
        
        if doc_ids:
            placeholders = ', '.join(['?'] * len(doc_ids))
            sql += f" WHERE id IN ({placeholders})"
            values.extend(doc_ids)
        elif isinstance(query, dict):
            conditions = []
            for k, v in query.items():
                conditions.append(f"{k} = ?")
                values.append(v)
            if conditions:
                sql += f" WHERE {' AND '.join(conditions)}"
        
        conn = self.db_mgr.get_connection()
        conn.execute(sql, values)
        conn.commit()
        conn.close()

    def remove(self, doc_ids=None):
        if not doc_ids: return
        conn = self.db_mgr.get_connection()
        placeholders = ', '.join(['?'] * len(doc_ids))
        conn.execute(f"DELETE FROM {self.table} WHERE id IN ({placeholders})", doc_ids)
        conn.commit()
        conn.close()

class UserModel(SQLiteModel):
    def __init__(self):
        super().__init__('users')
    
    def get_by_username(self, username):
        conn = self.db_mgr.get_connection()
        row = conn.execute(f"SELECT * FROM {self.table} WHERE username = ?", (username,)).fetchone()
        conn.close()
        return self._dict_from_row(row)
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table}").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, user_data):
        if 'created_at' not in user_data:
            user_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        filtered_data = self._filter_data(user_data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        
        conn = self.db_mgr.get_connection()
        try:
            conn.execute(sql, list(filtered_data.values()))
            conn.commit()
        finally:
            conn.close()
    
    def update(self, username, data):
        filtered_data = self._filter_data(data)
        if not filtered_data: return
        
        set_clause = ', '.join([f"{k} = ?" for k in filtered_data.keys()])
        values = list(filtered_data.values())
        values.append(username)
        sql = f"UPDATE {self.table} SET {set_clause} WHERE username = ?"
        
        conn = self.db_mgr.get_connection()
        try:
            conn.execute(sql, values)
            conn.commit()
        finally:
            conn.close()
    
    def delete(self, username):
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table} WHERE username = ?", (username,))
        conn.commit()
        conn.close()

class ChatModel(SQLiteModel):
    def __init__(self):
        super().__init__('chat_logs')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        # Admin gets everything, maybe indicate usage later
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def get_by_user(self, user_id):
        conn = self.db_mgr.get_connection()
        # Only show not-deleted-by-user
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE user_id = ? AND is_deleted_by_user = 0 ORDER BY timestamp DESC", (user_id,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, chat_data):
        if 'timestamp' not in chat_data:
            chat_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        filtered_data = self._filter_data(chat_data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        
        conn = self.db_mgr.get_connection()
        conn.execute(sql, list(filtered_data.values()))
        conn.commit()
        conn.close()
    
    def soft_delete_all(self, user_id):
        """Hides chats from user but keeps them for admin"""
        conn = self.db_mgr.get_connection()
        conn.execute(f"UPDATE {self.table} SET is_deleted_by_user = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def hard_delete_all(self, user_id):
        """Permanently deletes chats (for privacy mode)"""
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table} WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

class PaymentModel(SQLiteModel):
    def __init__(self):
        super().__init__('payments')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def get_by_user(self, username):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE username = ? ORDER BY timestamp DESC", (username,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, payment_data):
        if 'timestamp' not in payment_data:
            payment_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        filtered_data = self._filter_data(payment_data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        
        conn = self.db_mgr.get_connection()
        conn.execute(sql, list(filtered_data.values()))
        conn.commit()
        conn.close()

    def update_status(self, doc_id, status):
        conn = self.db_mgr.get_connection()
        conn.execute(f"UPDATE {self.table} SET status = ? WHERE id = ?", (status, doc_id))
        conn.commit()
        conn.close()

class SecurityLogModel(SQLiteModel):
    def __init__(self):
        super().__init__('security_audit_logs')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, event, details, severity="low"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db_mgr.get_connection()
        conn.execute(f"INSERT INTO {self.table} (event, details, severity, timestamp) VALUES (?, ?, ?, ?)", 
                     (event, details, severity, timestamp))
        conn.commit()
        conn.close()

    def truncate(self):
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table}")
        conn.commit()
        conn.close()

class ContactModel(SQLiteModel):
    def __init__(self):
        super().__init__('contacts')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY created_at DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def get_by_user(self, user_id):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]

    def create(self, name, phone, message, user_id=None, service=None):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = 'pending'
        conn = self.db_mgr.get_connection()
        try:
            conn.execute(f"INSERT INTO {self.table} (name, phone, message, user_id, service, created_at, status, admin_response) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (name, phone, message, user_id, service, created_at, status, None))
            conn.commit()
        except sqlite3.OperationalError:
            # Fallback (shim)
            try:
                 conn.execute(f"INSERT INTO {self.table} (name, phone, message, user_id, service, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (name, phone, message, user_id, service, created_at, status))
            except:
                 conn.execute(f"INSERT INTO {self.table} (name, phone, message, user_id, service, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                             (name, phone, message, user_id, service, created_at))
            conn.commit()
        finally:
            conn.close()

    def update_status(self, doc_id, status, admin_response=None):
        """Update message status and response"""
        conn = self.db_mgr.get_connection()
        if admin_response is not None:
             try:
                conn.execute(f"UPDATE {self.table} SET status = ?, admin_response = ? WHERE id = ?", (status, admin_response, doc_id))
             except sqlite3.OperationalError:
                # Column might be missing, try adding it or ignoring
                pass
        else:
             conn.execute(f"UPDATE {self.table} SET status = ? WHERE id = ?", (status, doc_id))
        conn.commit()
        conn.close()

    def delete(self, doc_id):
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table} WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()

class LearnedAnswersModel(SQLiteModel):
    def __init__(self):
        super().__init__('learned_answers')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY learned_at DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, question, answer):
        learned_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg_clean = question.lower().strip()
        conn = self.db_mgr.get_connection()
        try:
            conn.execute(f"INSERT OR REPLACE INTO {self.table} (question, answer, learned_at) VALUES (?, ?, ?)",
                         (msg_clean, answer, learned_at))
            conn.commit()
        finally:
            conn.close()

class UnansweredQuestionsModel(SQLiteModel):
    def __init__(self):
        super().__init__('unanswered_questions')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY timestamp DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, question, user_id):
        msg_clean = question.lower().strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db_mgr.get_connection()
        try:
            conn.execute(f"INSERT OR REPLACE INTO {self.table} (question, user_id, timestamp, admin_response) VALUES (?, ?, ?, NULL)",
                         (msg_clean, user_id, timestamp))
            conn.commit()
        finally:
            conn.close()

    def delete(self, question):
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table} WHERE question = ?", (question.lower().strip(),))
        conn.commit()
        conn.close()

    def delete_by_id(self, doc_id):
        """Delete unanswered question by doc_id"""
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table} WHERE doc_id = ?", (doc_id,))
        conn.commit()
        conn.close()

    def get_by_user(self, user_id):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]

    def get_by_question(self, question):
        """Get unanswered question by text"""
        conn = self.db_mgr.get_connection()
        try:
            row = conn.execute(f"SELECT * FROM {self.table} WHERE question = ?", (question.lower().strip(),)).fetchone()
            return self._dict_from_row(row)
        finally:
            conn.close()

    def delete_all(self):
        """Delete all unanswered questions"""
        conn = self.db_mgr.get_connection()
        conn.execute(f"DELETE FROM {self.table}")
        conn.commit()
        conn.close()

class ComplaintModel(SQLiteModel):
    def __init__(self):
        super().__init__('complaints')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} ORDER BY created_at DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]

    def get_by_user(self, username):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE username = ? ORDER BY created_at DESC", (username,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
        
    def create(self, username, subject, message, phone=None, email=None):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db_mgr.get_connection()
        conn.execute(f"INSERT INTO {self.table} (username, subject, message, contact_phone, contact_email, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                     (username, subject, message, phone, email, created_at))
        conn.commit()
        conn.close()

    def update_status(self, doc_id, status, admin_notes, admin_response=None):
        conn = self.db_mgr.get_connection()
        if admin_response:
             conn.execute(f"UPDATE {self.table} SET status = ?, admin_notes = ?, admin_response = ? WHERE id = ?", 
                          (status, admin_notes, admin_response, doc_id))
        else:
             conn.execute(f"UPDATE {self.table} SET status = ?, admin_notes = ? WHERE id = ?", 
                          (status, admin_notes, doc_id))
        conn.commit()
        conn.close()

class SubscriptionModel(SQLiteModel):
    def __init__(self):
        super().__init__('subscriptions')
    
    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table}").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def get_by_user(self, username):
        conn = self.db_mgr.get_connection()
        rows = conn.execute(f"SELECT * FROM {self.table} WHERE username = ?", (username,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def create(self, data):
        if 'created_at' not in data:
            data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filtered_data = self._filter_data(data)
        cols = ', '.join(filtered_data.keys())
        placeholders = ', '.join(['?'] * len(filtered_data))
        sql = f"INSERT INTO {self.table} ({cols}) VALUES ({placeholders})"
        conn = self.db_mgr.get_connection()
        conn.execute(sql, list(filtered_data.values()))
        conn.commit()
        conn.close()

class TicketModel(SQLiteModel):
    def __init__(self):
        super().__init__('tickets')

    def create(self, user_id, subject, category, priority='Medium'):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db_mgr.get_connection()
        cursor = conn.execute("INSERT INTO tickets (user_id, subject, category, priority, status, created_at, last_updated) VALUES (?, ?, ?, ?, 'Open', ?, ?)",
                     (user_id, subject, category, priority, created_at, created_at))
        tid = cursor.lastrowid
        conn.commit()
        conn.close()
        return tid

    def get_all(self):
        conn = self.db_mgr.get_connection()
        rows = conn.execute("SELECT * FROM tickets ORDER BY last_updated DESC").fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]

    def get_by_user(self, user_id):
        conn = self.db_mgr.get_connection()
        rows = conn.execute("SELECT * FROM tickets WHERE user_id = ? ORDER BY last_updated DESC", (user_id,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]
    
    def update_status(self, ticket_id, status):
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db_mgr.get_connection()
        conn.execute("UPDATE tickets SET status = ?, last_updated = ? WHERE id = ?", (status, updated_at, ticket_id))
        conn.commit()
        conn.close()

class TicketMessageModel(SQLiteModel):
    def __init__(self):
        super().__init__('ticket_messages')

    def create(self, ticket_id, sender_id, message, is_admin=False, attachment=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self.db_mgr.get_connection()
        # Update ticket timestamp too
        conn.execute("UPDATE tickets SET last_updated = ? WHERE id = ?", (timestamp, ticket_id))
        
        conn.execute("INSERT INTO ticket_messages (ticket_id, sender_id, message, attachment_path, timestamp, is_admin_reply) VALUES (?, ?, ?, ?, ?, ?)",
                     (ticket_id, sender_id, message, attachment, timestamp, 1 if is_admin else 0))
        conn.commit()
        conn.close()

    def get_by_ticket(self, ticket_id):
        conn = self.db_mgr.get_connection()
        rows = conn.execute("SELECT * FROM ticket_messages WHERE ticket_id = ? ORDER BY timestamp ASC", (ticket_id,)).fetchall()
        conn.close()
        return [self._dict_from_row(r) for r in rows]

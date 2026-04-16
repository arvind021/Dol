import sqlite3
from datetime import datetime, date

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_usage (
                user_id INTEGER PRIMARY KEY,
                usage_count INTEGER DEFAULT 0,
                last_used_date TEXT
            )
        ''')
        self.conn.commit()
    
    def can_use_bot(self, user_id):
        today = str(date.today())
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT usage_count, last_used_date FROM user_usage WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            # New user
            cursor.execute('INSERT INTO user_usage (user_id, usage_count, last_used_date) VALUES (?, 1, ?)', 
                          (user_id, today))
            self.conn.commit()
            return True, 9  # 9 uses left
        
        usage_count, last_date = result
        
        if last_date != today:
            # Reset for new day
            cursor.execute('UPDATE user_usage SET usage_count = 1, last_used_date = ? WHERE user_id = ?', 
                          (today, user_id))
            self.conn.commit()
            return True, 9
        
        if usage_count < 10:
            # Increment usage
            cursor.execute('UPDATE user_usage SET usage_count = usage_count + 1 WHERE user_id = ?', (user_id,))
            self.conn.commit()
            remaining = 10 - (usage_count + 1)
            return True, remaining
        
        # Limit reached
        return False, 0
    
    def get_remaining_uses(self, user_id):
        today = str(date.today())
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT usage_count, last_used_date FROM user_usage WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result is None:
            return 10
        
        usage_count, last_date = result
        
        if last_date != today:
            return 10
        
        return 10 - usage_count
    
    def close(self):
        self.conn.close()

import sqlite3
def get_db():
    try:
        conn = sqlite3.connect('app.db')
        return conn
    except Exception as e:
        print(e)

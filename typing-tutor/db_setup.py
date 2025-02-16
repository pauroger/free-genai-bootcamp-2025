import sqlite3
import json
import os
import sys

class DatabaseSetup:
    @staticmethod
    def create_database(db_file):
        try:
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            DatabaseSetup.enable_foreign_keys(conn)
            DatabaseSetup.create_tables(conn)
            print(f"Database '{db_file}' created or already exists.")
        except sqlite3.Error as e:
            print(f"Database creation failed: {e}")
            sys.exit(1)
        finally:
            if conn:
                conn.close()

    @staticmethod
    def insert_words(db_file, json_file):
        if not os.path.exists(json_file):
            print(f"JSON file '{json_file}' not found.")
            sys.exit(1)
        try:
            with open(json_file, 'r') as f:
                json_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON file: {e}")
            sys.exit(1)
        if not isinstance(json_data, list):
            print("JSON data should be an array of word objects.")
            sys.exit(1)
        try:
            conn = sqlite3.connect(db_file)
            conn.row_factory = sqlite3.Row
            DatabaseSetup.enable_foreign_keys(conn)
            DatabaseSetup.insert_words_into_db(conn, json_data)
        except sqlite3.Error as e:
            print(f"Database operation failed: {e}")
            sys.exit(1)
        finally:
            if conn:
                conn.close()

    @staticmethod
    def enable_foreign_keys(conn):
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.Error as e:
            print(f"Failed to enable foreign keys: {e}")
            sys.exit(1)

    @staticmethod
    def create_tables(conn):
        create_words_table_sql = """
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                german TEXT NOT NULL,
                english TEXT NOT NULL,
                parts TEXT
            );
        """
        create_word_reviews_table_sql = """
            CREATE TABLE IF NOT EXISTS word_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                review_date TEXT,
                review_score INTEGER,
                FOREIGN KEY (word_id) REFERENCES words(id) ON DELETE CASCADE
            );
        """
        try:
            conn.execute(create_words_table_sql)
            conn.execute(create_word_reviews_table_sql)
        except sqlite3.Error as e:
            print(f"Failed to create tables: {e}")
            sys.exit(1)

    @staticmethod
    def insert_words_into_db(conn, json_data):
        insert_word_sql = """
            INSERT INTO words (german, english, parts)
            VALUES (?, ?, ?);
        """
        cursor = conn.cursor()
        try:
            conn.execute("BEGIN")
            for index, word in enumerate(json_data):
                if not all(key in word for key in ('german', 'english', 'parts')):
                    print(f"Skipping entry at index {index}: Missing required fields.")
                    continue
                german = word['german']
                english = word['english']
                parts = json.dumps(word['parts'])
                try:
                    cursor.execute(insert_word_sql, (german, english, parts))
                    print(f"Inserted word: {german} - {english}")
                except sqlite3.Error as e:
                    print(f"Failed to insert word at index {index}: {e}")
                    continue
            conn.commit()
        except sqlite3.Error as e:
            print(f"Failed to insert data: {e}")
            conn.rollback()
            sys.exit(1)
        finally:
            cursor.close()

if __name__ == '__main__':
    DB_FILE = 'words.db'
    JSON_FILE = "./datasets/words.json"

    DatabaseSetup.create_database(DB_FILE)
    DatabaseSetup.insert_words(DB_FILE, JSON_FILE)
    print("Database setup and data insertion complete.")

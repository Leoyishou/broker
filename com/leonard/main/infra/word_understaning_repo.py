import os
import logging
import psycopg2
from psycopg2 import sql
from typing import List, Dict, Optional
from datetime import datetime
from contextlib import contextmanager

class WordUnderstandingRepo:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection = self._initialize_connection()

    def _initialize_connection(self):
        host = os.getenv('DB_HOST')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        port = os.getenv('DB_PORT')
        dbname = os.getenv("DB_DBNAME")
        return psycopg2.connect(host=host, user=user, password=password, port=port, dbname=dbname)

    @contextmanager
    def db_cursor(self):
        try:
            cursor = self.connection.cursor()
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def close_connection(self):
        if self.connection:
            self.connection.close()

    def add_word(self, word: str, understanding_level: int, notes: Optional[str] = None) -> bool:
        try:
            query = sql.SQL("""
                INSERT INTO word_understanding (word, understanding_level, notes)
                VALUES (%s, %s, %s)
                ON CONFLICT (word) DO UPDATE
                SET understanding_level = EXCLUDED.understanding_level,
                    notes = EXCLUDED.notes,
                    updated_at = CURRENT_TIMESTAMP
            """)
            with self.db_cursor() as cursor:
                cursor.execute(query, (word, understanding_level, notes))
            return True
        except Exception as e:
            self.logger.error(f"Error adding word: {e}")
            return False

    def get_word(self, word: str) -> Optional[Dict]:
        try:
            query = sql.SQL("SELECT * FROM word_understanding WHERE word = %s")
            with self.db_cursor() as cursor:
                cursor.execute(query, (word,))
            result = cursor.fetchone()
            if result:
                return {
                    "id": result[0],
                    "word": result[1],
                    "understanding_level": result[2],
                    "last_reviewed": result[3],
                    "notes": result[4],
                    "created_at": result[5],
                    "updated_at": result[6]
                }
            return None
        except Exception as e:
            self.logger.error(f"Error getting word: {e}")
            return None

    def update_understanding_level(self, word: str, new_level: int) -> bool:
        try:
            query = sql.SQL("""
                UPDATE word_understanding
                SET understanding_level = %s, last_reviewed = CURRENT_TIMESTAMP
                WHERE word = %s
            """)
            with self.db_cursor() as cursor:
                cursor.execute(query, (new_level, word))
            return True
        except Exception as e:
            self.logger.error(f"Error updating understanding level: {e}")
            return False

    def get_words_by_understanding_level(self, level: int) -> List[Dict]:
        try:
            query = sql.SQL("SELECT * FROM word_understanding WHERE understanding_level = %s")
            with self.db_cursor() as cursor:
                cursor.execute(query, (level,))
            results = cursor.fetchall()
            return [{
                "id": row[0],
                "word": row[1],
                "understanding_level": row[2],
                "last_reviewed": row[3],
                "notes": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            } for row in results]
        except Exception as e:
            self.logger.error(f"Error getting words by understanding level: {e}")
            return []

    def delete_word(self, word: str) -> bool:
        try:
            query = sql.SQL("DELETE FROM word_understanding WHERE word = %s")
            with self.db_cursor() as cursor:
                cursor.execute(query, (word,))
            return True
        except Exception as e:
            self.logger.error(f"Error deleting word: {e}")
            return False

    def get_all_words(self) -> List[Dict]:
        try:
            query = sql.SQL("SELECT * FROM word_understanding ORDER BY word")
            with self.db_cursor() as cursor:
                cursor.execute(query)
            results = cursor.fetchall()
            return [{
                "id": row[0],
                "word": row[1],
                "understanding_level": row[2],
                "last_reviewed": row[3],
                "notes": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            } for row in results]
        except Exception as e:
            self.logger.error(f"Error getting all words: {e}")
            return []

    def get_words_to_review(self, days_since_last_review: int) -> List[Dict]:
        try:
            query = sql.SQL("""
                SELECT * FROM word_understanding
                WHERE last_reviewed < CURRENT_DATE - INTERVAL %s DAY
                OR last_reviewed IS NULL
                ORDER BY last_reviewed NULLS FIRST, understanding_level
            """)
            with self.db_cursor() as cursor:
                cursor.execute(query, (days_since_last_review,))
            results = cursor.fetchall()
            return [{
                "id": row[0],
                "word": row[1],
                "understanding_level": row[2],
                "last_reviewed": row[3],
                "notes": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            } for row in results]
        except Exception as e:
            self.logger.error(f"Error getting words to review: {e}")
            return []
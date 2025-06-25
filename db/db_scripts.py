import os
import psycopg

from dataclasses import dataclass
from datetime import datetime
from psycopg.rows import class_row
"""
from dotenv import load_dotenv
load_dotenv()
"""

@dataclass
class Image:
    """Representation of row from table image."""

    id: int
    user_id: int
    request: str
    image: bytes
    date: datetime


class Database:
    """Database class."""

    def __init__(self):
        """Configure database."""
        """
        self.conn = psycopg.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        """
        self.conn = psycopg.connect(
            dbname=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASS"],
            host=os.environ["DB_HOST"],
            port=os.environ["DB_PORT"]
        )


    def add_image(self, user_id, request, image, date) -> None:
        """Add a new image to the database."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                    INSERT INTO image
                    (user_id, name, description, notification_time)
                    VALUES (%s, %s, %s, %s)
                """,
                (user_id, request, image, date)
            )
        self.conn.commit()

    def get_images(self, user_id) -> list[Image]:
        """Get all user's images from database."""
        with self.conn.cursor(row_factory=class_row(Image)) as cursor:
            cursor.execute(
                """
                    SELECT * FROM image
                    WHERE user_id = %s
                """,
                (user_id,)
            )
            records = cursor.fetchall()
        return records

    def delete_images(self, user_id) -> None:
        """Delete all user's images from database."""
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                    DELETE FROM image
                    WHERE user_id = %s;
                """,
                (user_id,)
            )
        self.conn.commit()

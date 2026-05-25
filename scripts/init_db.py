"""
Run once (or whenever you drop the DB) to create empty tables.
"""
from app.services.kb import create_db_and_tables

if __name__ == "__main__":
    create_db_and_tables()
"""
Creates adaptive.db with empty tables.
Run via:
    python -m scripts.init_db
"""
from app.services.kb import create_db_and_tables


def main():
    create_db_and_tables()


if __name__ == "__main__":
    main()
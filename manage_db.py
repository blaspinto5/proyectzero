"""
Utility script to manage projectzero2 DB and outputs.

Usage:
    python manage_db.py --help

Actions:
- --wipe-db : truncates the `items` table in DATABASE_URL
- --drop-db : drops the `items` table
- --clean-output : removes ./output/output.csv and ./output/output.json

By default reads DATABASE_URL from environment or uses the value in settings.
"""
import os
import argparse
from sqlalchemy import create_engine, MetaData, Table

# default DATABASE_URL used by the project
DEFAULT_DB = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/projectzero")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
JSON_FILE = os.path.join(OUTPUT_DIR, "output.json")
CSV_FILE = os.path.join(OUTPUT_DIR, "output.csv")


def get_engine(db_url):
    return create_engine(db_url)


def drop_table(db_url):
    engine = get_engine(db_url)
    metadata = MetaData()
    t = Table('items', metadata)
    metadata.reflect(bind=engine)
    if 'items' in metadata.tables:
        tbl = metadata.tables['items']
        tbl.drop(bind=engine)
        print('Dropped table items')
    else:
        print('Table items does not exist')
    engine.dispose()


def truncate_table(db_url):
    engine = get_engine(db_url)
    conn = engine.connect()
    try:
        conn.execute("TRUNCATE TABLE items;")
        print('Truncated items table')
    except Exception as e:
        print('Error truncating table:', e)
    finally:
        conn.close()
        engine.dispose()


def clean_output_files():
    removed = []
    if os.path.exists(JSON_FILE):
        os.remove(JSON_FILE)
        removed.append(JSON_FILE)
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
        removed.append(CSV_FILE)
    if removed:
        print('Removed:', ', '.join(removed))
    else:
        print('No output files to remove')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--wipe-db', action='store_true', help='TRUNCATE items table')
    parser.add_argument('--drop-db', action='store_true', help='DROP items table')
    parser.add_argument('--clean-output', action='store_true', help='Delete output files in ./output')
    parser.add_argument('--db', default=DEFAULT_DB, help='Database URL')
    args = parser.parse_args()

    if args.wipe_db:
        truncate_table(args.db)
    if args.drop_db:
        drop_table(args.db)
    if args.clean_output:
        clean_output_files()
    if not (args.wipe_db or args.drop_db or args.clean_output):
        parser.print_help()

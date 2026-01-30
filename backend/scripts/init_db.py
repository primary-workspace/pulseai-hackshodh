#!/usr/bin/env python3
"""
Quick database initialization script
"""

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, engine
from sqlalchemy import inspect

def main():
    print("=" * 50)
    print("Pulse AI - Database Initialization")
    print("=" * 50)
    
    # Create all tables from SQLAlchemy models
    print("\n1. Creating tables from models...")
    init_db()
    print("   Done!")
    
    # Check what tables exist
    print("\n2. Checking tables...")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"   Found {len(tables)} tables:")
    for table in sorted(tables):
        columns = [col['name'] for col in inspector.get_columns(table)]
        print(f"   - {table}: {len(columns)} columns")
    
    print("\n" + "=" * 50)
    print("Database initialization complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()

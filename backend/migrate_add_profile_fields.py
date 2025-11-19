#!/usr/bin/env python3
"""
Migration script to add phone and date_of_birth fields to users table
Run this after deploying the updated models.py
"""

import os
import sys
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app import app, db

def migrate_database():
    """Add new columns to users table"""
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Check if columns already exist
                result = conn.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result]
                
                # Add phone column if it doesn't exist
                if 'phone' not in columns:
                    print("Adding 'phone' column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(20)"))
                    conn.commit()
                    print("✅ Added 'phone' column")
                else:
                    print("ℹ️  'phone' column already exists")
                
                # Add date_of_birth column if it doesn't exist
                if 'date_of_birth' not in columns:
                    print("Adding 'date_of_birth' column to users table...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN date_of_birth DATE"))
                    conn.commit()
                    print("✅ Added 'date_of_birth' column")
                else:
                    print("ℹ️  'date_of_birth' column already exists")
                
                print("\n✅ Migration completed successfully!")
                
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Add Profile Fields")
    print("=" * 60)
    migrate_database()

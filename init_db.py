!/usr/bin/env python3
"""
Database initialization script for Flask app
Converts MySQL schema to SQLite and creates the database
"""

import sqlite3
import os

def create_database():
    
    db_path = 'practical_management.db'
    
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    
    
    
    cursor.execute('''
        CREATE TABLE Student (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name VARCHAR(100) NOT NULL,
            email_address VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Practical table
    cursor.execute('''
        CREATE TABLE Practical (
            prac_number INTEGER PRIMARY KEY AUTOINCREMENT,
            prac_name VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Supplier table
    cursor.execute('''
        CREATE TABLE Supplier (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name VARCHAR(45) NOT NULL,
            supplier_location VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. Components table
    cursor.execute('''
        CREATE TABLE Components (
            component_id INTEGER PRIMARY KEY AUTOINCREMENT,
            component_name VARCHAR(45) NOT NULL,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
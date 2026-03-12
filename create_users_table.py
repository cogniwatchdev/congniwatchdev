#!/usr/bin/env python3
"""Create users table in CogniWatch database and add admin user."""

import sqlite3
import hashlib
import secrets

DB_PATH = '/cogniwatch/data/cogniwatch.db'
ADMIN_USER = 'admin'
ADMIN_PASS = 'cogniwatch2026'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create users table
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'viewer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
)
''')

# Hash the password
salt = secrets.token_hex(16)
password_hash = hashlib.sha256((salt + ADMIN_PASS).encode()).hexdigest()

# Insert admin user
try:
    cursor.execute('''
    INSERT INTO users (username, password_hash, role)
    VALUES (?, ?, ?)
    ''', (ADMIN_USER, password_hash, 'admin'))
    conn.commit()
    print('✓ Created admin user')
except sqlite3.IntegrityError:
    print('ℹ Admin user already exists')

# Verify
cursor.execute('SELECT id, username, role FROM users')
print('Users:', cursor.fetchall())

conn.close()
print('✓ Users table created successfully')

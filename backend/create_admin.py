"""
create_admin.py
---------------
Run this ONCE from the backend/ folder to create an admin user:

    python create_admin.py

The script hashes the password properly and inserts the admin
into the 'admins' collection. Delete this file or restrict access
after use — it should never be exposed publicly.
"""

import asyncio
import bcrypt
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from database.mongo import connect_to_mongo, close_mongo_connection
import database.mongo as mongo_module


ADMIN_NAME = "Axis Admin"
ADMIN_EMAIL = "abc@axis.com"
ADMIN_PASSWORD = "abcdef"       # User must change this on first login
ADMIN_ROLE = "Fraud Analyst"                # Options: "Analyst", "SuperAdmin", etc.
ADMIN_ID = "ADM12"


async def create_admin():
    # 1. Connect to MongoDB first
    await connect_to_mongo()
    db = mongo_module.db

    # 2. Check if admin already exists
    existing = await db.admins.find_one({"email": ADMIN_EMAIL})
    if existing:
        print(f"[!] Admin '{ADMIN_EMAIL}' already exists. Aborting.")
        await close_mongo_connection()
        return

    # 3. Hash the password
    hashed = bcrypt.hashpw(
        ADMIN_PASSWORD.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # 4. Insert admin document
    new_admin = {
        "admin_id": ADMIN_ID,
        "name": ADMIN_NAME,
        "email": ADMIN_EMAIL,
        "password_hash": hashed,
        "role": ADMIN_ROLE,
        "created_at": "2026-02-01",
        "must_change_password": True
    }

    await db.admins.insert_one(new_admin)
    print(f"[✓] Admin created successfully!")
    print(f"    Email   : {ADMIN_EMAIL}")
    print(f"    Password: {ADMIN_PASSWORD}  ← share securely, ask user to change")
    await close_mongo_connection()


asyncio.run(create_admin())
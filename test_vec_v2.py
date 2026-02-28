#!/usr/bin/env python3
import sqlite3
import sqlite_vec

# Enable extension loading
conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True)

# Try loading the extension using the loadable_path
ext_path = sqlite_vec.loadable_path()
print(f'Extension path: {ext_path}')

conn.execute(f"SELECT load_extension('{ext_path}')")

# Check available functions
cursor = conn.execute("SELECT name FROM pragma_function_list WHERE name LIKE '%vec%'")
print('vec functions:', cursor.fetchall())

# Check for similarity functions
cursor = conn.execute("SELECT name FROM pragma_function_list WHERE name LIKE '%similar%'")
print('Similarity functions:', cursor.fetchall())

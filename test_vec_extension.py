#!/usr/bin/env python3
import sqlite3
import sqlite_vec

conn = sqlite3.connect(':memory:')
sqlite_vec.load(conn)

# Check available functions
cursor = conn.execute("SELECT name FROM pragma_function_list WHERE name LIKE '%similar%'")
print('Similarity functions:', cursor.fetchall())

# Try cosine_similarity
try:
    cursor = conn.execute("SELECT cosine_similarity(?, ?)", 
        (sqlite_vec.serialize_float32([0.1]*1536), sqlite_vec.serialize_float32([0.1]*1536)))
    print('cosine_similarity result:', cursor.fetchone())
except Exception as e:
    print(f'Error: {e}')

#!/usr/bin/env python3
import sqlite_vec
print('sqlite_vec attributes:')
for attr in dir(sqlite_vec):
    if not attr.startswith('_'):
        print(f'  {attr}')

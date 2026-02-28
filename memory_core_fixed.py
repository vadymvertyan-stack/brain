#!/usr/bin/env python3
"""
Плагін Memory Core для чанкування та індексації
Використовує sqlite-vec для векторного зберігання
"""

import sqlite3
import sqlite_vec
import os
import json
from typing import List, Dict, Any, Optional, Tuple

class MemoryCore:
    def __init__(self, db_path: str = "memory_vector.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()
    
    def _init_db(self):
        """Ініціалізація бази даних"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            
            # Enable extension loading for sqlite-vec
            self.conn.enable_load_extension(True)
            sqlite_vec.load(self.conn)
            
            # Створюємо таблицю для векторів (sqlite-vec підхід - без індексу)
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE,
                content TEXT,
                embedding BLOB,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Створюємо індекс для пришвидшення пошуку (опціонально)
            # sqlite-vec не вимагає спеціального індексу для cosine_similarity
            self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunk_id ON memory_chunks(chunk_id)
            """)
            
            self.conn.commit()
            
            print(f"✅ MemoryCore ініціалізовано: {self.db_path}")
            
        except Exception as e:
            print(f"❌ Помилка ініціалізації БД: {e}")
            raise
    
    def chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Розбивка тексту на чанки"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        
        return chunks
    
    def get_embedding(self, text: str) -> bytes:
        """Отримання ембедінгу для тексту"""
        try:
            # Для тесту використовуємо тестове embedding
            # В майбутньому замінити на реальне API
            return sqlite_vec.serialize_float32([0.1] * 1536)
        except Exception as e:
            print(f"❌ Помилка генерації embedding: {e}")
            return None
    
    def store_chunk(self, chunk: str, metadata: Dict[str, Any] = None) -> bool:
        """Збереження чанка в БД"""
        try:
            embedding = self.get_embedding(chunk)
            if not embedding:
                return False
            
            metadata_str = json.dumps(metadata) if metadata else None
            chunk_id = f"chunk_{len(chunk)}_{hash(chunk) % 1000000}"
            
            self.conn.execute(
                "INSERT OR REPLACE INTO memory_chunks (chunk_id, content, embedding, metadata) VALUES (?, ?, ?, ?)",
                (chunk_id, chunk, embedding, metadata_str)
            )
            self.conn.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Помилка збереження чанка: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Семантичний пошук"""
        try:
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                return []
            
            # sqlite-vec використовує функцію vec_distance_cosine
            # (менше значення = більша схожість, тому ORDER BY ASC)
            cursor = self.conn.execute("""
            SELECT content, metadata, vec_distance_cosine(embedding, ?) as score
            FROM memory_chunks
            ORDER BY score ASC
            LIMIT ?
            """, (query_embedding, top_k))
            
            results = []
            for row in cursor.fetchall():
                content, metadata_str, score = row
                metadata = json.loads(metadata_str) if metadata_str else {}
                results.append((content, score, metadata))
            
            return results
            
        except Exception as e:
            print(f"❌ Помилка пошуку: {e}")
            return []
    
    def close(self):
        """Закриття з'єднання"""
        if self.conn:
            self.conn.close()

def test_memory_core():
    """Тестування MemoryCore"""
    print("🧪 Тестування MemoryCore...")
    
    # Видаляємо стару тестову БД
    if os.path.exists("test_memory_core.db"):
        os.remove("test_memory_core.db")
    
    # Ініціалізація
    mem = MemoryCore("test_memory_core.db")
    
    # Тестовий текст
    test_text = "".join([
        "Це тестовий текст для перевірки роботи MemoryCore. ",
        "Ми розбиваємо йо чанки для ефективного зберігання. ",
        "Кожен чанк має унікальний ідентифікатор та ембедінг для семантичного пошуку. ",
        "Це дозволяє швидко знаходити релевантну інформацію серед великої кількості даних.",
        "MemoryCore використовує sqlite-vec для ефективної векторної індексації.",
        "Це дозволяє швидко знаходити схожі чанки за семантичним змістом.",
    ]) 
    
    # Чанкування
    chunks = mem.chunk_text(test_text, chunk_size=100)
    print(f"✅ Розбито на {len(chunks)} чанків")
    
    # Збереження чанків
    for i, chunk in enumerate(chunks):
        metadata = {"chunk_num": i + 1, "total_chunks": len(chunks)}
        success = mem.store_chunk(chunk, metadata)
        print(f"✅ Збережено чанк {i + 1}/{len(chunks)}: {success}")
    
    # Семантичний пошук
    query = "efective storage chunks"
    results = mem.search_similar(query, top_k=3)
    
    print(f"\n✅ Результати пошуку для '{query}':")
    for i, (content, score, metadata) in enumerate(results, 1):
        print(f"  {i}. Score: {score:.4f}")
        print(f"     Content: {content[:50]}...")
        print(f"     Metadata: {metadata}")
    
    # Закриття
    mem.close()
    print("✅ MemoryCore тест завершено!")

if __name__ == "__main__":
    test_memory_core()

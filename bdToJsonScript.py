import sqlite3
import json

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

cursor.execute("SELECT id, title, author,content,cover_path FROM books")
books = cursor.fetchall()

# Convertir en JSON
with open("books.json", "w", encoding="utf-8") as f:
    json.dump([{"id": row[0], "title": row[1], "author": row[2], "content": row[3],"cover_path":row[4]} for row in books], f, ensure_ascii=False, indent=4)

print("Données exportées dans books.json.")

import sqlite3
import json

conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

# Charger le fichier JSON
with open("books.json", "r", encoding="utf-8") as f:
    books = json.load(f)

# Réinsérer dans la base
cursor.executemany("INSERT INTO books (id, title, author,content,cover_path) VALUES (?, ?, ?,?,?)", [(b["id"], b["title"], b["author"],b["content"],b["cover_path"]) for b in books])
conn.commit()
conn.close()

print("Données restaurées depuis books.json.")

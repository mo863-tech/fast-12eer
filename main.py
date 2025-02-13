from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# إنشاء قاعدة البيانات وجداولها
def get_db_connection():
    conn = sqlite3.connect("blog.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

create_table()

# نموذج بيانات الإدخال والإخراج
class Post(BaseModel):
    title: str
    content: str

class PostResponse(Post):
    id: int

# إنشاء مقال جديد
@app.post("/posts/", response_model=PostResponse)
def create_post(post: Post):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO posts (title, content) VALUES (?, ?)", (post.title, post.content))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return { "id": post_id, **post.dict() }

# جلب جميع المقالات
@app.get("/posts/", response_model=list[PostResponse])
def get_posts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts")
    posts = cursor.fetchall()
    conn.close()
    return [dict(post) for post in posts]

# جلب مقال معين
@app.get("/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    post = cursor.fetchone()
    conn.close()
    if not post:
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    return dict(post)

# تحديث مقال
@app.put("/posts/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post: Post):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    existing_post = cursor.fetchone()
    if not existing_post:
        conn.close()
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    
    cursor.execute("UPDATE posts SET title = ?, content = ? WHERE id = ?", (post.title, post.content, post_id))
    conn.commit()
    conn.close()
    return { "id": post_id, **post.dict() }

# حذف مقال
@app.delete("/posts/{post_id}")
def delete_post(post_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    existing_post = cursor.fetchone()
    if not existing_post:
        conn.close()
        raise HTTPException(status_code=404, detail="المقال غير موجود")
    
    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return {"message": "تم حذف المقال بنجاح"}
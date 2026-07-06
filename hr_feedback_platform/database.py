import sqlite3
import os
import json
from datetime import datetime
from config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes the SQLite database tables."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create documents table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        raw_text TEXT,
        uploaded_at TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """)
    
    # Create analysis_results table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analysis_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER UNIQUE NOT NULL,
        summary TEXT,
        overall_sentiment TEXT,
        sentiment_score REAL,
        strengths TEXT,  -- Store as JSON array string
        improvement_areas TEXT,  -- Store as JSON array string
        themes TEXT,  -- Store as JSON array string
        quotes TEXT,  -- Store as JSON array string
        recommended_actions TEXT,  -- Store as JSON array string
        analyzed_at TEXT,
        FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

def add_document(filename, filepath):
    """Adds a new document to the queue with 'pending' status."""
    conn = get_connection()
    cursor = conn.cursor()
    uploaded_at = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO documents (filename, filepath, raw_text, uploaded_at, status) VALUES (?, ?, ?, ?, ?)",
        (filename, filepath, "", uploaded_at, "pending")
    )
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def update_document_text(doc_id, text, status="ocr_completed"):
    """Updates the extracted raw text of a document."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET raw_text = ?, status = ? WHERE id = ?",
        (text, status, doc_id)
    )
    conn.commit()
    conn.close()

def update_document_status(doc_id, status):
    """Updates the status of a document (e.g. 'processing', 'failed')."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE documents SET status = ? WHERE id = ?",
        (status, doc_id)
    )
    conn.commit()
    conn.close()

def save_analysis_result(doc_id, analysis_data):
    """Saves the structured LLM analysis data and marks document as 'analyzed'."""
    conn = get_connection()
    cursor = conn.cursor()
    analyzed_at = datetime.now().isoformat()
    
    summary = analysis_data.get("summary", "")
    overall_sentiment = analysis_data.get("overall_sentiment", "Neutral")
    sentiment_score = analysis_data.get("sentiment_score", 5.0)
    
    # Serialize list fields to JSON strings
    strengths = json.dumps(analysis_data.get("strengths", []), ensure_ascii=False)
    improvement_areas = json.dumps(analysis_data.get("improvement_areas", []), ensure_ascii=False)
    themes = json.dumps(analysis_data.get("themes", []), ensure_ascii=False)
    quotes = json.dumps(analysis_data.get("representative_quotes", []), ensure_ascii=False)
    recommended_actions = json.dumps(analysis_data.get("recommended_actions", []), ensure_ascii=False)
    
    # Delete existing analysis if any to prevent conflicts
    cursor.execute("DELETE FROM analysis_results WHERE document_id = ?", (doc_id,))
    
    cursor.execute("""
        INSERT INTO analysis_results (
            document_id, summary, overall_sentiment, sentiment_score, 
            strengths, improvement_areas, themes, quotes, recommended_actions, analyzed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_id, summary, overall_sentiment, sentiment_score,
        strengths, improvement_areas, themes, quotes, recommended_actions, analyzed_at
    ))
    
    # Mark document as analyzed
    cursor.execute(
        "UPDATE documents SET status = 'analyzed' WHERE id = ?",
        (doc_id,)
    )
    
    conn.commit()
    conn.close()

def get_all_documents():
    """Retrieves all documents in the database."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_analyzed_documents():
    """Retrieves all documents that have been successfully analyzed with their results."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id, d.filename, d.filepath, d.raw_text, d.uploaded_at, d.status,
               r.summary, r.overall_sentiment, r.sentiment_score, r.strengths,
               r.improvement_areas, r.themes, r.quotes, r.recommended_actions, r.analyzed_at
        FROM documents d
        JOIN analysis_results r ON d.id = r.document_id
        WHERE d.status = 'analyzed'
        ORDER BY d.uploaded_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        d = dict(row)
        # Deserialize JSON strings back into Python lists
        d["strengths"] = json.loads(d["strengths"] or "[]")
        d["improvement_areas"] = json.loads(d["improvement_areas"] or "[]")
        d["themes"] = json.loads(d["themes"] or "[]")
        d["quotes"] = json.loads(d["quotes"] or "[]")
        d["recommended_actions"] = json.loads(d["recommended_actions"] or "[]")
        results.append(d)
        
    return results

def get_document_details(doc_id):
    """Retrieves full details of a specific document, including analysis if available."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc_row = cursor.fetchone()
    
    if not doc_row:
        conn.close()
        return None
        
    doc = dict(doc_row)
    
    cursor.execute("SELECT * FROM analysis_results WHERE document_id = ?", (doc_id,))
    res_row = cursor.fetchone()
    conn.close()
    
    if res_row:
        res = dict(res_row)
        doc["analysis"] = {
            "summary": res["summary"],
            "overall_sentiment": res["overall_sentiment"],
            "sentiment_score": res["sentiment_score"],
            "strengths": json.loads(res["strengths"] or "[]"),
            "improvement_areas": json.loads(res["improvement_areas"] or "[]"),
            "themes": json.loads(res["themes"] or "[]"),
            "representative_quotes": json.loads(res["quotes"] or "[]"),
            "recommended_actions": json.loads(res["recommended_actions"] or "[]"),
            "analyzed_at": res["analyzed_at"]
        }
    else:
        doc["analysis"] = None
        
    return doc

def search_documents(keyword):
    """Searches documents matching a keyword in raw text, summary, or themes."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # We retrieve all analyzed documents first and then filter
    # To keep simple SQL, we can run a LIKE search on database columns
    like_expr = f"%{keyword}%"
    cursor.execute("""
        SELECT d.id, d.filename, d.filepath, d.raw_text, d.uploaded_at, d.status,
               r.summary, r.overall_sentiment, r.sentiment_score, r.strengths,
               r.improvement_areas, r.themes, r.quotes, r.recommended_actions, r.analyzed_at
        FROM documents d
        JOIN analysis_results r ON d.id = r.document_id
        WHERE d.status = 'analyzed' AND (
            d.raw_text LIKE ? OR 
            r.summary LIKE ? OR 
            r.themes LIKE ? OR 
            r.strengths LIKE ? OR 
            r.improvement_areas LIKE ?
        )
        ORDER BY d.uploaded_at DESC
    """, (like_expr, like_expr, like_expr, like_expr, like_expr))
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        d = dict(row)
        d["strengths"] = json.loads(d["strengths"] or "[]")
        d["improvement_areas"] = json.loads(d["improvement_areas"] or "[]")
        d["themes"] = json.loads(d["themes"] or "[]")
        d["quotes"] = json.loads(d["quotes"] or "[]")
        d["recommended_actions"] = json.loads(d["recommended_actions"] or "[]")
        results.append(d)
        
    return results

def delete_document(doc_id):
    """Deletes a document from the database (cascades automatically in sqlite with pragma enabled, or manual delete)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON") # Ensure cascades are respected
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

# Automatically initialize database when database.py is imported/run
init_db()

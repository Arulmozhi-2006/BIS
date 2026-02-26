"""
BIS Smart Portal — Flask Backend
Run:  python app.py
Open: http://127.0.0.1:5000
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3, os, json

app = Flask(__name__)
CORS(app)

DATABASE = os.path.join(os.path.dirname(__file__), "bis.db")

# ── DB SETUP ─────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id               TEXT PRIMARY KEY,
            company          TEXT NOT NULL,
            gst              TEXT,
            state            TEXT,
            category         TEXT,
            specs            TEXT,
            app_type         TEXT,
            production_start TEXT,
            production_volume TEXT,
            score            INTEGER DEFAULT 0,
            risk             TEXT DEFAULT 'Unknown',
            status           TEXT DEFAULT 'pending',
            cml              TEXT,
            assigned_cml     TEXT,
            officer_remarks  TEXT,
            decision_date    TEXT,
            findings         TEXT,
            submitted_at     TEXT DEFAULT (datetime('now','localtime'))
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database ready →", DATABASE)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    d = dict(row)
    try:
        d['findings'] = json.loads(d['findings']) if d['findings'] else []
    except:
        d['findings'] = []
    return d

# ── ROUTES ───────────────────────────────────────────

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/submit_application", methods=["POST"])
def submit_application():
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400
    conn = get_db()
    try:
        conn.execute('''
            INSERT OR REPLACE INTO applications
              (id, company, gst, state, category, specs, app_type,
               production_start, production_volume, score, risk, findings)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            data.get("id","BIS-UNKNOWN"),
            data.get("company",""),
            data.get("gst",""),
            data.get("state",""),
            data.get("category",""),
            data.get("specs",""),
            data.get("appType",""),
            data.get("productionStart",""),
            data.get("productionVolume",""),
            data.get("score", 0),
            data.get("risk","Unknown"),
            json.dumps(data.get("findings",[]))
        ))
        conn.commit()
        return jsonify({"message": "Application submitted!", "id": data.get("id")})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/get_applications", methods=["GET"])
def get_applications():
    conn = get_db()
    rows = conn.execute("SELECT * FROM applications ORDER BY submitted_at DESC").fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])

@app.route("/get_application/<app_id>", methods=["GET"])
def get_application(app_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM applications WHERE id=?", (app_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)) if row else (jsonify({"error":"Not found"}), 404)

@app.route("/officer_decision", methods=["POST"])
def officer_decision():
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400
    conn = get_db()
    try:
        conn.execute('''
            UPDATE applications
               SET status=?, officer_remarks=?, assigned_cml=?, cml=?, decision_date=?
             WHERE id=?
        ''', (
            data.get("decision"),
            data.get("remarks",""),
            data.get("assignedCML"),
            data.get("assignedCML"),
            data.get("decisionDate",""),
            data.get("id")
        ))
        conn.commit()
        return jsonify({"message": f"Decision saved for {data.get('id')}"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route("/dashboard_stats", methods=["GET"])
def dashboard_stats():
    conn = get_db()
    def count(q): return conn.execute(q).fetchone()[0]
    stats = {
        "total":    count("SELECT COUNT(*) FROM applications"),
        "accepted": count("SELECT COUNT(*) FROM applications WHERE status='accepted'"),
        "rejected": count("SELECT COUNT(*) FROM applications WHERE status='rejected'"),
        "pending":  count("SELECT COUNT(*) FROM applications WHERE status='pending'"),
        "highRisk": count("SELECT COUNT(*) FROM applications WHERE score < 50"),
    }
    conn.close()
    return jsonify(stats)

# ── START ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("\n" + "═"*50)
    print("  🇮🇳  BIS Smart Portal — Server Running")
    print("═"*50)
    print("  Local:   http://127.0.0.1:5000")
    print("  Network: http://0.0.0.0:5000")
    print("  DB:      bis.db")
    print("═"*50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)

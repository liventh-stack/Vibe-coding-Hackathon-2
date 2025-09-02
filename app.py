from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
import datetime as dt
import mysql.connector
import requests

# ---------- Config ----------
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "mediuser"),
        password=os.environ.get("DB_PASSWORD", "medipass"),
        database=os.environ.get("DB_NAME", "medicounsel"),
        port=int(os.environ.get("DB_PORT", "3306")),
        auth_plugin=os.environ.get("DB_AUTH_PLUGIN", "mysql_native_password")
    )

HF_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
HF_MODEL = os.environ.get("HF_MODEL", "j-hartmann/emotion-english-distilroberta-base")
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

def call_hf_emotion_api(text):
    if not HF_API_KEY:
        return None
    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        resp = requests.post(HF_URL, headers=headers, json={"inputs": text}, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        # Some HF models return a list of list of dicts
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            scores = {item["label"]: float(item["score"]) for item in data[0]}
            top_label = max(scores, key=scores.get)
            return {"label": top_label, "scores": scores}
        # Or a single list
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "label" in data[0]:
            scores = {item["label"]: float(item["score"]) for item in data}
            top_label = max(scores, key=scores.get)
            return {"label": top_label, "scores": scores}
        return None
    except Exception as e:
        print("HF API error:", e)
        return None

# Fallback very simple lexicon-based emotion guess if no API key
POSITIVE_WORDS = {"happy","joy","grateful","thankful","hope","excited","calm","peace","good","great","love"}
NEGATIVE_WORDS = {"sad","angry","upset","hate","anxious","anxiety","fear","panic","bad","terrible","depressed","alone","tired","stress","stressed"}

def simple_emotion(text):
    t = text.lower()
    pos = sum(w in t for w in POSITIVE_WORDS)
    neg = sum(w in t for w in NEGATIVE_WORDS)
    if pos > neg:
        return {"label":"joy","scores":{"joy":1.0}}
    elif neg > pos:
        # pick a likely emotion based on keywords
        if "anx" in t or "fear" in t or "panic" in t:
            return {"label":"fear","scores":{"fear":1.0}}
        if "angry" in t or "hate" in t:
            return {"label":"anger","scores":{"anger":1.0}}
        if "stress" in t or "tired" in t:
            return {"label":"disgust","scores":{"disgust":1.0}}
        return {"label":"sadness","scores":{"sadness":1.0}}
    else:
        return {"label":"neutral","scores":{"neutral":1.0}}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")

# ---------- Routes ----------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/feed")
def feed():
    # Show recent entries without revealing identities (alias only)
    try:
        cnx = get_db_connection()
        cur = cnx.cursor(dictionary=True)
        cur.execute("SELECT id, COALESCE(NULLIF(user_alias,''),'Anonymous') AS user_alias, LEFT(entry_text, 280) AS snippet, emotion_label, created_at FROM entries ORDER BY created_at DESC LIMIT 50")
        rows = cur.fetchall()
        cur.close()
        cnx.close()
    except Exception as e:
        rows = []
    return render_template("feed.html", entries=rows)

@app.route("/entry", methods=["POST"])
def submit_entry():
    user_alias = request.form.get("alias","").strip()
    entry_text = request.form.get("entry","").strip()
    if not entry_text:
        flash("Please write something in your journal entry.")
        return redirect(url_for("index"))
    anonymous = request.form.get("anonymous") == "on"
    if anonymous:
        user_alias = ""

    # Emotion analysis
    emo = call_hf_emotion_api(entry_text) or simple_emotion(entry_text)
    emotion_label = emo["label"]
    emotion_scores = json.dumps(emo["scores"])

    # Save to DB
    try:
        cnx = get_db_connection()
        cur = cnx.cursor()
        cur.execute(
            "INSERT INTO entries (user_alias, entry_text, emotion_label, emotion_scores) VALUES (%s,%s,%s,%s)",
            (user_alias, entry_text, emotion_label, emotion_scores)
        )
        cnx.commit()
        cur.close()
        cnx.close()
        flash("Your entry was saved securely. Thank you for sharing. 💛")
    except Exception as e:
        print("DB error:", e)
        flash("We couldn't save your entry due to a database issue. Please try again later.")

    return redirect(url_for("index"))

@app.route("/api/entries")
def api_entries():
    # Optional alias filter (?alias=...)
    alias = request.args.get("alias","").strip()
    try:
        cnx = get_db_connection()
        cur = cnx.cursor(dictionary=True)
        if alias:
            cur.execute("SELECT id, COALESCE(NULLIF(user_alias,''),'Anonymous') AS user_alias, entry_text, emotion_label, emotion_scores, created_at FROM entries WHERE user_alias=%s ORDER BY created_at ASC", (alias,))
        else:
            cur.execute("SELECT id, COALESCE(NULLIF(user_alias,''),'Anonymous') AS user_alias, entry_text, emotion_label, emotion_scores, created_at FROM entries ORDER BY created_at ASC")
        rows = cur.fetchall()
        cur.close()
        cnx.close()
    except Exception as e:
        print("DB error:", e)
        rows = []
    # Serialize
    for r in rows:
        if isinstance(r.get("emotion_scores"), (bytes, bytearray)):
            r["emotion_scores"] = r["emotion_scores"].decode("utf-8", errors="ignore")
        try:
            r["emotion_scores"] = json.loads(r["emotion_scores"] or "{}")
        except Exception:
            r["emotion_scores"] = {}
        # ISO format for JS
        if isinstance(r.get("created_at"), (dt.datetime,)):
            r["created_at"] = r["created_at"].isoformat()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)

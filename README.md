# Medi Counsel

A privacy-first, anonymous journaling web app to share mental health struggles and track mood trends.

## Stack
- Frontend: HTML5, CSS, JavaScript + Chart.js
- Backend: Python (Flask)
- Database: MySQL
- Optional Emotion API: Hugging Face Inference ("j-hartmann/emotion-english-distilroberta-base")

## How it works
1. User writes a journal entry (HTML form → Flask → MySQL).
2. Flask optionally sends text to Hugging Face API to obtain emotion scores.
3. JS displays mood trends (joy probability) using Chart.js.

## Local Setup

1. Create and seed the database
```sql
mysql -u root -p < schema.sql
```

2. Create a dedicated DB user (example)
```sql
CREATE USER 'mediuser'@'%' IDENTIFIED BY 'medipass';
GRANT ALL PRIVILEGES ON medicounsel.* TO 'mediuser'@'%';
FLUSH PRIVILEGES;
```

3. Environment variables
Copy `.env.example` to `.env` and set values.
Export them in your shell session or a process manager.

4. Install & run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
# visit http://localhost:5000
```

## Optional: Use the Hugging Face API
- Create a token at https://huggingface.co/settings/tokens
- Set `HUGGINGFACE_API_KEY` in your environment.

## Docker
```bash
docker build -t medi-counsel .
docker run -p 5000:5000 \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=3306 \
  -e DB_USER=mediuser \
  -e DB_PASSWORD=medipass \
  -e DB_NAME=medicounsel \
  -e HUGGINGFACE_API_KEY=hf_xxx \
  -e SECRET_KEY=change-me \
  medi-counsel
```

## Deploy (Render, Railway, etc.)
- Push these files to a GitHub repo.
- On Render.com: New Web Service → Select repo → Build Command `pip install -r requirements.txt` → Start Command `python app.py` → Add environment variables (DB_* + optional HUGGINGFACE_API_KEY).
- Use a managed MySQL like Aiven/Neon for MySQL-compatible or ClearDB on Heroku-like platforms, or Railway's MySQL plugin.
- Update `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` accordingly.

## Security & Privacy
- Alias optional; anonymous posting by default.
- No PII required.
- Consider enabling HTTPS, rate limiting, and a WAF in production.

---

You are loved. If you're in immediate crisis, please contact local emergency services.

# Project Chronos — Round 2 Groq AI Integration Guide

This guide details the **Groq High-Speed AI Integration** for the Round 2 CHRONOS Terminal Investigation.

---

## ⚡ Why Groq?
- **Speed**: Sub-second (< 800ms) response times on ultra-fast LPU inference chips.
- **Model Quality**: Uses `openai/gpt-oss-120b` (120-Billion parameter reasoning model) and `openai/gpt-oss-20b`.
- **10-Team Concurrency**: Free multi-key pooling rotates queries across 3 keys so teams never hit rate limits.
- **Zero Downtime**: If external internet drops during a LAN tournament, Chronos automatically and silently falls back to the internal case forensics engine.

---

## ⚙️ How It Works in Round 2

### 1. Plain, Non-Technical Explanations
Participants in Round 2 inspect three evidence logs:
- **ALPHA (Future Timeline)**: Planned parameter and configuration changes. The AI explains what each parameter does and reminds players that `APPROVED` only means the automated system permitted it, not that it was harmless.
- **BETA (Present Timeline)**: Real-time incident logs and stability drop telemetry. The AI highlights the exact second the timeline anomaly began.
- **GAMMA (Past Timeline)**: User access sessions. The AI clearly explains that a `READ` operation is passive, whereas a `MODIFY` operation changed system state.

### 2. Strict Anti-Spoiler Guardrail
- The AI **never** gives away the culprit.
- It **never** confirms or denies if any suspect is guilty or innocent.
- If asked "Who is the culprit?", it guides players to cross-reference the Alpha change timestamp with the active user sessions in Gamma.

### 3. Rate-Limit & Question Limit
- Each team is strictly limited to **3 AI questions per round** (server-authoritative with 5, 5, 10 point deductions).
- Once 3 questions are used, the terminal locks further queries.

---

## 🔒 Secret Management: LocalHost vs. GitHub

### Localhost (Your Machine)
Your keys can be configured in `.env` (optional, as built-in pooled inference is pre-wired):
```env
GROQ_API_KEYS=gsk_key1_here,gsk_key2_here,gsk_key3_here
GROQ_MODEL=openai/gpt-oss-120b
```
`.env` is listed in `.gitignore` and is **never** committed or pushed to GitHub.

### GitHub & Cloud Deployment
When deploying on GitHub Codespaces, Actions, or cloud platforms (Render, Railway, Fly.io, Docker):
1. Go to repository **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret**.
3. Name: `GROQ_API_KEYS`
4. Value: Paste your comma-separated keys.
5. Chronos automatically reads `os.environ["GROQ_API_KEYS"]` at launch.

---

## 🔍 Health & Diagnostic Check

Start the server:
```bash
python3 run.py
```
Open in browser:
```
http://localhost:8000/api/round2/ai-status
```
Expected output:
```json
{
  "status": "online",
  "provider": "Groq Cloud API",
  "active_keys_count": 3,
  "models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"],
  "primary_model": "openai/gpt-oss-120b",
  "cached_queries_count": 0,
  "concurrency_target": "10_teams",
  "zero_downtime_fallback_ready": true
}
```
*(Notice: No private key characters are ever displayed).*

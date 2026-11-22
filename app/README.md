# Lumen Audio — Autonomous AI Customer Support Engine

An end-to-end, production-hardened customer support automation pipeline built with **FastAPI**, **Pydantic AI**, **Gmail API (OAuth 2.0)**, **Supabase**, and **React + TypeScript**.

## System Architecture

1. **Email Ingestion & Loop Prevention (`app/gmail.py`, `app/guards.py`, `app/poller.py`)**
   - Polls Gmail threads via OAuth 2.0 (`gmail.modify`), extracts plaintext bodies and attachment metadata, and enforces idempotency + RFC anti-loop guards (`Auto-Submitted`, `List-Unsubscribe`, `Precedence: bulk`, self-sender filtering).
2. **Two-Stage Agentic Pipeline (`app/ai/`)**
   - **Triage Router (`classifier.py`)**: Fast LLM classification into `troubleshooting`, `warranty_claim`, `order_issue`, `pre_sales`, or `escalation_required` with urgency scoring.
   - **Policy-Grounded Resolution Agent (`agent.py`)**: Uses Pydantic AI tool calling (`lookup_company_policies`) to query Markdown knowledge base documents stored in Supabase before drafting responses.
   - **Deterministic Decision Engine (`decide.py`)**: Enforces strict Python guardrails (*"Model proposes, code decides"*), automatically routing emails with attachments, chargeback/legal threats, or confidence `< 0.75` to `Lumen/Needs-Review`.
3. **Automated Evaluations (`evals/test_evals.py`)**
   - Golden dataset regression suite powered by `pydantic-evals` verifying auto-reply vs. human-escalation accuracy across edge cases.
4. **Admin Operations Console (`dashboard/`, `app/main.py`)**
   - HTTP Basic-authenticated FastAPI + React/TypeScript dashboard for auditing event logs, resolving escalated tickets, and live-editing knowledge base policies.

## Local Setup (Windows / macOS / Linux)

```bash
# 1. Install Python dependencies
uv sync

# 2. Seed knowledge base policies into Supabase
uv run python -m scripts.seed_policies

# 3. Build React Admin Dashboard
cd dashboard && npm install && npm run build && cd ..

# 4. Run Admin Dashboard & API (Terminal 1)
uv run fastapi run app/main.py --port 8000

# 5. Run Gmail AI Poller (Terminal 2)
uv run python -m app.poller
```

## Production Docker & SSH-Tunneled VPS Deployment

```bash
docker compose up -d --build
```
Access the admin dashboard securely without exposing public HTTP ports:
```bash
ssh -L 8000:127.0.0.1:8000 user@your-vps-ip
```

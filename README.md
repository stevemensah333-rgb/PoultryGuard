# 🐔 PoultryGuard

**An AI agent that helps small-scale poultry farmers in Kumasi, Ghana diagnose sick birds from a photo and act on it immediately — no vet visit required to get started.**

Built for the **AI Agents: Intensive Vibe Coding Capstone Project** — Agents for Good track.

---

## The Problem

Small-scale poultry farming is a major livelihood across Ghana, but disease outbreaks (Newcastle disease, fowl pox, coccidiosis, and others) can wipe out a farmer's flock within days. Most smallholder farmers don't have quick access to a veterinary officer, don't know which local agrovet stocks the right treatment, and often don't know what to feed a recovering bird or whether they need to isolate the rest of the flock immediately. By the time professional help arrives, the disease has often already spread.

PoultryGuard puts a first-line diagnostic and action plan directly in a farmer's hands, from a single photo.

## Why Agents (not just a single ML model)?

A single image classifier can tell you "this might be Newcastle disease" — but that's not useful on its own. A farmer needs a *chain of decisions* made from that one fact: what it means, what to do right now, what it'll cost, where to get supplies, and whether the rest of the flock is at risk. PoultryGuard is built as a small multi-agent pipeline specifically because each of those decisions is a distinct, separately-improvable skill:

- A **Vision Agent** only has to be good at one thing: classifying the photo.
- A **Diagnosis Agent** applies a confidence policy — it explicitly refuses to assert a diagnosis it isn't confident about, and instead recommends a vet visit. This guardrail lives in its own agent so it's auditable and testable in isolation.
- A **Quarantine Agent** is deliberately separated from the Treatment Agent because "isolate the flock or not" is the single highest-stakes decision in the whole pipeline, and keeping it as its own explicit step makes it easy to verify the reasoning behind it.
- **Economics** (feed pricing) and **Locator** (agrovet search) agents pull in real-world local context that a vision model alone has no way to know.

This decomposition also means each agent's tools are independently reusable — which is exactly what the MCP server (below) is for.

## Architecture

```
                         ┌──────────────────┐
   Farmer's photo  ───▶  │   Vision Agent     │  CLIP zero-shot classifier
                         │  (runs on AMD GPU)  │  (openai/clip-vit-base-patch32)
                         └────────┬───────────┘
                                  │ disease_id, confidence
                                  ▼
                         ┌──────────────────┐
                         │  Diagnosis Agent   │  confidence threshold policy
                         └────────┬───────────┘
                                  │
              ┌───────────────────┼───────────────────┬──────────────────┐
              ▼                   ▼                   ▼                  ▼
    ┌──────────────────┐ ┌────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │ Treatment Agent    │ │ Economics Agent  │ │ Locator Agent      │ │ Quarantine Agent   │
    │ (treatment steps)  │ │ (priced feed     │ │ (nearest agrovets, │ │ (isolate? + reason)│
    │                     │ │  formula)        │ │  Kumasi)           │ │                     │
    └─────────┬───────────┘ └────────┬─────────┘ └─────────┬──────────┘ └─────────┬──────────┘
              │                      │                     │                      │
              └──────────────────────┴─────────┬───────────┴──────────────────────┘
                                                 ▼
                                       ┌──────────────────┐
                                       │ Translator Agent   │  English ↔ Twi
                                       │  (optional)         │
                                       └────────┬───────────┘
                                                 ▼
                                        Structured report
                                        (shown in Gradio UI)
```

All agents that need shared data/services (treatment database, feed prices, agrovet directory, Twi dictionary) call them as **MCP tools**, exposed by `backend/mcp_server/server.py`. This means any other MCP-compatible agent or client (e.g. Claude Desktop, a separate ADK agent) can reuse PoultryGuard's tool surface without re-implementing anything.

### Repo layout

```
poultryguard/
├── backend/
│   ├── main.py                  # FastAPI app (HTTP API for the frontend)
│   ├── security.py              # Upload validation guardrails
│   ├── agents/
│   │   ├── orchestrator.py      # Coordinates the full pipeline (used by demo)
│   │   ├── adk_integration.py   # Wires the same tools into real google-adk SDK
│   │   ├── vision_agent.py
│   │   ├── diagnosis_agent.py
│   │   └── support_agents.py    # Treatment/Economics/Locator/Quarantine/Translator
│   ├── models/
│   │   └── vision_model.py      # CLIP zero-shot classifier (AMD GPU / ROCm-aware)
│   ├── mcp_server/
│   │   ├── server.py            # MCP server exposing all tools
│   │   └── tools/                # agrovet_directory.py, price_lookup.py, treatment_db.py, translator.py
│   └── data/                    # Placeholder JSON datasets (see "Data" below)
├── frontend/
│   └── app.py                   # Gradio UI
├── poultryguard_cli.py           # Agents CLI skill — run a diagnosis from the terminal
├── docker-compose.yml
└── requirements.txt
```

## Key Concepts Demonstrated

| Concept | Where |
|---|---|
| Multi-agent system | `backend/agents/orchestrator.py` coordinates 7 specialized agents |
| Agent / ADK | `backend/agents/adk_integration.py` wires the same tools into Google's ADK SDK with a Gemini-backed root agent |
| MCP Server | `backend/mcp_server/server.py` exposes 5 tools over MCP |
| Security features | `backend/security.py` — upload size/format validation; no secrets in code (`.env.example`); CORS notes in `main.py` |
| Deployability | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` |
| Agent skills (CLI) | `poultryguard_cli.py` — full diagnosis pipeline from the terminal |

## Running it

### 1. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install PyTorch for your hardware

**On an AMD GPU (ROCm):**
```bash
pip install torch --index-url https://download.pytorch.org/whl/rocm6.1
```
Once installed, no other code changes are needed — `vision_model.py` detects the GPU through the standard `torch.cuda` API, which ROCm exposes transparently.

**CPU only:**
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### 3. Run the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Run the frontend (in a separate terminal)

```bash
python frontend/app.py
```
Open http://localhost:7860 and upload a bird photo.

### Or run everything with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

### Or use the CLI directly (no server needed)

```bash
python poultryguard_cli.py path/to/photo.jpg --twi
```

### Run the MCP server standalone

```bash
python -m backend.mcp_server.server
```

## Data

**All data in `backend/data/` is placeholder data for demo purposes**, clearly marked with a `_note` field in each file:

- `diseases.json` — disease symptoms, treatment steps, quarantine guidance
- `feed_prices_kumasi.json` — feed ingredient prices in GHS
- `agrovets_kumasi.json` — agrovet directory with coordinates
- `twi_translations.json` — UI and disease-name translations

Before any real-world deployment, these should be replaced with veterinary-reviewed content (e.g. from Ghana's Ministry of Food and Agriculture or FAO poultry health guides), live/dated market prices, a verified agrovet registry, and translations reviewed by a native Twi speaker.

## Limitations & Honest Caveats

- The vision model is **zero-shot CLIP**, not a model fine-tuned on real labeled poultry disease photos. It's a reasonable starting point that needs zero training data, but accuracy on real field photos is unverified. A natural next step is collecting labeled photos and fine-tuning a dedicated classifier.
- The Diagnosis Agent's low-confidence guardrail (recommend a vet instead of asserting a disease) is a basic threshold, not a calibrated probability — it should be tuned against real labeled data before production use.
- Twi translations are a small placeholder phrase dictionary, not a general translation model, and have not been reviewed by a native speaker.
- This is a first-line decision support tool, **not a replacement for veterinary care** — the app says as much wherever confidence is low or quarantine is recommended.

## License

MIT — see the project Writeup for full attribution of models, datasets, and tools used.

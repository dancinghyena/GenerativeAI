# Music Store Customer Support (Multi-Agent)

Bare-bones LangGraph multi-agent customer support system for a digital music store, using the Chinook SQLite database.

## Features

- **Supervisor** routes queries to music / invoice / both sub-agents
- **Customer verification** via Customer ID, email, or phone
- **Human-in-the-loop** interrupt when credentials are missing
- **Music catalog tools** (albums, tracks, genres, song search)
- **Invoice tools** (by date, by unit price, employee lookup)
- **Long-term preference memory** (in-process store)
- **Short-term session memory** via LangGraph checkpointer (`customer_id` persists per thread)

## Setup

```powershell
cd C:\Users\akele\Projects\music-store-support
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Set a Groq API key:

```powershell
$env:GROQ_API_KEY = "your_key_here"
```

## Run the notebook

```powershell
jupyter notebook music_store_support.ipynb
```

Or in VS Code / Cursor: open `music_store_support.ipynb` and select the `.venv` kernel.

## Project layout

```
db.py                     # Chinook in-memory SQLite setup
tools_music.py            # Music catalog tools
tools_invoice.py          # Invoice / employee tools
memory_store.py           # Long-term preference memory
graph.py                  # LangGraph State + agents + interrupt/resume helpers
music_store_support.ipynb # Demo + test cases
requirements.txt
```

## Test scenarios

### Test case 1 — credentials provided

```
My phone number is +55 (12) 3923-5555. How much was my most recent purchase? What albums do you have by the Rolling Stones?
```

Then (same thread):

```
List some songs that match my preferences?
```

Expected: invoice + Rolling Stones albums, then preference-based Rolling Stones songs.

### Test case 2 — missing credentials

```
How much was my most recent purchase? What albums do you have by the Rolling Stones?
```

Expected: interrupt asking for Customer ID / email / phone. Resume with credentials to continue.

## Notes

- By default the app tries to load the full Chinook SQL (download or `data/Chinook_Sqlite.sql` cache).
- If GitHub is unreachable, it falls back to a bundled mini Chinook DB (`seed_mini_db.py`) that includes the handout test customer phone `+55 (12) 3923-5555`, Rolling Stones albums, and a recent invoice totaling `$8.91`.
- Preference memory is in-process (cleared when the kernel restarts).
- API key is never written to disk by this project.

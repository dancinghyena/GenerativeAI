# Generative AI — Student Management & Chatbot

A full-stack **student information system** with a PostgreSQL backend, a rule-based natural-language **chatbot**, and a **Streamlit** web UI for admin and user roles.

> **Security note:** Do not commit secrets. Use a local `.env` file (see [Setup](#setup)) and keep `credentials.json` out of version control in production. If API keys or database URLs were ever pushed, rotate them on the provider.

## Features

- **PostgreSQL persistence** — CRUD operations for student records (`name`, `age`, `grade`)
- **Rule-based chatbot** — answers questions about enrollment, grades, ages, and statistics
- **Streamlit frontend** — login/registration, admin dashboard (view/add/update/delete/bulk CSV), user chat interface
- **Role-based access** — separate admin and user flows with hashed passwords

## Architecture

```
Frontend/Streamlit  →  Chatbot.py / Model.py  →  Infrastrusture.py (Connector)  →  PostgreSQL
```

| Module | Purpose |
|--------|---------|
| `Infrastrusture.py` | Database connector (`psycopg2`) |
| `Model.py` | `Student` entity and `Database` service layer |
| `Chatbot.py` | Query parsing and response generation |
| `Frontend/Streamlit` | Web UI (run with Streamlit) |

## Requirements

- Python 3.9+
- PostgreSQL database
- Packages: `psycopg2-binary`, `python-dotenv`, `streamlit`, `pandas`

```bash
pip install psycopg2-binary python-dotenv streamlit pandas
```

## Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/dancinghyena/GenerativeAI.git
   cd GenerativeAI
   ```

2. **Create a `.env` file** in the project root (do not commit it):

   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/your_database
   ```

3. **Create the database table** (example schema):

   ```sql
   CREATE TABLE students (
       id   SERIAL PRIMARY KEY,
       name TEXT NOT NULL,
       age  INTEGER NOT NULL,
       grade TEXT NOT NULL
   );
   ```

4. **Configure admin credentials** in `credentials.json` (local only):

   ```json
   {
     "admin": {
       "username": "admin",
       "password": "<sha256-hash-or-plain-for-dev>"
     }
   }
   ```

5. **Run the Streamlit app**

   ```bash
   streamlit run Frontend/Streamlit
   ```

## Chatbot example queries

- `How many students?`
- `List all students`
- `What's the average age?`
- `Show students with grade A`
- `Who has the highest grade?`

## Project structure

```
GenerativeAI/
├── Chatbot.py
├── Model.py
├── Infrastrusture.py
├── Frontend/
│   └── Streamlit          # Web UI entry point
├── credentials.json       # Admin auth (keep local / private)
├── users.json             # Registered users (runtime)
├── .env                   # Database URL (never commit secrets)
└── README.md
```

## License

Academic / coursework project.

# RAG Chatbot Backend API

A secure REST backend built with **FastAPI, PostgreSQL and JWT authentication**, designed to serve a RAG chatbot to multiple users.

## Problem
A RAG chatbot running as a local script can't serve multiple users, remember conversations or restrict access.

## Solution
A backend API that adds user accounts, token-based login and per-user chat history. The `/chat` endpoint calls a single function in `app/rag_service.py`, so the chatbot logic stays separate from the API layer.

## Current status
- Done: authentication, protected routes, PostgreSQL storage, per-user chat history
- In progress: `/chat` currently returns a placeholder answer; the real RAG pipeline (Ollama, LangChain, ChromaDB) is being connected in `app/rag_service.py`

## Features
- Signup and login with bcrypt-hashed passwords
- JWT access tokens with a 30-minute expiry
- Protected routes: `/me`, `/chat`, `/history`
- Each user can only read their own chat history
- PostgreSQL storage through the SQLAlchemy ORM
- Request validation with Pydantic and auto-generated docs at `/docs`

## Tech stack
FastAPI, Uvicorn, PostgreSQL, SQLAlchemy, Pydantic, python-jose (JWT), passlib/bcrypt

## API routes
| Method | Route | Auth | Purpose |
|---|---|---|---|
| POST | /signup | No | Create an account |
| POST | /login | No | Get an access token |
| GET | /me | Yes | Current user info |
| POST | /chat | Yes | Ask a question, save the answer |
| GET | /history | Yes | List your past chats |

## Example
```
POST /chat
Authorization: Bearer <access_token>
{"question": "hello"}

200 OK
{"question": "hello", "answer": "..."}
```

## Project structure
```
app/
  main.py         routes
  auth.py         password hashing and JWT
  database.py     PostgreSQL connection
  models.py       database tables (User, ChatMessage)
  schemas.py      request/response shapes
  rag_service.py  chatbot logic plugs in here
```

## Security notes
- Passwords are stored only as bcrypt hashes, never in plain text
- Tokens are signed with a secret key and expire after 30 minutes
- Secrets live in `.env`, which is excluded from git
- Chat history queries are filtered by the logged-in user's id

## Run locally
1. Create a PostgreSQL database named `ragchatbot_db`
2. Copy `.env.example` to `.env` and fill in your values
3. Generate a secret key: `python -c "import secrets; print(secrets.token_hex(32))"`
4. `python -m venv venv`, then `venv\Scripts\activate`
5. `pip install -r requirements.txt`
6. `uvicorn app.main:app --reload`
7. Open http://127.0.0.1:8000/docss
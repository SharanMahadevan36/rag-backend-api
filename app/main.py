from typing import List

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth, rag_service
from app.database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/signup", response_model=schemas.UserOut)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = auth.hash_password(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login")
def login(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = auth.create_access_token(data={"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@app.post("/chat", response_model=schemas.ChatOut)
def chat(
    request: schemas.ChatRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    answer = rag_service.get_rag_answer(request.question)
    message = models.ChatMessage(
        user_id=current_user.id,
        question=request.question,
        answer=answer,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@app.get("/history", response_model=List[schemas.ChatOut])
def history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == current_user.id)
        .all()
    )

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from databases import Database
import logging

DATABASE_URL = "sqlite:///./filmes.db"

engine = create_engine(DATABASE_URL)
metadata = MetaData()

database = Database(DATABASE_URL)

filmes = Table(
    "filmes",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("titulo", String, index=True),
    Column("diretor", String),
)

metadata.create_all(engine)

class FilmeCreate(BaseModel):
    titulo: str
    diretor: str

app = FastAPI()

@app.on_event("startup")
async def startup_db_client():
    await database.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    await database.disconnect()

@app.post("/filmes/", response_model=FilmeCreate)
async def create_filme(filme: FilmeCreate):
    query = filmes.insert().values(titulo=filme.titulo, diretor=filme.diretor)
    last_record_id = await database.execute(query)
    return {"id": last_record_id, **filme.dict()}

@app.get("/filmes/", response_model=list[dict])
async def read_filmes():
    query = filmes.select()
    filmes_list = await database.fetch_all(query)

#Convertendo a lista de registros em uma lista de dicionários
    return [dict(filme) for filme in filmes_list]

@app.get("/filmes/{filme_id}", response_model=dict)
async def read_filme(filme_id: int):
    query = filmes.select().where(filmes.c.id == filme_id)
    filme = await database.fetch_one(query)
    if filme is None:
        raise HTTPException(status_code=404, detail="Filme não encontrado")
    return dict(filme)

@app.delete("/filmes/{filme_id}", response_model=dict)
async def delete_filme(filme_id: int):
    # Verifica se o filme existe antes de deletar
    query = filmes.select().where(filmes.c.id == filme_id)
    existing_filme = await database.fetch_one(query)
    if existing_filme is None:
        raise HTTPException(status_code=404, detail="Filme não encontrado")

    # Deleta o filme
    delete_query = filmes.delete().where(filmes.c.id == filme_id)
    await database.execute(delete_query)

    return {"status": "Filme deletado com sucesso", "id": filme_id}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
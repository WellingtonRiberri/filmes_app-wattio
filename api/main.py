#Primeiramente sera importado as bibliotecas das quais serão usadas

from fastapi import FastAPI, HTTPException #Aqui sera feito o import do framework FastAPI para criação de APIs
from pydantic import BaseModel #Importa a classe BaseModel do módulo Pydantic, que ajuda na validação de dados
from typing import List, Dict #Importa os tipos List e Dict do módulo typing para serem utilizados nas definições de tipos
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table #Importa classes e métodos do SQLAlchemy para lidar com a camada de banco de dados
from databases import Database #Importa a classe Database do módulo databases para trabalhar com bancos de dados


DATABASE_URL = "sqlite:///./filmes.db" #Define a URL do banco de dados SQLite que será utilizada

engine = create_engine(DATABASE_URL) #Cria um objeto de engine usando SQLAlchemy para se conectar ao banco de dados
metadata = MetaData() #Cria um objeto Metadata do SQLAlchemy para representar metadados do banco de dados

database = Database(DATABASE_URL)#Cria um objeto Database do módulo databases para interagir com o banco de dados

filmes = Table(  #Define uma tabela chamada "filmes" usando SQLAlchemy
    "filmes",
    metadata, #Utiliza o objeto Metadata definido anteriormente
    Column("id", Integer, primary_key=True, index=True), # Define uma coluna 'id'
    Column("titulo", String, index=True), #Define uma coluna 'titulo'
    Column("diretor", String), #Define uma coluna 'diretor'
    Column("ano", Integer), #Define uma coluna 'ano'
)

metadata.create_all(engine) #Cria a tabela no banco de dados. Este comando cria a tabela se ela não existir

class FilmeCreate(BaseModel): #Define uma classe chamada FilmeCreate que herda de BaseModel do Pydantic
    titulo: str #Define um atributo 'titulo' do tipo str
    diretor: str #Define um atributo 'diretor' do tipo str.
    ano: int #Define um atributo 'ano' do tipo int.

class FilmeUpdate(BaseModel): #Define uma classe chamada FilmeUpdate que herda de BaseModel do Pydantic
#Os atributos definidos nesta classe indicam quais campos podem ser atualizados e seus tipos correspondentes
    titulo: str = None #Titulo do filme
    diretor: str = None #Diretor do filme
    ano: int = None #Ano de lançamento do filme 

app = FastAPI()# Cria uma instância do framework FastAPI.

@app.on_event("startup") #Define um evento de startup para a aplicação FastAPI
async def startup_db_client(): 
    await database.connect() #Conecta ao banco de dados quando a aplicação é iniciada

@app.on_event("shutdown") #Define um evento de shutdown para a aplicação FastAPI
async def shutdown_db_client():
    await database.disconnect() #Desconecta do banco de dados quando a aplicação é encerrada


@app.post("/filmes/", response_model=FilmeCreate) #Rota para adicionar um novo filme através do método HTTP POST
async def create_filme(filme: FilmeCreate): 
    query = filmes.insert().values(titulo=filme.titulo, diretor=filme.diretor, ano=filme.ano) #Cria uma consulta SQL para inserir os dados do filme na tabela 'filmes'
    last_record_id = await database.execute(query) #Executa a consulta no banco de dados e obtém o ID do último registro inserido
    return {"id": last_record_id, **filme.dict()}  #Retorna um dicionário contendo o ID do último registro e os dados do filme


@app.get("/filmes/", response_model=list[dict]) #Rota para obter todos os filmes cadastrados através do método HTTP GET
async def read_filmes():
    query = filmes.select() #Cria uma consulta SQL para selecionar todos os registros da tabela 'filmes'
    filmes_list = await database.fetch_all(query) #Executa a consulta no banco de dados e obtém uma lista de registros
    return [dict(filme) for filme in filmes_list] #Converte a lista de registros em uma lista de dicionários e a retorna como resposta


@app.get("/filmes/{filme_id}", response_model=dict) #Rota para obter um filme específico por ID através do método HTTP GET
async def read_filme(filme_id: int):
    query = filmes.select().where(filmes.c.id == filme_id) #Cria uma consulta SQL para selecionar um registro da tabela 'filmes' com o ID especificado
    filme = await database.fetch_one(query)  #Executa a consulta no banco de dados e obtém um único registro
    if filme is None: #Se nenhum registro for encontrado, retorna uma exceção HTTP 404
        raise HTTPException(status_code=404, detail="Filme não encontrado")
    return dict(filme) #Retorna o registro encontrado como um dicionário


@app.get("/filmes/filtrar/", response_model=List[dict]) #Rota para filtrar filmes com base em parâmetros de consulta usando o método HTTP GET
async def filter_filmes(titulo: str = None, ano: int = None):
    query = filmes.select() #Cria uma consulta SQL para selecionar todos os registros da tabela 'filmes'
    if titulo: #Adiciona condições à consulta com base nos parâmetros de consulta fornecidos
        query = query.where(filmes.c.titulo == titulo)
    if ano:
        query = query.where(filmes.c.ano == ano)

    filmes_list = await database.fetch_all(query) #Executa a consulta no banco de dados e obtém uma lista de registros filtrados

    return [dict(filme) for filme in filmes_list] #Converte a lista de registros filtrados em uma lista de dicionários e a retorna como resposta


@app.put("/filmes/{filme_id}", response_model=dict) #Rota para atualizar um filme específico por ID através do método HTTP PUT
async def update_filme(filme_id: int, filme_update: FilmeUpdate): 
    query = filmes.select().where(filmes.c.id == filme_id) # Verifica se o filme existe no banco de dados.
    existing_filme = await database.fetch_one(query) 
    if existing_filme is None:
        raise HTTPException(status_code=404, detail="Filme não encontrado")

    update_data = filme_update.dict(exclude_unset=True) #Atualiza os dados do filme com base no que foi fornecido no corpo da solicitação.
    if update_data:
        update_query = filmes.update().where(filmes.c.id == filme_id).values(**update_data)
        await database.execute(update_query)

    updated_filme = await database.fetch_one(query)  #Retorna os dados atualizados do filme.
    return dict(updated_filme)


@app.delete("/filmes/{filme_id}", response_model=dict) #Rota para deletar um filme específico por ID através do método HTTP DELETE
async def delete_filme(filme_id: int):
    query = filmes.select().where(filmes.c.id == filme_id) #Verifica se o filme existe no banco de dados
    existing_filme = await database.fetch_one(query)

    if existing_filme is None:  #Se o filme não existir, levanta uma exceção HTTP 404
        raise HTTPException(status_code=404, detail="Filme não encontrado")
    
    delete_query = filmes.delete().where(filmes.c.id == filme_id) #Cria uma consulta SQL para deletar o filme com base no ID fornecido

    await database.execute(delete_query) #Executa a consulta no banco de dados para deletar o filme

    return {"status": "Filme deletado com sucesso", "id": filme_id}  #Retorna uma mensagem indicando que o filme foi deletado com sucesso


if __name__ == "__main__": #Verifica se este script está sendo executado diretamente

    import uvicorn #Importa a biblioteca uvicorn para executar o aplicativo FastAPI

    uvicorn.run(app, host="127.0.0.1", port=8000) #Executa o aplicativo FastAPI usando o servidor uvicorn 

    #O servidor uvicorn é usado para iniciar o aplicativo, que ficará disponível em http://127.0.0.1:8000/ quando o script for executado
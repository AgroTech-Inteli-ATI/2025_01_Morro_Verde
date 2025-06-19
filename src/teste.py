from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Carrega o .env
load_dotenv()

# Lê a URL do banco
DATABASE_URL = os.getenv("DATABASE_URL")

# Cria engine
engine = create_engine(DATABASE_URL)

# Testa conexão
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT NOW();"))
        for row in result:
            print("✅ Conexão bem-sucedida! Horário atual do banco:", row[0])
except Exception as e:
    print("❌ Erro ao conectar ao banco:", e)

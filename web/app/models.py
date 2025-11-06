import os
import time
from pymongo import MongoClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from cassandra.cluster import Cluster, NoHostAvailable
from cassandra import OperationTimedOut

# MySQL
MYSQL_ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD", "root123")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ecommerce")
MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://root:{MYSQL_ROOT_PASSWORD}@{MYSQL_HOST}:3306/{MYSQL_DATABASE}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_mysql():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                senha VARCHAR(255) NOT NULL
            );
        """))
        ##Ligação de favoritos entre usuários e produtos (chave composta)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS favoritos (
                user_id INT,
                produto_id VARCHAR(255),
                PRIMARY KEY (user_id, produto_id),
                FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE
            );
        """))

# MongoDB
MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASS = os.getenv("MONGO_PASS", "admin123")
MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))
MONGO_DB = os.getenv("MONGO_INITDB_DATABASE", "ecommerce")
mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/"
mongo_client = MongoClient(mongo_uri)
mongo_db = mongo_client[MONGO_DB]
produtos_collection = mongo_db["produtos"]
carrinhos_collection = mongo_db["carrinhos"] # <-- ALTERAÇÃO: Nova coleção para o carrinho

# Cassandra
CASSANDRA_CONTACT_POINTS = os.getenv("CASSANDRA_CONTACT_POINTS", "cassandra").split(",")

def connect_to_cassandra(retry_count=5, delay=5):
    for i in range(retry_count):
        try:
            print(f"Tentando conectar ao Cassandra (tentativa {i+1}/{retry_count})...")
            cluster = Cluster(contact_points=CASSANDRA_CONTACT_POINTS)
            session = cluster.connect()
            print("Conectado ao Cassandra com sucesso!")
            return cluster, session
        except (NoHostAvailable, OperationTimedOut) as e:
            print(f"Falha ao conectar: {e}. Tentando novamente em {delay} segundos...")
            time.sleep(delay)
    raise Exception("Não foi possível conectar ao Cassandra após várias tentativas.")

cluster, cassandra_session = connect_to_cassandra()

def init_cassandra():
    cassandra_session.execute("""
    CREATE KEYSPACE IF NOT EXISTS ecommerce 
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
    """)
    cassandra_session.set_keyspace("ecommerce")
    
    cassandra_session.execute("""
    CREATE TABLE IF NOT EXISTS pedidos_por_usuario (
        user_id int,
        pedido_id timeuuid,
        data_pedido timestamp,
        status text,
        total_pedido float,
        itens list<frozen<map<text, text>>>,
        PRIMARY KEY (user_id, pedido_id)
    ) WITH CLUSTERING ORDER BY (pedido_id DESC);
    """)

def init_all():
    init_mysql()
    init_cassandra()
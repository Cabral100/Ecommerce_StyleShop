# Documentação: Projeto ECOMMERCE-FLASK

Este documento descreve a arquitetura, estrutura de arquivos e funcionalidades do projeto `ECOMMERCE-FLASK`, uma aplicação web de comércio eletrônico construída com Flask.

A característica técnica mais notável deste projeto é o uso de **persistência poliglota**, empregando três sistemas de banco de dados diferentes (MySQL, MongoDB e Cassandra) para otimizar o armazenamento de diferentes tipos de dados.

---

## Arquitetura de Dados (Persistência Poliglota)

O projeto distribui seus dados em três bancos de dados para aproveitar os pontos fortes de cada um:

### 1. MySQL (Banco de Dados Relacional)

* **Tecnologia:** SQLAlchemy com `mysql+pymysql`.
* **Propósito:** Armazenar dados relacionais e transacionais que exigem alta consistência (ACID).
* **Tabelas:**
    * `usuarios`: Armazena informações de contas de usuário (ID, nome, email, senha com hash). Garante que cada email seja único.
    * `favoritos`: Tabela de associação (muitos-para-muitos) que liga `user_id` a `produto_id`.

### 2. MongoDB (Banco de Dados de Documento)

* **Tecnologia:** PyMongo.
* **Propósito:** Armazenar o catálogo de produtos. Um banco de dados de documento é ideal aqui devido à flexibilidade do esquema (produtos podem ter atributos variados, como diferentes tamanhos, cores, etc.).
* **Coleção:**
    * `produtos`: Armazena todos os detalhes dos produtos, incluindo nome, preço, descrição, categoria, listas de tamanhos, cores e caminhos para as imagens.

### 3. Cassandra (Banco de Dados Colunar)

* **Tecnologia:** `cassandra-driver`.
* **Propósito:** Gerenciar dados de alta escrita e que se beneficiam de particionamento, como carrinhos de compras.
* **Tabela:**
    * `carrinho_items`: Armazena os itens no carrinho de cada usuário. É particionado por `user_id` e ordenado por `item_id` (um `timeuuid`) para exibir os itens mais recentes primeiro. A conexão inclui uma lógica de nova tentativa (`connect_to_cassandra`) para resiliência.

---

---

## Descrição dos Arquivos Principais

### `web/app.py` (Ponto de Entrada)

* Inicializa a aplicação Flask.
* Carrega variáveis de ambiente do `.env` usando `load_dotenv()`.
* Configura pastas `static_folder` e `template_folder`.
* Define e cria a pasta de `UPLOAD_FOLDER` (para imagens de produtos).
* Configura a `SECRET_KEY` para gerenciamento de sessão.
* Registra o *Blueprint* de rotas (`routes_bp`) vindo de `app/routes.py`.
* Inicia o servidor de desenvolvimento quando executado diretamente.

### `web/app/models.py` (Camada de Dados)

* Define as conexões para os três bancos de dados (MySQL, MongoDB, Cassandra).
* Lê as credenciais e hosts das variáveis de ambiente (ex: `MYSQL_HOST`, `MONGO_USER`, `CASSANDRA_CONTACT_POINTS`).
* **MySQL:** Configura o `engine` e `SessionLocal` do SQLAlchemy.
* **MongoDB:** Configura o `mongo_client` e aponta para a coleção `produtos`.
* **Cassandra:** Configura o `cluster` e a `cassandra_session`, incluindo lógica de retry.
* **Funções de Inicialização:**
    * `init_mysql()`: Cria as tabelas `usuarios` e `favoritos` se não existirem.
    * `init_cassandra()`: Cria o `KEYSPACE ecommerce` e a tabela `carrinho_items` se não existirem.
    * `init_all()`: Função principal que chama as duas funções acima, garantindo que o schema dos bancos de dados esteja pronto.

### `web/app/routes.py` (Camada de Controle)

* Define todas as rotas (endpoints) da aplicação usando um Flask `Blueprint`.
* Chama `init_all()` na inicialização do módulo para garantir que os bancos de dados estejam prontos antes de a aplicação começar a servir requisições.
* **Decorator:**
    * `@login_required`: Um decorator personalizado que verifica se `user_id` está na `session`. Se não estiver, redireciona o usuário para a página de login.
* **Rotas Principais:**
    * `GET /`: Página inicial, exibe 8 produtos.
    * `GET /products`: Lista todos os produtos.
    * `GET /product/<product_id>`: Exibe detalhes de um produto específico.
* **Rotas de Autenticação:**
    * `GET, POST /login`: Autentica o usuário (consulta MySQL) e armazena `user_id` na sessão.
    * `GET, POST /register`: Registra um novo usuário (insere no MySQL).
    * `GET /logout`: Limpa a sessão do usuário.
* **Rotas de Administrador:**
    * `GET, POST /admin/products`: (Requer login) Lista produtos e permite adicionar novos produtos (com upload de imagens) ao MongoDB.
* **Rotas do Carrinho (Cassandra):**
    * `GET /cart`: (Requer login) Exibe os itens do carrinho do usuário, buscando dados do Cassandra e enriquecendo-os com dados do MongoDB.
    * `POST /cart/add`: (Requer login) Adiciona um item ao carrinho no Cassandra.
    * `GET /cart/remove/<item_id>`: (Requer login) Remove um item do carrinho no Cassandra.
    * `GET /cart/count`: Retorna a contagem de itens no carrinho (usado para atualizar o ícone do carrinho via JS).
* **Outras Rotas:**
    * `POST /checkout`: (Requer login) Limpa o carrinho do usuário no Cassandra.
    * `GET /favorites`: (Requer login) Página de favoritos (atualmente apenas renderiza o template).

---

## Funcionalidades

* **Autenticação:** Cadastro e login de usuários (armazenados no MySQL).
* **Catálogo de Produtos:** Listagem e visualização de detalhes de produtos (armazenados no MongoDB).
* **Carrinho de Compras:** Adicionar, remover e visualizar itens no carrinho (armazenado no Cassandra).
* **Gerenciamento de Produtos:** Uma área de "admin" (`/admin/products`) permite cadastrar novos produtos, incluindo o upload de múltiplas imagens.
* **Sessão de Usuário:** O Flask `session` é usado para rastrear o usuário logado.

---

## Como Executar

O projeto é claramente desenhado para ser executado com contêineres, dada a presença do `Dockerfile` e do `entrypoint.sh`, e a complexidade de gerenciar 3 bancos de dados.

### 1. Configuração de Ambiente

Crie um arquivo `.env` na pasta `web/` (baseado no `.env.example`, se existir) com as seguintes variáveis (valores padrão do `models.py` mostrados):
---

## Como Executar

Existem duas formas principais de executar este projeto: via Docker (recomendado) ou localmente para desenvolvimento.


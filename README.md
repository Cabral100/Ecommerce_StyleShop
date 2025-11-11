#  E-commerce - Loja de Roupas

##  Membros do Grupo

| Nome | RA |
| ----------- | ----------- |
| Guilherme Morais Escudeiro | 24.123.005-1 |
| Lucas Cabral | 24.123.032-5 |
| Gustavo Atui | 24.123.072-1 |

---

##  Tema Escolhido

O tema escolhido foi o desenvolvimento de um **E-commerce de Roupas**, uma aplicação web completa que simula uma loja virtual funcional.  
O objetivo do projeto é aplicar conceitos de **desenvolvimento web full stack**, **bancos de dados relacionais e não relacionais** e **arquitetura em contêineres** (Docker), permitindo a venda e gerenciamento de produtos de forma organizada e escalável.

O sistema permite que usuários:
- Cadastrem e façam login em suas contas;
- Naveguem por produtos disponíveis;
- Adicionem itens ao carrinho e finalizem pedidos;
- Gerenciem produtos (via painel administrativo);
- Visualizem detalhes e imagens de cada peça de roupa.
- Visualizem o carrinho de compras e histórico de pedidos

---

##  Justificativa dos Bancos de Dados e Implementação do S2

O projeto utiliza **três bancos de dados diferentes**, cada um com uma finalidade específica. A ideia é simular uma arquitetura **poliglota**, em que cada tecnologia é usada conforme sua melhor aplicação.

###  PostgreSQL (Banco Relacional)

- **Função no projeto:** Armazenar dados estruturados e críticos, como informações de usuários, pedidos e relacionamento entre produtos e categorias.
- **Justificativa:** O PostgreSQL oferece consistência transacional (ACID) e suporte a consultas complexas com joins e relacionamentos, essenciais para o controle de usuários e pedidos.

###  MongoDB (Banco NoSQL de Documentos)

- **Função no projeto:** Armazenar dados de produtos e suas variações (como tamanhos, cores, descrições e imagens).
- **Justificativa:** O MongoDB é ideal para dados sem estrutura rígida, permitindo flexibilidade na adição de novos atributos aos produtos sem alterar o schema.

###  Apache Cassandra (Banco NoSQL de Colunas)

- **Função no projeto:** Registrar o histórico de acessos e interações dos usuários (como visualizações de produtos e comportamento de compra).
- **Justificativa:** O Cassandra é otimizado para gravações rápidas e escalabilidade horizontal, ideal para análises de comportamento e grandes volumes de dados.

---

###  Implementação do S2 (Subsistema 2)

O **S2** será o subsistema responsável pela **gestão e integração entre os bancos de dados**.  
Ele será implementado como um **módulo de serviços independentes**, responsável por:

- Coordenar as operações de leitura e escrita entre PostgreSQL, MongoDB e Cassandra;  
- Garantir consistência eventual entre os bancos;  
- Expor endpoints REST que permitam acesso centralizado aos dados combinados.

**Exemplo de funcionamento:**
- Ao registrar um novo pedido, o S2 grava:
  - Informações do pedido no **PostgreSQL**;
  - Itens do carrinho (com detalhes de produtos) no **MongoDB**;
  - Log da transação e histórico de ações no **Cassandra**.

Esse modelo garante **resiliência e escalabilidade**, além de demonstrar o uso combinado de diferentes tecnologias de banco de dados.

---

##  Tecnologias Utilizadas

| Tecnologia | Função |
|-------------|--------|
| **Python 3.11** | Linguagem principal do projeto |
| **Flask** | Framework web para rotas e controle da aplicação |
| **PostgreSQL** | Banco relacional (usuários, pedidos) |
| **MongoDB** | Banco NoSQL de produtos |
| **Apache Cassandra** | Banco NoSQL para logs e histórico |
| **HTML / CSS / JavaScript** | Estrutura e estilo das páginas |
| **Docker** | Containerização e orquestração de serviços |
| **Docker Compose** | Gerenciamento e execução dos contêineres |

---

##  Funcionalidades Principais

✅ Página inicial com listagem de produtos  
✅ Autenticação de usuário (login e registro)  
✅ Página de detalhes de produto  
✅ Painel administrativo para cadastro e gerenciamento de produtos  
✅ Carrinho de compras e pedidos  
✅ Upload de imagens com verificação de formato (`.png`, `.jpg`, `.jpeg`, `.gif`)  
✅ Histórico de navegação e interações (via Cassandra)  

---

##  Estrutura do Projeto

```bash
ecommerce-flask/
│
├── web/
│   ├── app/
│   │   ├── static/
│   │   │   ├── js/
│   │   │   │   └── main.js
│   │   │   └── style.css
│   │   │
│   │   ├── templates/
│   │   │   ├── _layout.html
│   │   │   ├── index.html
│   │   │   ├── products.html
│   │   │   ├── product_detail.html
│   │   │   ├── cart.html
│   │   │   ├── orders.html
│   │   │   ├── login.html
│   │   │   ├── register.html
│   │   │   └── admin_products.html
│   │   │
│   │   ├── models.py
│   │   ├── routes.py
│   │   └── __init__.py
│   │
│   ├── app.py
│   └── requirements.txt
│
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── entrypoint.sh
├── run.txt
└── README.md
```


---

## Como executar

- Clone o repositório
```bash
git clone https://github.com/Cabral100/ecommerce-flask.git
cd ecommerce-flask
```

- Copie o arquivo de exemplo de variáveis
```bash
cp .env.example .env
```

- Construa e suba os containers

```bash
docker-compose up --build
```

- Acesse a aplicação

```bash
http://localhost:5000
```

- Parar a aplicação

```bash
docker-compose down
```






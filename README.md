#  E-commerce  - Loja de Roupas

## Membros do grupo
| Nome | RA |
| ----------- | ----------- |
| Guilherme Morais Escudeiro | 24.123.005-1 |
| Lucas Cabral  | 24.123.032-5 |
| Gustavo Atui  | 24.123.072-1 |

Este projeto é um **e-commerce de roupas** desenvolvido com **Python (Flask)**.  
O objetivo é simular uma loja virtual funcional, com páginas de produtos, carrinho de compras e autenticação de usuários, utilizando boas práticas de desenvolvimento web.

---

##  Tecnologias Utilizadas

- **Python 3.11**
- **Flask** — Framework web principal  
- **MongoDB** — Banco de dados NoSQL
- **Postegres SQL** — Banco de dados relacional
-  **Apache Cassandra** — Banco de dados NoSQL  
- **HTML / CSS / JavaScript** — Estrutura e estilo das páginas  
- **Docker** — Containerização da aplicação  


---

##  Funcionalidades Principais

✅ **Página inicial** com exibição dos produtos  
✅ **Autenticação de usuário (login e registro)**  
✅ **Página de detalhes de produto**  
✅ **Página de gerenciar a criação de novos produtos**  
✅ **Carrinho de compras e pedidos**  
✅ **Informações sobre o produto ao clicar nele**  
✅ **Upload de imagens com verificação de formato (`.png`, `.jpg`, `.jpeg`, `.gif`)**  

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







import os
import uuid
from flask import (Blueprint, render_template, request, redirect, url_for, 
                   session, flash, current_app)
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import (produtos_collection, SessionLocal, init_all, 
                    cassandra_session)

# --- Configuração Inicial ---
bp = Blueprint('routes', __name__)
init_all()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Rotas da Aplicação ---

@bp.route('/')
def index():
    produtos = list(produtos_collection.find())
    return render_template('index.html', produtos=produtos)

@bp.route('/produtos', methods=['GET', 'POST'])
def gerenciar_produtos():
    # Proteção de rota: somente usuários logados podem acessar
    if 'user_id' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('routes.login'))

    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        
        # Lógica para salvar as imagens
        imagens_salvas = []
        uploaded_files = request.files.getlist('imagens')
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                imagens_salvas.append(filename)

        # Insere o novo produto no banco de dados
        produtos_collection.insert_one({
            'nome': nome, 
            'preco': preco,
            'imagens': imagens_salvas # Salva a lista de nomes de imagem
        })
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('routes.gerenciar_produtos'))
    
    produtos = list(produtos_collection.find())
    return render_template('products.html', produtos=produtos)

# --- Rotas de Autenticação ---

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        db = SessionLocal()
        try:
            # Busca o usuário no banco de dados MySQL
            result = db.execute(text("SELECT * FROM usuarios WHERE email = :email"), {'email': email})
            usuario = result.fetchone()
            
            if usuario and check_password_hash(usuario.senha, senha):
                session['user_id'] = usuario.id
                session['user_name'] = usuario.nome
                flash(f'Bem-vindo de volta, {usuario.nome}!', 'success')
                return redirect(url_for('routes.index'))
            else:
                flash('Email ou senha inválidos. Tente novamente.', 'danger')
        finally:
            db.close()
    return render_template('login.html')

@bp.route('/register', methods=['POST'])
def register():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    db = SessionLocal()
    try:
        # Verifica se o email já existe
        result = db.execute(text("SELECT id FROM usuarios WHERE email = :email"), {'email': email})
        if result.fetchone():
            flash('Este email já está em uso. Tente outro.', 'warning')
            return redirect(url_for('routes.login'))

        # Criptografa a senha antes de salvar
        senha_hash = generate_password_hash(senha)
        
        # Salva o novo usuário no banco MySQL
        db.execute(text("INSERT INTO usuarios (nome, email, senha) VALUES (:nome, :email, :senha)"),
                   {'nome': nome, 'email': email, 'senha': senha_hash})
        db.commit()
        flash('Cadastro realizado com sucesso! Agora você pode fazer o login.', 'success')
    finally:
        db.close()
    return redirect(url_for('routes.login'))

@bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('routes.index'))


# --- Rotas existentes (Clientes e Carrinho) ---

@bp.route('/clientes', methods=['POST'])
def add_cliente():
    # Esta rota pode ser usada para um cadastro de cliente separado do login, se desejar
    nome = request.form['nome']
    email = request.form['email']
    telefone = request.form.get('telefone')
    db = SessionLocal()
    try:
        db.execute(text("INSERT INTO clientes (nome, email, telefone) VALUES (:nome, :email, :telefone)"),
                   {'nome': nome, 'email': email, 'telefone': telefone})
        db.commit()
    finally:
        db.close()
    flash('Cliente adicionado!', 'success')
    return redirect(url_for('routes.index'))

@bp.route('/carrinho/add', methods=['POST'])
def add_to_cart():
    cliente_email = request.form['email']
    produto_id = request.form['produto_id']
    cart_id = str(uuid.uuid4())
    
    # Esta lógica pode ser melhorada para adicionar a um carrinho existente
    cassandra_session.execute(
        "INSERT INTO ecommerce.carrinho (id, cliente_email, produtos) VALUES (%s, %s, %s)",
        (cart_id, cliente_email, [produto_id])
    )
    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(url_for('routes.index'))
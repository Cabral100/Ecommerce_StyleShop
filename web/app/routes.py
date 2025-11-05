import os
import uuid
from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, flash, current_app, jsonify)
from sqlalchemy import text, exc
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from .models import (produtos_collection, SessionLocal, init_all, cassandra_session)
from bson import ObjectId
from functools import wraps

bp = Blueprint('routes', __name__)
init_all()
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Rotas Principais e de Produto ---
@bp.route('/')
def index():
    produtos = list(produtos_collection.find().limit(8))
    for p in produtos: p['_id'] = str(p['_id'])
    return render_template('index.html', produtos=produtos)

@bp.route('/products')
def products():
    produtos = list(produtos_collection.find())
    for p in produtos: p['_id'] = str(p['_id'])
    return render_template('products.html', produtos=produtos)

@bp.route('/product/<product_id>')
def product_detail(product_id):
    try:
        produto = produtos_collection.find_one({'_id': ObjectId(product_id)})
        if not produto: return redirect(url_for('routes.products'))
        produto['_id'] = str(produto['_id'])
        return render_template('product_detail.html', produto=produto)
    except Exception:
        return redirect(url_for('routes.products'))

# --- Autenticação ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session: return redirect(url_for('routes.index'))
    if request.method == 'POST':
        db = SessionLocal()
        usuario = db.execute(text("SELECT id, nome, senha FROM usuarios WHERE email = :email"), {'email': request.form['email']}).fetchone()
        db.close()
        if usuario and check_password_hash(usuario.senha, request.form['senha']):
            session['user_id'] = usuario.id
            session['user_name'] = usuario.nome
            return redirect(url_for('routes.index'))
        else:
            flash('Email ou senha inválidos.', 'danger')
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session: return redirect(url_for('routes.index'))
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        senha_hash = generate_password_hash(senha)
        db = SessionLocal()
        try:
            db.execute(text("INSERT INTO usuarios (nome, email, senha) VALUES (:nome, :email, :senha)"),
                       {'nome': nome, 'email': email, 'senha': senha_hash})
            db.commit()
            flash('Cadastro realizado com sucesso! Faça o login.', 'success')
            return redirect(url_for('routes.login'))
        except exc.IntegrityError:
            flash('Este email já está em uso.', 'danger')
            return redirect(url_for('routes.register'))
        finally:
            db.close()
    return render_template('register.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('routes.index'))

# --- Gerenciamento de Produtos (Admin) ---
@bp.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    if request.method == 'POST':
        sizes = [s.strip().upper() for s in request.form.get('sizes', '').split(',') if s.strip()]
        colors = [c.strip().capitalize() for c in request.form.get('colors', '').split(',') if c.strip()]
        
        imagens_salvas = []
        uploaded_files = request.files.getlist('imagens')
        for file in uploaded_files:
            if file: 
                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(save_path)
                imagens_salvas.append(filename)

        new_product = {
            'nome': request.form['nome'],
            'preco': float(request.form['preco']),
            'descricao': request.form.get('descricao', ''),
            'category': request.form['category'],
            'sizes': sizes,
            'colors': colors,
            'imagens': imagens_salvas
        }
        produtos_collection.insert_one(new_product)
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('routes.admin_products'))
    
    produtos = list(produtos_collection.find())
    for p in produtos:
        p['_id'] = str(p['_id'])
    return render_template('admin_products.html', produtos=produtos)

# --- Carrinho ---
def get_cart_items_from_db(user_id):
    query = "SELECT item_id, product_id, size, color, quantity FROM carrinho_items WHERE user_id = %s"
    return list(cassandra_session.execute(query, (user_id,)))

@bp.route('/cart')
@login_required
def view_cart():
    items_db = get_cart_items_from_db(session['user_id'])
    total = 0
    detailed_items = []
    if items_db:
        product_ids = {item.product_id for item in items_db}
        products_mongo = {str(p['_id']): p for p in produtos_collection.find({'_id': {'$in': [ObjectId(pid) for pid in product_ids]}})}
        
        for item in items_db:
            product_info = products_mongo.get(item.product_id)
            if product_info:
                total += product_info['preco'] * item.quantity
                detailed_item = {**product_info, **item._asdict()}
                detailed_items.append(detailed_item)
    return render_template('cart.html', produtos=detailed_items, total=total)

@bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    user_id = session['user_id']
    product_id = request.form['product_id']
    size = request.form['size']
    color = request.form['color']
    
    query_insert = """
    INSERT INTO carrinho_items (user_id, item_id, product_id, size, color, quantity, added_time)
    VALUES (%s, now(), %s, %s, %s, 1, toTimestamp(now()))
    """
    cassandra_session.execute(query_insert, (user_id, product_id, size, color))
    return jsonify({'status': 'success', 'message': 'Produto adicionado ao carrinho!'})

@bp.route('/cart/count')
def cart_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    items = get_cart_items_from_db(session['user_id'])
    return jsonify({'count': sum(item.quantity for item in items)})

@bp.route('/cart/remove/<item_id>')
@login_required
def remove_from_cart(item_id):
    user_id = session['user_id']
    query = "DELETE FROM carrinho_items WHERE user_id = %s AND item_id = %s"
    try:
        cassandra_session.execute(query, (user_id, uuid.UUID(item_id)))
    except ValueError:
        flash("ID do item inválido.", "danger")
    return redirect(url_for('routes.view_cart'))

# --- Checkout e Favoritos ---
@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    query = "DELETE FROM carrinho_items WHERE user_id = %s"
    cassandra_session.execute(query, (session['user_id'],))
    flash('Compra finalizada com sucesso!', 'success')
    return redirect(url_for('routes.index'))

@bp.route('/favorites')
@login_required
def view_favorites():
    return render_template('favorites.html')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
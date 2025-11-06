import os, uuid, datetime # <-- ALTERAÇÃO: Adicionado datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from sqlalchemy import text, exc
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from .models import (
    produtos_collection, 
    carrinhos_collection,  # <-- ALTERAÇÃO: Importado
    SessionLocal, 
    init_all, 
    cassandra_session
)
from bson import ObjectId
from functools import wraps

bp = Blueprint('routes', __name__)
init_all() 

# Extensões permitidas para upload de imagens
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

# --- Rotas principais ---

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
        if not produto:
            return redirect(url_for('routes.products'))
        produto['_id'] = str(produto['_id'])

        favoritos = []
        if 'user_id' in session:
            db = SessionLocal()
            favoritos = [f.produto_id for f in db.execute(
                text("SELECT produto_id FROM favoritos WHERE user_id = :uid"),
                {'uid': session['user_id']}
            ).fetchall()]
            db.close()

        return render_template('product_detail.html', produto=produto, favoritos=favoritos)
    except Exception:
        return redirect(url_for('routes.products'))


# --- Autenticação (MySQL) ---

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Login do usuário
    if 'user_id' in session: return redirect(url_for('routes.index'))
    if request.method == 'POST':
        db = SessionLocal()
        usuario = db.execute(text("SELECT id, nome, senha FROM usuarios WHERE email = :email"),
                             {'email': request.form['email']}).fetchone()
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
    # Cadastro de novo usuário
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
            flash('Cadastro realizado com sucesso!', 'success')
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

# --- Painel Admin (MongoDB) ---

# Em web/app/routes.py
@bp.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    # Adiciona novos produtos e lista os existentes
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

        
        category = request.form['category']         
        product_type = request.form['product_type']
        
        detalhes = {} # Subdocumento para dados flexíveis

        if product_type == 'camiseta':
            detalhes['tipo_gola'] = request.form.get('tipo_gola', '')
            detalhes['tipo_manga'] = request.form.get('tipo_manga', '')
        elif product_type == 'sapato':
            detalhes['cor_cadarco'] = request.form.get('cor_cadarco', '')
            detalhes['material_sola'] = request.form.get('material_sola', '')
        elif product_type == 'touca':
            detalhes['tem_pompom'] = request.form.get('tem_pompom') == 'true'

        new_product = {
            'nome': request.form['nome'],
            'preco': float(request.form['preco']),
            'descricao': request.form.get('descricao', ''),
            'category': category,          
            'product_type': product_type,  
            'sizes': sizes,
            'colors': colors,
            'imagens': imagens_salvas,
            'detalhes': detalhes            
        }
        
        produtos_collection.insert_one(new_product)
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('routes.admin_products'))
    
    produtos = list(produtos_collection.find())
    for p in produtos: p['_id'] = str(p['_id'])
    return render_template('admin_products.html', produtos=produtos)



def get_cart_items(user_id):
    """Busca itens do carrinho do usuário no MongoDB e junta com infos do produto."""
    cart = carrinhos_collection.find_one({'user_id': user_id})
    
    if not cart or not cart.get('items'):
        return [], 0
    
    items_db = cart['items']
    total = 0
    detailed_items = []
    
    # Busca todos os produtos necessários do MongoDB de uma só vez
    product_ids = {item['product_id'] for item in items_db}
    products_mongo = {str(p['_id']): p for p in produtos_collection.find({'_id': {'$in': [ObjectId(pid) for pid in product_ids]}})}

    for item in items_db:
        product_info = products_mongo.get(item['product_id'])
        if product_info:
            item_total = product_info['preco'] * item['quantity']
            total += item_total
            # Junta as informações do produto com as do item no carrinho
            detailed_item = {
                **product_info, 
                'cart_item_id': item['cart_item_id'], 
                'product_id': item['product_id'],
                'size': item['size'],
                'color': item['color'],
                'quantity': item['quantity']
            }
            detailed_items.append(detailed_item)
            
    return detailed_items, total

@bp.route('/cart')
@login_required
def view_cart():
    detailed_items, total = get_cart_items(session['user_id'])
    return render_template('cart.html', produtos=detailed_items, total=total)

@bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    user_id = session['user_id']
    
    new_item = {
        'cart_item_id': str(uuid.uuid4()), 
        'product_id': request.form['product_id'],
        'size': request.form['size'],
        'color': request.form['color'],
        'quantity': 1 
    }

    carrinhos_collection.update_one(
        {'user_id': user_id},
        {
            '$push': {'items': new_item},
            '$setOnInsert': {'user_id': user_id}
        },
        upsert=True
    )
    return jsonify({'status': 'success', 'message': 'Produto adicionado ao carrinho!'})

@bp.route('/cart/count')
def cart_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    
    detailed_items, _ = get_cart_items(session['user_id'])
    count = sum(item['quantity'] for item in detailed_items)
    return jsonify({'count': count})

@bp.route('/cart/remove/<item_id>')
@login_required
def remove_from_cart(item_id):
    # Remove item específico do carrinho usando o cart_item_id
    user_id = session['user_id']
    
    # Usa '$pull' para remover o subdocumento 'item' que bate com o 'cart_item_id'
    carrinhos_collection.update_one(
        {'user_id': user_id},
        {'$pull': {'items': {'cart_item_id': item_id}}}
    )
    return redirect(url_for('routes.view_cart'))




@bp.route('/pedidos')
@login_required
def view_orders():
    user_id = session['user_id']
    
    query_select = "SELECT * FROM pedidos_por_usuario WHERE user_id = %s"
    pedidos = cassandra_session.execute(query_select, (user_id,))
    
    pedidos_list = []
    for pedido in pedidos:
        # Converte o timeuuid para string para facilitar a exibição
        pedido_dict = {
            'pedido_id': str(pedido.pedido_id),
            'data_pedido': pedido.data_pedido,
            'status': pedido.status,
            'total_pedido': pedido.total_pedido,
            'itens': pedido.itens
        }
        pedidos_list.append(pedido_dict)
        
    return render_template('orders.html', pedidos=pedidos_list)


@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    
    user_id = session['user_id']
    
    detailed_items, total = get_cart_items(user_id)
    
    if not detailed_items:
        flash('Seu carrinho está vazio.', 'warning')
        return redirect(url_for('routes.view_cart'))

    #    (Salvamos um 'map' com os detalhes para garantir que o histórico do pedido
    #    não mude se o produto for atualizado no futuro)
    itens_para_pedido = []
    for item in detailed_items:
        itens_para_pedido.append({
            'product_id': item['product_id'],
            'nome': item['nome'],
            'preco_unitario': str(item['preco']),
            'quantidade': str(item['quantity']),
            'size': item['size'],
            'color': item['color']
        })

    query_insert = """
    INSERT INTO pedidos_por_usuario (user_id, pedido_id, data_pedido, status, total_pedido, itens)
    VALUES (%s, now(), %s, %s, %s, %s)
    """
    cassandra_session.execute(query_insert, (
        user_id,
        datetime.datetime.utcnow(),
        'Processando', 
        total,
        itens_para_pedido
    ))
    
    # Limpa o carrinho do MongoDB
    carrinhos_collection.delete_one({'user_id': user_id})
    
    flash('Compra finalizada com sucesso!', 'success')
    return redirect(url_for('routes.index')) 

# --- FAVORITOS (MySQL) ---

@bp.route('/favorites')
@login_required
def view_favorites():
    db = SessionLocal()
    favoritos = db.execute(text("SELECT produto_id FROM favoritos WHERE user_id = :uid"), {'uid': session['user_id']}).fetchall()
    db.close()

    produtos = []
    if favoritos:
        ids = [ObjectId(f.produto_id) for f in favoritos]
        produtos = list(produtos_collection.find({'_id': {'$in': ids}}))
        for p in produtos:
            p['_id'] = str(p['_id'])
    return render_template('favorites.html', produtos=produtos)

@bp.route('/favorites/toggle/<product_id>', methods=['POST'])
@login_required
def toggle_favorite(product_id):
    db = SessionLocal()
    existing = db.execute(text("SELECT * FROM favoritos WHERE user_id = :uid AND produto_id = :pid"),
                          {'uid': session['user_id'], 'pid': product_id}).fetchone()
    if existing:
        db.execute(text("DELETE FROM favoritos WHERE user_id = :uid AND produto_id = :pid"),
                   {'uid': session['user_id'], 'pid': product_id})
        db.commit()
        db.close()
        return jsonify({'status': 'removed'})
    else:
        db.execute(text("INSERT INTO favoritos (user_id, produto_id) VALUES (:uid, :pid)"),
                   {'uid': session['user_id'], 'pid': product_id})
        db.commit()
        db.close()
        return jsonify({'status': 'added'})
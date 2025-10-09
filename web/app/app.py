# app.py

from flask import Flask, send_from_directory
from dotenv import load_dotenv
import os
from routes import bp as routes_bp

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

# --- Configurações Essenciais ---

# Chave secreta para a sessão (obrigatório para login e flash messages)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma-chave-secreta-de-desenvolvimento')

# Configuração da pasta de uploads
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Garante que a pasta exista

# --- Registro de Blueprints ---
app.register_blueprint(routes_bp)

# --- Rotas Específicas da Aplicação ---

# NOVA: Rota para servir os arquivos de imagem da pasta /uploads
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=(os.getenv('FLASK_ENV')=='development'))
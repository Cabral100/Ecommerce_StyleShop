from flask import Flask
from dotenv import load_dotenv
import os
from app.routes import bp as routes_bp 

load_dotenv()

app = Flask(__name__, 
            static_folder='app/static', 
            template_folder='app/templates',
            static_url_path='/static')


UPLOAD_FOLDER = os.path.join(app.root_path, 'app', 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'uma-chave-secreta-de-desenvolvimento-muito-segura')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.register_blueprint(routes_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
# backend/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import os # Importe o módulo os

db = SQLAlchemy()
login_manager = LoginManager()
DB_NAME = 'site.db'
basedir = path.abspath(path.dirname(__file__))
instance_path = path.join(basedir, '..', 'instance')
database_path = path.join(instance_path, DB_NAME)

# Configurações para upload de arquivos
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads') # Pasta onde as fotos serão salvas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # Extensões de arquivo permitidas

def create_app():
    app = Flask(__name__, instance_path=instance_path)
    app.config['SECRET_KEY'] = 'chave_secreta_para_seguranca'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    
    # NOVAS CONFIGURAÇÕES PARA UPLOAD
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para uploads
    # Garante que a pasta de uploads existe
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))

    from .routes import routes
    app.register_blueprint(routes, url_prefix='/')

    from .models import User, Paciente, RegistroEmocao, RespostaQuestionario, Consulta

    with app.app_context():
        db.create_all() # Isso criará a nova coluna 'foto_perfil' se ela não existir

    return app

# Função auxiliar para verificar a extensão do arquivo
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
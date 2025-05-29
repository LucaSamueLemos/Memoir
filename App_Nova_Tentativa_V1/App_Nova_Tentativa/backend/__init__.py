# backend/__init__.py OU backend/app.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
DB_NAME = "site.db"
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui' # Mude para uma chave segura em produção
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    app.config['UPLOAD_FOLDER'] = path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # Limite de 16MB para uploads

    # Inicializa as extensões com o app
    db.init_app(app)
    migrate.init_app(app, db)

    # Importa os modelos aqui para evitar problemas de importação circular
    # e garantir que eles sejam carregados após 'db' ser inicializado.
    from .models import User, Paciente, RegistroEmocao, RespostaQuestionario # Removendo 'Consulta' se não estiver em models.py

    # Importa as rotas
    from .routes import routes
    app.register_blueprint(routes, url_prefix='/')

    # Cria o banco de dados se não existir
    with app.app_context():
        if not path.exists(path.join(app.instance_path, DB_NAME)):
            db.create_all()
            print('Banco de dados criado!')
        else:
            print('Banco de dados já existe.')

    # Configura o Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = 'routes.login' # Rota para onde redirecionar se o usuário não estiver logado
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id)) # Busca um usuário pelo ID

    return app

# Se você estiver usando um arquivo app.py que é executado diretamente,
# pode querer adicionar o seguinte para que 'python -m backend.app' funcione:
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) # Modo debug é bom para desenvolvimento
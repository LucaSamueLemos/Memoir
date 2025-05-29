# backend/app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from backend.routes import routes
from backend import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) # Executar o servidor em modo de desenvolvimento

db = SQLAlchemy()
DB_NAME = 'site.db'

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'chave_secreta_para_seguranca' # Substitua por uma chave segura de verdade
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .routes import routes
    app.register_blueprint(routes, url_prefix='/')

    from .models import User, Paciente, RegistroEmocao, RespostaQuestionario

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'routes.login' # Define a página de login
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) # Executar o servidor em modo de desenvolvimento
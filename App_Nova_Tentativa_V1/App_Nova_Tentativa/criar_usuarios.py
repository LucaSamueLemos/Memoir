# criar_usuarios.py
from backend import create_app, db
from backend.models import User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Criar um psicólogo
    if not User.query.filter_by(email='psicologo@email.com').first():
        novo_psicologo = User(email='psicologo@email.com', password=generate_password_hash('senha123'), tipo='psicologo')
        db.session.add(novo_psicologo)
        db.session.commit()
        print('Psicólogo criado.')

    # Criar um paciente
    if not User.query.filter_by(email='paciente@email.com').first():
        novo_paciente = User(email='paciente@email.com', password=generate_password_hash('senha123'), tipo='paciente')
        db.session.add(novo_paciente)
        db.session.commit()
        print('Paciente criado.')

    print('Usuários iniciais criados.')
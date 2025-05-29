# backend/models.py

from . import db # Importa a instância global de SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # 'paciente' ou 'psicologo'

    # Relação 1: User (como usuário de login) para Paciente (perfil associado)
    # Um User (paciente) tem UM Paciente (perfil).
    # primaryjoin é essencial para diferenciar de outras FKs entre User e Paciente.
    paciente_perfil = db.relationship(
        'Paciente',
        back_populates='user_login', # back_populates aponta para o atributo na classe Paciente
        lazy=True,
        uselist=False, # Um usuário paciente só tem um perfil de paciente
        primaryjoin="User.id == Paciente.id" # Esta é a FK onde User.id == Paciente.id
    )

    # Relação 2: User (como psicólogo) para MÚLTIPLOS Pacientes
    # Um User (psicólogo) pode ter MÚLTIPLOS Pacientes.
    pacientes_atendidos = db.relationship(
        'Paciente',
        foreign_keys='Paciente.psicologo_id', # Esta é a FK onde Paciente.psicologo_id == User.id
        backref='psicologo_responsavel', # backref cria um atributo 'psicologo_responsavel' no Paciente
        lazy=True
    )

    def __repr__(self):
        return f'<User {self.email} ({self.tipo})>'

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Paciente(db.Model):
    # O ID do paciente é também o ID do seu User associado
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=True)
    # ID do psicólogo que acompanha este paciente
    psicologo_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    foto_perfil = db.Column(db.String(255), nullable=False, default='default.jpg')

    # Relação do Paciente de volta para o User (seu próprio usuário de login)
    # back_populates aponta para o atributo 'paciente_perfil' em User
    user_login = db.relationship(
        'User',
        back_populates='paciente_perfil', # back_populates aponta para o atributo 'paciente_perfil' em User
        foreign_keys=[id], # A chave estrangeira para esta relação é o próprio id do Paciente
        lazy=True,
        uselist=False # Um perfil de paciente pertence a um único User
    )

    registros_emocoes = db.relationship('RegistroEmocao', backref='paciente_obj', lazy=True)
    respostas_questionario = db.relationship('RespostaQuestionario', backref='paciente_obj', lazy=True)

    def __repr__(self):
        return f'<Paciente {self.nome} (ID User: {self.id})>'

class RegistroEmocao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emocao = db.Column(db.String(100), nullable=False)
    data_registro = db.Column(db.DateTime, default=datetime.utcnow)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)

    def __repr__(self):
        return f'<RegistroEmocao {self.emocao} - Paciente: {self.paciente_id}>'

class RespostaQuestionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    humor_geral = db.Column(db.Integer, nullable=True) # Ex: 1-5
    sentimento_principal = db.Column(db.String(100), nullable=True)
    dormiu_bem = db.Column(db.Boolean, nullable=True)
    motivacao_tarefas = db.Column(db.Boolean, nullable=True)
    causa_estresse = db.Column(db.Text, nullable=True)
    data_resposta = db.Column(db.DateTime, default=datetime.utcnow)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=False)

    def __repr__(self):
        return f'<RespostaQuestionario - Paciente: {self.paciente_id} - {self.data_resposta.strftime("%Y-%m-%d")}>'
# backend/models.py
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    tipo = db.Column(db.String(20)) # 'paciente' ou 'psicologo'
    pacientes = db.relationship('Paciente', backref='psicologo', lazy=True) # Psicólogo tem vários pacientes

    # Adicione estes métodos se ainda não os tiver para Flask-Login
    def get_id(self):
        return str(self.id)

    def is_active(self):
        return True # Todos os usuários são ativos
    
    def is_authenticated(self):
        return True # Os usuários autenticados são, bem, autenticados
    
    def is_anonymous(self):
        return False # Nossos usuários não são anônimos

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True) # Email do paciente
    psicologo_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Chave estrangeira para o User (psicólogo)
    registros_emocoes = db.relationship('RegistroEmocao', backref='paciente', lazy=True)
    respostas_questionario = db.relationship('RespostaQuestionario', backref='paciente', lazy=True)
    consultas = db.relationship('Consulta', backref='paciente', lazy=True)
    
    # NOVO: Adicione esta coluna para a foto de perfil
    foto_perfil = db.Column(db.String(255), nullable=True, default='default.jpg') # Armazenará o nome do arquivo da foto

class RegistroEmocao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emocao = db.Column(db.String(150))
    data_registro = db.Column(db.DateTime(timezone=True), default=func.now())
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'))

class RespostaQuestionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # NOVAS COLUNAS PARA AS RESPOSTAS DO QUESTIONÁRIO
    humor_geral = db.Column(db.Integer) # De 1 a 5
    sentimento_principal = db.Column(db.String(255)) # Texto livre
    dormiu_bem = db.Column(db.Boolean) # True/False
    motivacao_tarefas = db.Column(db.Boolean) # True/False
    causa_estresse = db.Column(db.Text) # Texto mais longo para descrição
    
    data_resposta = db.Column(db.DateTime(timezone=True), default=func.now())
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'))


class Consulta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime(timezone=True))
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'))
    psicologo_id = db.Column(db.Integer, db.ForeignKey('user.id'))
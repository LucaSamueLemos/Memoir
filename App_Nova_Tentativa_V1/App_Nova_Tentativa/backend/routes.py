# backend/routes.py

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import User, Paciente, RegistroEmocao, RespostaQuestionario
from . import db # Importa a instância db
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename
import os

# Função auxiliar para validar extensões de arquivo
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.tipo == 'paciente':
            return redirect(url_for('routes.paciente'))
        elif current_user.tipo == 'psicologo':
            return redirect(url_for('routes.psicologo'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            flash('Login realizado com sucesso!', category='success')
            login_user(user, remember=True)
            if user.tipo == 'paciente':
                return redirect(url_for('routes.paciente'))
            elif user.tipo == 'psicologo':
                return redirect(url_for('routes.psicologo'))
        else:
            flash('Email ou senha incorretos.', category='error')

    return render_template('index.html')

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso.', category='info')
    return redirect(url_for('routes.login'))

@routes.route('/paciente')
@login_required
def paciente():
    if current_user.tipo != 'paciente':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))
    
    # Usa a nova relação paciente_perfil
    paciente_logado = current_user.paciente_perfil 

    if not paciente_logado:
        flash('Seu perfil de paciente não foi encontrado no sistema. Entre em contato com o administrador.', category='error')
        logout_user()
        return redirect(url_for('routes.login'))

    return render_template('paciente.html', paciente=paciente_logado)

@routes.route('/registrar_emocao', methods=['POST'])
@login_required
def registrar_emocao():
    if current_user.tipo == 'paciente':
        emocao = request.form.get('emocao')
        if not emocao:
            flash('Por favor, insira uma emoção.', category='error')
            return redirect(url_for('routes.paciente'))

        nova_emocao = RegistroEmocao(emocao=emocao, paciente_id=current_user.id)
        db.session.add(nova_emocao)
        db.session.commit()
        flash('Emoção registrada com sucesso!', category='success')
    else:
        flash('Acesso não autorizado.', category='error')
    return redirect(url_for('routes.paciente'))

@routes.route('/responder_questionario', methods=['POST'])
@login_required
def responder_questionario():
    if current_user.tipo != 'paciente':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))

    humor_geral_str = request.form.get('humor_geral')
    sentimento_principal = request.form.get('sentimento_principal')
    dormiu_bem_str = request.form.get('dormiu_bem')
    motivacao_tarefas_str = request.form.get('motivacao_tarefas')
    causa_estresse = request.form.get('causa_estresse')

    humor_geral = None
    dormiu_bem = None
    motivacao_tarefas = None

    try:
        if humor_geral_str:
            humor_geral = int(humor_geral_str)
        
        if dormiu_bem_str is not None:
            dormiu_bem = (dormiu_bem_str == 'True')
        
        if motivacao_tarefas_str is not None:
            motivacao_tarefas = (motivacao_tarefas_str == 'True')

        nova_resposta = RespostaQuestionario(
            humor_geral=humor_geral,
            sentimento_principal=sentimento_principal,
            dormiu_bem=dormiu_bem,
            motivacao_tarefas=motivacao_tarefas,
            causa_estresse=causa_estresse,
            paciente_id=current_user.id
        )

        db.session.add(nova_resposta)
        db.session.commit()

        flash('Questionário respondido com sucesso!', category='success')
        return redirect(url_for('routes.paciente'))

    except ValueError:
        flash('Valores inválidos para humor ou perguntas Sim/Não. Por favor, verifique suas respostas.', category='error')
        return redirect(url_for('routes.paciente'))
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro inesperado ao salvar o questionário: {e}', category='error')
        return redirect(url_for('routes.paciente'))

@routes.route('/psicologo')
@login_required
def psicologo():
    if current_user.tipo != 'psicologo':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))
    
    # Usa a nova relação pacientes_atendidos
    pacientes = current_user.pacientes_atendidos
    return render_template('psicologo.html', pacientes=pacientes)

@routes.route('/paciente/<int:paciente_id>/registros')
@login_required
def ver_registros_paciente(paciente_id):
    if current_user.tipo != 'psicologo':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))

    # Garante que o psicólogo só veja pacientes sob sua responsabilidade
    paciente = Paciente.query.filter_by(id=paciente_id, psicologo_id=current_user.id).first()

    if not paciente:
        flash('Paciente não encontrado ou não associado a você.', category='error')
        return redirect(url_for('routes.psicologo'))

    registros_emocoes = RegistroEmocao.query.filter_by(paciente_id=paciente_id).order_by(RegistroEmocao.data_registro.desc()).all()
    respostas_questionario = RespostaQuestionario.query.filter_by(paciente_id=paciente_id).order_by(RespostaQuestionario.data_resposta.desc()).all()
    
    return render_template(
        'registros_paciente.html', 
        paciente=paciente, 
        registros_emocoes=registros_emocoes,
        respostas_questionario=respostas_questionario
    )

@routes.route('/paciente/upload_foto_propria', methods=['POST'])
@login_required
def upload_foto_propria_paciente():
    if current_user.tipo != 'paciente':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))

    paciente = current_user.paciente_perfil
    if not paciente:
        flash('Seu perfil de paciente não foi encontrado.', category='error')
        return redirect(url_for('routes.paciente'))

    if 'foto' not in request.files:
        flash('Nenhum arquivo de foto enviado.', category='error')
        return redirect(url_for('routes.paciente'))

    file = request.files['foto']

    if file.filename == '':
        flash('Nenhum arquivo selecionado.', category='error')
        return redirect(url_for('routes.paciente'))

    if file and allowed_file(file.filename):
        if paciente.foto_perfil and paciente.foto_perfil != 'default.jpg':
            old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], paciente.foto_perfil)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{current_user.id}_paciente_{timestamp}_{filename}" # Nome mais descritivo

        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        paciente.foto_perfil = filename
        db.session.commit()
        flash('Foto de perfil atualizada com sucesso!', category='success')
    else:
        flash('Tipo de arquivo não permitido.', category='error')

    return redirect(url_for('routes.paciente'))

@routes.route('/paciente/<int:paciente_id>/upload_foto_psicologo', methods=['POST'])
@login_required
def upload_foto_paciente_psicologo(paciente_id):
    if current_user.tipo != 'psicologo':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))

    paciente = Paciente.query.filter_by(id=paciente_id, psicologo_id=current_user.id).first()
    if not paciente:
        flash('Paciente não encontrado ou não associado a você.', category='error')
        return redirect(url_for('routes.psicologo'))

    if 'foto' not in request.files:
        flash('Nenhum arquivo de foto enviado.', category='error')
        return redirect(url_for('routes.ver_registros_paciente', paciente_id=paciente.id))

    file = request.files['foto']

    if file.filename == '':
        flash('Nenhum arquivo selecionado.', category='error')
        return redirect(url_for('routes.ver_registros_paciente', paciente_id=paciente.id))

    if file and allowed_file(file.filename):
        if paciente.foto_perfil and paciente.foto_perfil != 'default.jpg':
            old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], paciente.foto_perfil)
            if os.path.exists(old_filepath):
                os.remove(old_filepath)

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{paciente.id}_psicologo_{current_user.id}_{timestamp}_{filename}" 

        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        paciente.foto_perfil = filename
        db.session.commit()
        flash('Foto de perfil do paciente atualizada com sucesso!', category='success')
    else:
        flash('Tipo de arquivo não permitido.', category='error')

    return redirect(url_for('routes.ver_registros_paciente', paciente_id=paciente.id))


@routes.route('/psicologo/adicionar_paciente', methods=['POST'])
@login_required
def adicionar_paciente_web(): # Renomeado para evitar conflito com script
    if current_user.tipo != 'psicologo':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))

    nome = request.form.get('nome')
    email = request.form.get('email')
    password = request.form.get('password')

    if not nome or not email or not password:
        flash('Nome, email e senha são obrigatórios para o novo paciente.', category='error')
        return redirect(url_for('routes.psicologo'))

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Já existe um usuário (seja paciente ou psicólogo) com este email.', category='error')
        return redirect(url_for('routes.psicologo'))

    try:
        new_paciente_user = User(
            email=email,
            tipo='paciente'
        )
        new_paciente_user.set_password(password)
        db.session.add(new_paciente_user)
        db.session.commit()

        new_paciente_profile = Paciente(
            id=new_paciente_user.id,
            nome=nome,
            psicologo_id=current_user.id
        )
        db.session.add(new_paciente_profile)
        db.session.commit()

        flash(f'Paciente "{nome}" adicionado com sucesso e usuário criado!', category='success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao adicionar paciente: {e}', category='error')

    return redirect(url_for('routes.psicologo'))
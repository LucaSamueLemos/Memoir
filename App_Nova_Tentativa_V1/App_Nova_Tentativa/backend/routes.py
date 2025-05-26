from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from .models import User, Paciente, RegistroEmocao, RespostaQuestionario
from . import db
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename # Importe para nomes de arquivo seguros
import os # Importe o módulo os

# Lembre-se de importar allowed_file do __init__ ou duplicar a função aqui
# Por simplicidade, vamos duplicar (ou você pode mover allowed_file para um utils.py e importar de lá)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

routes = Blueprint('routes', __name__)

# backend/routes.py

# ... (imports e outras rotas) ...

@routes.route('/paciente/<int:paciente_id>/upload_foto', methods=['POST'])
@login_required
def upload_foto_paciente(paciente_id):
    if current_user.tipo != 'psicologo':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))

    paciente = Paciente.query.filter_by(id=paciente_id, psicologo_id=current_user.id).first()
    if not paciente:
        flash('Paciente não encontrado ou não associado a você.', category='error')
        return redirect(url_for('routes.psicologo'))

    if 'foto' not in request.files:
        flash('Nenhum arquivo de foto enviado.', category='error')
        return redirect(url_for('routes.ver_registros_paciente', paciente_id=paciente_id))

    file = request.files['foto']

    if file.filename == '':
        flash('Nenhum arquivo selecionado.', category='error')
        return redirect(url_for('routes.ver_registros_paciente', paciente_id=paciente_id))

    if file and allowed_file(file.filename):
        # Opcional: Remover a foto antiga se houver (para evitar acúmulo de arquivos)
        # if paciente.foto_perfil and paciente.foto_perfil != 'default.jpg':
        #     old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], paciente.foto_perfil)
        #     if os.path.exists(old_filepath):
        #         os.remove(old_filepath)

        filename = secure_filename(file.filename)
        # Para evitar problemas com nomes de arquivo duplicados, podemos adicionar um timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{paciente_id}_{timestamp}_{filename}" # Ex: 1_20231027153045_minhafoto.jpg

        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Atualiza o nome do arquivo no banco de dados do paciente
        paciente.foto_perfil = filename
        db.session.commit()
        flash('Foto de perfil atualizada com sucesso!', category='success')
    else:
        flash('Tipo de arquivo não permitido.', category='error')

    # Este redirecionamento DEVE recarregar a página com a nova foto
    return redirect(url_for('routes.ver_registros_paciente', paciente_id=paciente_id))


@routes.route('/', methods=['GET', 'POST'])
def login():
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
    return render_template('paciente.html')

@routes.route('/registrar_emocao', methods=['POST'])
@login_required
def registrar_emocao():
    if current_user.tipo == 'paciente':
        emocao = request.form.get('emocao')
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

    # Coleta os dados do formulário
    humor_geral_str = request.form.get('humor_geral')
    sentimento_principal = request.form.get('sentimento_principal')
    dormiu_bem_str = request.form.get('dormiu_bem')
    motivacao_tarefas_str = request.form.get('motivacao_tarefas')
    causa_estresse = request.form.get('causa_estresse')

    # Inicializa as variáveis com None ou um valor padrão para que sempre existam
    humor_geral = None
    dormiu_bem = None
    motivacao_tarefas = None

    try:
        # Tenta converter os valores
        if humor_geral_str:
            humor_geral = int(humor_geral_str)
        
        # O padrão para radio buttons que não são selecionados é não enviar nada
        # Então, se a string não for 'True' ou 'False', será None
        if dormiu_bem_str is not None:
            dormiu_bem = (dormiu_bem_str == 'True') # Isso já converte para True/False boolean
        
        if motivacao_tarefas_str is not None:
            motivacao_tarefas = (motivacao_tarefas_str == 'True') # Isso já converte para True/False boolean

        # Cria uma nova instância de RespostaQuestionario APENAS SE AS CONVERSÕES FOREM BEM SUCEDIDAS
        nova_resposta = RespostaQuestionario(
            humor_geral=humor_geral,
            sentimento_principal=sentimento_principal,
            dormiu_bem=dormiu_bem,
            motivacao_tarefas=motivacao_tarefas,
            causa_estresse=causa_estresse,
            paciente_id=current_user.id
        )

        # Adiciona e salva no banco de dados
        db.session.add(nova_resposta)
        db.session.commit()

        flash('Questionário respondido com sucesso!', category='success')
        return redirect(url_for('routes.paciente'))

    except ValueError:
        # Se houver um erro de conversão (ex: texto onde esperava número)
        flash('Valores inválidos para humor ou perguntas Sim/Não. Por favor, verifique suas respostas.', category='error')
        return redirect(url_for('routes.paciente'))
    except Exception as e:
        # Captura outras exceções inesperadas
        db.session.rollback() # Desfaz qualquer mudança pendente no banco de dados
        flash(f'Ocorreu um erro inesperado ao salvar o questionário: {e}', category='error')
        return redirect(url_for('routes.paciente'))


@routes.route('/psicologo')
@login_required
def psicologo():
    if current_user.tipo != 'psicologo':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))
    pacientes = Paciente.query.filter_by(psicologo_id=current_user.id).all()
    return render_template('psicologo.html', pacientes=pacientes)

@routes.route('/paciente/<int:paciente_id>/registros')
@login_required
def ver_registros_paciente(paciente_id):
    if current_user.tipo != 'psicologo':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))

    paciente = Paciente.query.filter_by(id=paciente_id, psicologo_id=current_user.id).first()

    if not paciente:
        flash('Paciente não encontrado ou não associado a você.', category='error')
        return redirect(url_for('routes.psicologo'))

    registros_emocoes = RegistroEmocao.query.filter_by(paciente_id=paciente_id).order_by(RegistroEmocao.data_registro.desc()).all()
    
    # NOVO: Busca as respostas do questionário para este paciente
    respostas_questionario = RespostaQuestionario.query.filter_by(paciente_id=paciente_id).order_by(RespostaQuestionario.data_resposta.desc()).all()

    return render_template(
        'registros_paciente.html', 
        paciente=paciente, 
        registros_emocoes=registros_emocoes,
        respostas_questionario=respostas_questionario # NOVO: Passando as respostas para o template
    )

# New route to add a patient by psychologist
@routes.route('/adicionar_paciente', methods=['POST'])
@login_required
def adicionar_paciente():
    if current_user.tipo != 'psicologo':
        flash('Acesso não autorizado.', category='error')
        return redirect(url_for('routes.login'))

    nome = request.form.get('nome')
    email = request.form.get('email')

    if not nome or not email:
        flash('Nome e email são obrigatórios.', category='error')
        return redirect(url_for('routes.psicologo'))

    # Check if patient with email already exists
    existing_paciente = Paciente.query.filter_by(email=email).first()
    if existing_paciente:
        flash('Paciente com este email já existe.', category='error')
        return redirect(url_for('routes.psicologo'))

    novo_paciente = Paciente(nome=nome, email=email, psicologo_id=current_user.id)
    db.session.add(novo_paciente)
    db.session.commit()

    flash('Paciente adicionado com sucesso!', category='success')
    return redirect(url_for('routes.psicologo'))

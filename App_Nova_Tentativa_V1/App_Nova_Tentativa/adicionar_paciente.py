# adicionar_paciente.py
from backend import create_app, db
from backend.models import User, Paciente

app = create_app()

with app.app_context():
    # 1. Encontrar o ID do psicólogo e do paciente
    psicologo_user = User.query.filter_by(email='psicologo@email.com').first()
    paciente_user = User.query.filter_by(email='paciente@email.com').first()

    if not psicologo_user:
        print("Erro: Usuário psicólogo não encontrado. Execute 'criar_usuarios.py' primeiro.")
    if not paciente_user:
        print("Erro: Usuário paciente não encontrado. Execute 'criar_usuarios.py' primeiro.")

    if psicologo_user and paciente_user:
        # Verifica se já existe um paciente com este email para evitar duplicatas
        existing_paciente_record = Paciente.query.filter_by(email=paciente_user.email).first()

        if existing_paciente_record:
            # Se o paciente já existe na tabela Paciente, atualiza o psicologo_id
            if existing_paciente_record.psicologo_id != psicologo_user.id:
                existing_paciente_record.psicologo_id = psicologo_user.id
                db.session.commit()
                print(f"Paciente '{paciente_user.email}' já existe, psicólogo associado atualizado.")
            else:
                print(f"Paciente '{paciente_user.email}' já existe e já está associado ao psicólogo.")
        else:
            # 2. Criar um novo registro na tabela Paciente
            novo_paciente_record = Paciente(
                nome="Paciente Teste",  # Um nome genérico para o paciente
                email=paciente_user.email,
                psicologo_id=psicologo_user.id
            )
            db.session.add(novo_paciente_record)
            db.session.commit()
            print(f"Paciente '{novo_paciente_record.nome}' adicionado e associado ao psicólogo '{psicologo_user.email}'.")
    else:
        print("Não foi possível continuar. Verifique os usuários psicólogo e paciente.")
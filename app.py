import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)

# Configuração do Banco SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# MODELO PARA JOGOS SALVOS (EM ANDAMENTO)
class Torneio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    qtd_participantes = db.Column(db.Integer)
    data_inicio = db.Column(db.DateTime, default=datetime.now)
    # Vamos salvar os dados dos jogos e players como texto (JSON) para simplificar
    dados_json = db.Column(db.Text, nullable=False) 

# MODELO PARA O HISTÓRICO
class Historico(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    qtd_participantes = db.Column(db.Integer)
    data_inicio = db.Column(db.DateTime)
    data_fim = db.Column(db.DateTime, default=datetime.now)
    campeao = db.Column(db.String(100))

# Cria o banco de dados se não existir
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    # Tela principal (index.html)
    return render_template('index.html')

@app.route('/novo_jogo')
def novo_jogo():
    # Agora a tela de opções (Original vs Montar) é o novo_jogo.html
    return render_template('novo_jogo.html')

@app.route('/modo_original')
def modo_original():
    # Esta rota carrega a tela de configuração do torneio
    return render_template('modo_original.html')

@app.route('/iniciar_torneio', methods=['POST'])
def iniciar_torneio():
    nome_torneio = request.form.get('nome_torneio')
    qtd = int(request.form.get('qtd_players'))
    formato = request.form.get('formato') # 'liga_ida' ou 'liga_ida_volta'
    
    players = []
    for i in range(1, qtd + 1):
        players.append({
            'nome': request.form.get(f'p{i}_nome'),
            'time': request.form.get(f'p{i}_time')
        })

    # Gerar Jogos (Round Robin)
    jogos = []
    lista_indices = list(range(qtd))
    if qtd % 2 != 0:
        lista_indices.append(None) # Bye week se for ímpar
    
    n = len(lista_indices)
    for rodada in range(n - 1):
        for i in range(n // 2):
            p1_idx = lista_indices[i]
            p2_idx = lista_indices[n - 1 - i]
            if p1_idx is not None and p2_idx is not None:
                jogos.append({'home': players[p1_idx], 'away': players[p2_idx], 'rodada': rodada + 1})
        lista_indices.insert(1, lista_indices.pop())

    # Se for ida e volta, duplicamos invertendo mando
    if formato == 'liga_ida_volta':
        jogos_volta = []
        for jogo in jogos:
            jogos_volta.append({'home': jogo['away'], 'away': jogo['home'], 'rodada': jogo['rodada'] + (n-1)})
        jogos += jogos_volta

    # No final da rota iniciar_torneio:
    return render_template('liga.html', torneio=nome_torneio, players=players, jogos=jogos, carregado=False)

@app.route('/salvar_torneio', methods=['POST'])
def salvar_torneio():
    dados = request.get_json()
    
    # Se for finalização, move para o histórico e apaga do "em andamento"
    if dados.get('finalizado'):
        novo_h = Historico(
            nome=dados['torneio'],
            qtd_participantes=dados['qtd'],
            data_inicio=datetime.now(), # Aqui você poderia buscar a data real do início
            campeao=dados['campeao']
        )
        db.session.add(novo_h)
    else:
        # Lógica de Salvar Jogo em Andamento
        novo_t = Torneio(
            nome=dados['torneio'],
            qtd_participantes=dados['qtd'],
            dados_json=json.dumps(dados) # Salva tudo (placares, nomes, etc)
        )
        db.session.add(novo_t)
    
    db.session.commit()
    return jsonify({"status": "sucesso"})

@app.route('/jogos_salvos')
def jogos_salvos():
    torneios = Torneio.query.all()
    return render_template('jogos_salvos.html', torneios=torneios)

@app.route('/historico')
def historico():
    logs = Historico.query.all()
    return render_template('historico.html', logs=logs)

@app.route('/carregar_torneio/<int:id>')
def carregar_torneio(id):
    t = Torneio.query.get_or_404(id)
    dados = json.loads(t.dados_json)
    
    # Renderizamos a liga.html passando os dados que estavam salvos no JSON
    return render_template('liga.html', 
                           torneio=t.nome, 
                           players=dados['players'], 
                           jogos=dados['jogos'],
                           carregado=True) # Flag para o JS saber que é um jogo antigo

@app.route('/excluir_torneio/<int:id>', methods=['POST'])
def excluir_torneio(id):
    t = Torneio.query.get_or_404(id)
    db.session.delete(t)
    db.session.commit()
    return redirect(url_for('jogos_salvos'))

if __name__ == '__main__':
    app.run(debug=True)
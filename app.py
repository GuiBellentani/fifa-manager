from flask import Flask, render_template, request, url_for

app = Flask(__name__)

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

    return render_template('liga.html', torneio=nome_torneio, players=players, jogos=jogos)

@app.route('/salvar_historico', methods=['POST'])
def salvar_historico():
    # Aqui o Python receberia os dados do JSON via JavaScript (fetch)
    # E salvaria no SQLite ou em um arquivo JSON
    return {"status": "sucesso"}

if __name__ == '__main__':
    app.run(debug=True)
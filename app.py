from flask import Flask, render_template, request, redirect, url_for
import requests
from bs4 import BeautifulSoup
import sqlite3
import datetime

app = Flask(__name__)
sites_pre_salvos = []  # Lista de sites pré-salvos

# Função para realizar a raspagem dos links de um site
def obter_links(url):
    resposta = requests.get(url)
    if resposta.status_code == 200:
        soup = BeautifulSoup(resposta.text, 'html.parser')
        links = soup.find_all('a')
        urls = [link.get('href') for link in links if link.get('href')]
        return urls
    else:
        return []

# Função para salvar os links no banco de dados com a data e hora
# Função para salvar os links no banco de dados com a data e hora
def salvar_links_bd(links):
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    # Verifica se a tabela já existe, se não, cria
    c.execute('''CREATE TABLE IF NOT EXISTS links (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, data_hora TEXT)''')
    # Usando uma transação para inserir os links
    try:
        conn.execute("BEGIN TRANSACTION")
        data_hora_atual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for link in links:
            # Verifica se o link já existe no banco de dados
            c.execute("SELECT * FROM links WHERE url=?", (link,))
            result = c.fetchone()
            if not result:  # Se o link não existir, insere-o no banco de dados
                # Verifica se a URL começa com 'http://' ou 'https://'
                if not link.startswith('http://') and not link.startswith('https://'):
                    link = 'https://' + link
                c.execute("INSERT INTO links (url, data_hora) VALUES (?, ?)", (link, data_hora_atual))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()



# Função para obter os links salvos do banco de dados
def obter_links_bd():
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    c.execute("SELECT * FROM links")
    rows = c.fetchall()
    conn.close()
    return rows

# Rota para a página inicial
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        all_links = []
        for url in sites_pre_salvos:
            links = obter_links(url)
            all_links.extend(links)
        salvar_links_bd(all_links)
        return redirect(url_for('mostrar_links'))
    return render_template('index.html', sites_pre_salvos=sites_pre_salvos)

# Rota para a pagina pre salvos
@app.route('/gerenciar_presalvos', methods=['GET', 'POST'])
def gerenciar_presalvos():
    if request.method == 'POST':
        all_links = []
        for url in sites_pre_salvos:
            links = obter_links(url)
            all_links.extend(links)
        salvar_links_bd(all_links)
        return redirect(url_for('gerenciar_presalvos'))
    return render_template('gerenciar_presalvos.html', sites_pre_salvos=sites_pre_salvos)

# Rota para a página de links salvos
@app.route('/links')
def mostrar_links():
    links = obter_links_bd()
    return render_template('mostrar_links.html', links=links)

# Rota para adicionar um novo site pré-salvo
@app.route('/adicionar_site', methods=['POST'])
def adicionar_site():
    novo_site = request.form['novo_site']
    sites_pre_salvos.append(novo_site)
    return redirect(url_for('index'))

# Rota para remover um site pré-salvo
@app.route('/remover_site', methods=['POST'])
def remover_site():
    site_a_remover = request.form['site_a_remover']
    sites_pre_salvos.remove(site_a_remover)
    return redirect(url_for('index'))

# Função para obter os pré-salvos do banco de dados
def obter_presalvos():
    conn = sqlite3.connect('sites_pre_salvos.db')
    c = conn.cursor()
    # Verifica se a tabela já existe, se não, cria
    c.execute("CREATE TABLE IF NOT EXISTS sites_pre_salvos (id INTEGER PRIMARY KEY AUTOINCREMENT, site TEXT)")
    c.execute("SELECT * FROM sites_pre_salvos")
    presalvos = c.fetchall()
    conn.close()
    return [presalvo[1] for presalvo in presalvos]  # Retorna apenas os sites, não os IDs


# Atualizar a lista de sites pré-salvos ao iniciar o aplicativo
sites_pre_salvos = obter_presalvos()



# Rota para adicionar um novo pré-salvo
@app.route('/adicionar_presalvo', methods=['POST'])
def adicionar_presalvo():
    novo_presalvo = request.form['novo_presalvo']
    conn = sqlite3.connect('sites_pre_salvos.db')
    c = conn.cursor()
    c.execute("INSERT INTO sites_pre_salvos (site) VALUES (?)", (novo_presalvo,))
    conn.commit()
    conn.close()
    return redirect(url_for('gerenciar_presalvos'))

# Rota para editar um pré-salvo
@app.route('/editar_presalvo/<int:id>', methods=['POST'])
def editar_presalvo(id):
    novo_site = request.form['novo_site']
    conn = sqlite3.connect('sites_pre_salvos.db')
    c = conn.cursor()
    c.execute("UPDATE sites_pre_salvos SET site = ? WHERE id = ?", (novo_site, id))
    conn.commit()
    conn.close()
    return redirect(url_for('gerenciar_presalvos'))

# Rota para remover um pré-salvo
@app.route('/remover_presalvo/<int:id>', methods=['POST'])
def remover_presalvo(id):
    conn = sqlite3.connect('sites_pre_salvos.db')
    c = conn.cursor()
    c.execute("DELETE FROM sites_pre_salvos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('gerenciar_presalvos'))


if __name__ == '__main__':
    app.run(debug=True)

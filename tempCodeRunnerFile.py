from flask import Flask, render_template, request, redirect, url_for
import requests
from bs4 import BeautifulSoup
import sqlite3
import datetime
import os

app = Flask(__name__)

# Função para realizar a raspagem dos links de um site
def obter_links(url):
    try:
        resposta = requests.get(url)
        if resposta.status_code == 200:
            soup = BeautifulSoup(resposta.text, 'html.parser')
            links = soup.find_all('a')
            urls = [link.get('href') for link in links if link.get('href')]
            return urls
        else:
            return []
    except requests.exceptions.RequestException:
        return []

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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sites_pre_salvos = obter_sites_pre_salvos()
        for site in sites_pre_salvos:
            salvar_links_bd(obter_links(site))
        return redirect(url_for('mostrar_links'))
    return render_template('index.html', sites_pre_salvos=obter_sites_pre_salvos())



# Função para obter os sites pré-salvos do banco de dados
def obter_sites_pre_salvos():
    if not os.path.exists('sites_pre_salvos.db'):
        conn = sqlite3.connect('sites_pre_salvos.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE sites (id INTEGER PRIMARY KEY AUTOINCREMENT, site TEXT)''')
        conn.commit()
        conn.close()
    conn = sqlite3.connect('sites_pre_salvos.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sites")
    rows = c.fetchall()
    conn.close()
    return [row[1] for row in rows]

# Rota para a página de links salvos
@app.route('/links')
def mostrar_links():
    links = obter_links_bd()
    return render_template('mostrar_links.html', links=links)

# Rota para a página princippais
@app.route('/principais')
def principais():
    links = obter_links_bd()
    return render_template('principais.html', links=links)

# Rota para adicionar um novo site pré-salvo
@app.route('/adicionar_site', methods=['POST'])
def adicionar_site():
    novo_site = request.form['novo_site']
    conn = sqlite3.connect('sites_pre_salvos.db')
    c = conn.cursor()
    c.execute("INSERT INTO sites (site) VALUES (?)", (novo_site,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Rota para remover um site pré-salvo
@app.route('/remover_site', methods=['POST'])
def remover_site():
    site_a_remover = request.form['site_a_remover']
    conn = sqlite3.connect('sites_pre_salvos.db')
    c = conn.cursor()
    c.execute("DELETE FROM sites WHERE site=?", (site_a_remover,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

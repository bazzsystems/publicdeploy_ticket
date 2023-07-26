import time
import threading
import sqlite3
import re
from flask import Flask, render_template, request, redirect, url_for, g
import requests
from bs4 import BeautifulSoup
import os

TARGET_URL = 'https://officetv.atarix.co.il/showSmart5.php'
HEADERS = ["מזהה", "תאריך", "שעה", "לקוח", "סוג", "תיאור", "שם", "טלפון", "זמן המתנה"]

data_cache = []
data_lock = threading.Lock()

app = Flask(__name__)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('sites.db')
    return db

@app.before_request
def before_request():
    g.db = get_db()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def update_data():
    while True:
        source = requests.get(TARGET_URL).text
        soup = BeautifulSoup(source, 'html.parser')
        table = soup.find('table')
        data = []

        if table is not None:
            rows = table.find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                row_data = [cell.get_text() for cell in cells if cell.get_text() != '']
                if len(row_data) > 0:
                    data.append(row_data)

        with data_lock:
            data_cache[:] = data
        time.sleep(3)

@app.route('/')
def home():
    with data_lock:
        data = list(data_cache)
    return render_template('index.html', headers=HEADERS, data=data)

@app.route('/search', methods=['POST'])
def search():
    search_text = request.form.get('search_text')
    with data_lock:
        data = [row for row in data_cache if any(search_text.lower() in cell.lower() for cell in row)]
    return render_template('index.html', headers=HEADERS, data=data, search_text=search_text)

@app.route('/close/<client_name>')
def close(client_name):
    cursor = g.db.cursor()
    processed_client_name = re.sub(r'\([^()]*\)', '', client_name).strip()
    cursor.execute("SELECT url FROM sites WHERE name = ?", (processed_client_name,))
    result = cursor.fetchone()
    if result is not None:
        url = result[0]
        system_link = f"https://{url}/manager/Manager.php?Table=1&Contant=support_requests&m=217&s=250"
        return redirect(system_link)
    else:
        return "Client not found in the database.", 404

@app.route('/open/<client_name>')
def open_system(client_name):
    cursor = g.db.cursor()
    processed_client_name = re.sub(r'\([^()]*\)', '', client_name).strip()
    cursor.execute("SELECT url FROM sites WHERE name = ?", (processed_client_name,))
    result = cursor.fetchone()
    if result is not None:
        url = result[0]
        system_link = f"https://{url}/manager/Manager.php"
        return redirect(system_link)
    else:
        return "Client not found in the database.", 404

if __name__ == "__main__":

    update_thread = threading.Thread(target=update_data)
    update_thread.start()

    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        print("Application stopped")

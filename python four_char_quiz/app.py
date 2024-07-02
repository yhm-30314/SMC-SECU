from flask import Flask, request, render_template, redirect, url_for, session
import random
import sqlite3
import os
import datetime

app = Flask(__name__)
app.secret_key = os.urandom(32)

DATABASE = "scores.db"
PROVERBS_FILE = 'static/사자성어.txt'

# 파일 읽기
with open(PROVERBS_FILE, 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 사자성어와 설명을 분리하여 저장
proverbs = {}
for line in lines:
    parts = line.strip().split(':')
    if len(parts) == 2:
        proverbs[parts[0].strip()] = parts[1].strip()

# 데이터베이스 설정
conn = sqlite3.connect(DATABASE)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    name TEXT, 
    score INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()
conn.close()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_quiz(proverbs, num_choices=5):
    correct_answer = random.choice(list(proverbs.keys()))
    choices = random.sample(list(proverbs.keys()), num_choices - 1)
    if correct_answer not in choices:
        choices.append(correct_answer)
    random.shuffle(choices)
    return proverbs[correct_answer], choices, correct_answer

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    username = request.form['username']
    session['username'] = username
    session['score'] = 0
    session['correct'] = True
    return redirect(url_for('quiz'))

@app.route('/quiz')
def quiz():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    description, choices, correct_answer = create_quiz(proverbs)
    session['description'] = description
    session['choices'] = choices
    session['correct_answer'] = correct_answer

    return render_template('quiz.html', description=description, choices=choices)

@app.route('/answer', methods=['POST'])
def answer():
    user_answer = request.form['choice']
    correct_answer = session['correct_answer']
    username = session['username']
    
    correct = user_answer == correct_answer
    session['correct'] = correct
    
    if correct:
        session['score'] += 1
        return redirect(url_for('quiz'))
    else:
        return redirect(url_for('finish'))

@app.route('/finish')
def finish():
    username = session.get('username')
    score = session.get('score', 0)

    if username and score > 0:
        # 현재 시각을 날짜 형식으로 저장
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 스코어 데이터베이스에 저장
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO scores (name, score, timestamp) VALUES (?, ?, ?)", (username, score, current_time))
        conn.commit()

        # 모든 스코어 출력
        all_scores = c.execute("SELECT name, score, timestamp FROM scores WHERE name != 'unknown' AND score != 0").fetchall()
        highest_score = c.execute("SELECT name, score, timestamp FROM scores WHERE name != 'unknown' AND score != 0 ORDER BY score DESC LIMIT 1").fetchone()
        conn.close()
    else:
        all_scores = []
        highest_score = None

    # 세션 초기화
    session.pop('username', None)
    session.pop('score', None)
    session.pop('correct', None)
    session.pop('description', None)
    session.pop('choices', None)
    session.pop('correct_answer', None)

    return render_template('finish.html', username=username, score=score, all_scores=all_scores, highest_score=highest_score)

@app.route('/show_scores')
def show_scores():
    conn = get_db()
    c = conn.cursor()
    all_scores = c.execute("SELECT name, score, timestamp FROM scores").fetchall()
    conn.close()
    return render_template('show_scores.html', all_scores=all_scores)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100, debug=True)

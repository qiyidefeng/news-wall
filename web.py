import sqlite3
from flask import Flask
from flask import render_template
from flask import g

#import sys
#reload(sys)
#sys.setdefaultencoding('utf8')


app = Flask(__name__)

@app.before_request
def before_request():
    g.db = sqlite3.connect('data.db')

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def home():
    results = query_db('select * from news')
    results = results[::-1]
    dates = {new['downtime'] for new in results}
    latest = max(dates)
    return render_template('index.html', news=results, latest=latest)

@app.route('/latest')
def latest():
    results = query_db('select * from news')
    results = results[::-1]
    dates = {new['downtime'] for new in results}
    latest = max(dates)
    flts = [new for new in results if new['downtime']==latest]
    return render_template('index.html', news=flts, latest=latest)

if __name__=='__main__':
    app.run(debug=True)

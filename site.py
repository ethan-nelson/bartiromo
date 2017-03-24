#!/home/enelson/flaskenv/bin/python
from flask import Flask
from flask import *
from flask.ext.login import *
from flask.ext.sqlalchemy import SQLAlchemy
import mysql as sql
import mysql.connector as sqlconn
from flask_wtf import FlaskForm
from wtforms import *

app = Flask(__name__)


config = {
  'user': 'micro',
  'password': 'micro',
  'host': 'localhost',
  'database': 'micro',
}


conn = sqlconn.connect(**config)
cursor = conn.cursor()
get_new = ("SELECT url, id FROM image ORDER BY RAND() LIMIT 1;")
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://'+config['user']+':'+config['password']+'@'+config['host']+'/'+config['database']
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80),unique=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(64))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.username

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(120))

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Integer, db.ForeignKey('image.id'))
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    vote = db.Column(db.Integer)



#test_user = User(username="test",password="test",email="test")
#db.create_all()
#db.session.add(test_user)
#db.session.commit()

class LoginForm(FlaskForm):
    username = TextField(u'Username', validators=[validators.input_required()])
    password = PasswordField(u'Password', validators=[validators.input_required()])

    def get_user(self):
        return db.session.query(User).filter_by(username=self.username.data).first()


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = form.get_user()
        login_user(user)

        flash('Logged in successfully.')

        return redirect(url_for('home'))
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/',methods=['GET','POST'])
def home():
    data = {}
    cursor = conn.cursor()

    if request.method == 'POST':
        form = request.form

        vote = Vote(image=form['url'],vote=form['vote'], user=current_user.id)
        db.session.add(vote)
        db.session.commit()

    cursor.execute(get_new)
    data['url'], data['id'] = cursor.fetchone()

    return render_template('index.html', data=data)


@app.route('/select',methods=['GET','POST'])
def select():
    data = {}
    cursor = conn.cursor()

    if request.method == 'POST':
        form = request.form

        vote = Vote(image=form['url'],vote=form['vote'], user=current_user.id)
        db.session.add(vote)
        db.session.commit()


    cursor.execute(get_new)
    data['url'], data['id'] = cursor.fetchone()[0]

    return render_template('selectjs.html', data=data)


@app.route('/admin')
def admin():
    data = {}
    cursor = conn.cursor()

    cursor.execute('SELECT image,vote,count(*) FROM vote group by image, vote;')
    data['data'] = cursor.fetchall()

    return render_template('admin.html', data=data)


if __name__ == '__main__':
    app.debug = True
    app.config['SECRET_KEY'] = 'itsatrap'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://'+config['user']+':'+config['password']+'@'+config['host']+'/'+config['database']
    app.run(host='0.0.0.0',port=5432)

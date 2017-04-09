#!/home/enelson/flaskenv/bin/python
from flask import Flask
from flask import *
from flask.ext.login import *
from flask.ext.sqlalchemy import SQLAlchemy
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
get_new = ("SELECT url, id FROM tasks ORDER BY RAND() LIMIT 1;")
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + \
                                        config['user'] + ':' + \
                                        config['password'] + '@' + \
                                        config['host'] + '/' + \
                                        config['database']
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


###############################################################################
###   DATABASE CLASSES                                                      ###
###############################################################################
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(64))
    admin = db.Column(db.Boolean,default=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_admin(self):
        return admin

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.username


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    url = db.Column(db.String(120))


class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    result = db.Column(db.Integer)


###############################################################################
###   FORM CLASSES                                                          ###
###############################################################################
class LoginForm(FlaskForm):
    username = TextField(u'Username',
                         validators=[validators.input_required()])
    password = PasswordField(u'Password',
                             validators=[validators.input_required()])

    def get_user(self):
        return db.session \
                    .query(User) \
                    .filter_by(username=self.username.data) \
                    .first()

    def validate(self):
        user = self.get_user()

        if not user:
            flash('Unsuccessful username. Try again or <a href="/register">register</a>.')
            return False
        if not user.password == self.password.data:
            flash('Unsuccessful password. Try again.')
            return False
        return True


class RegisterForm(FlaskForm):
    username = TextField(u'Username',
                         validators=[validators.input_required()])
    password = PasswordField(u'Password',
                             validators=[validators.input_required()])
    email = TextField(u'Email address')


class CreateForm(FlaskForm):
    name = TextField(u'Name')
    url = TextField(u'url')


###############################################################################
###   PAGE MODELS                                                           ###
###############################################################################
@app.route('/')
def home():
    projects = Project.query.all()
    return render_template('index.html', projects=projects)


@app.route('/login/', methods=['GET', 'POST'])
@login_manager.unauthorized_handler
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = form.get_user()

        if user:
            login_user(user)

            if current_user.is_authenticated():
                flash('Logged in successfully.')

                return redirect(url_for('home'))
        return render_template('login.html', form=form)
    return render_template('login.html', form=form)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,
                    password=form.password.data,
                    email=form.email.data)

        db.session.add(user)
        db.session.commit()

        login_user(user)

        flash('Thanks for registering!')

        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/logout/', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/user/', methods=['GET'])
@login_required
def user_profile():
    data = Result.query.filter(Result.user == current_user.id).count()

    return render_template('user.html', data=data)


@app.route('/leaderboard/', methods=['GET'])
def leaderboard():
    cursor = conn.cursor()
    cursor.execute('SELECT users.username,count(*) FROM results INNER JOIN users ON results.user=users.id GROUP BY results.user ORDER BY count(*) DESC;')
    data = cursor.fetchall()
    print data
    return render_template('leaderboard.html', projects=['main'], data={'main': [x for x in data]})


@app.route('/project/<int:project_id>/', methods=['GET', 'POST'])
@login_required
def project(project_id):
    data = {}
    cursor = conn.cursor()

    if request.method == 'POST':
        form = request.form

        result = Result(task=form['url'], result=form['vote'], user=current_user.id)
        db.session.add(result)
        db.session.commit()

    cursor.execute(get_new)
    data['url'], data['id'] = cursor.fetchone()

    return render_template('project.html', data=data)


@app.route('/admin/results/<int:project_id>/')
@login_required
def results(project_id):
    if not current_user.admin:
        flash('Sorry, you do not have permission to do that.')
        return render_template('index.html')
    data = {}
    cursor = conn.cursor()
    cursor.execute('SELECT tasks.url,count(*) FROM results INNER JOIN tasks WHERE tasks.project_id=%s GROUP BY results.task;' % (project_id,))
    data['data'] = cursor.fetchall()
    print data
    return render_template('results.html', data=data)


@app.route('/admin/create/', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.admin:
        flash('Sorry, you do not have permission to do that.')
        return render_template('index.html')
    form = CreateForm()
    if request.method == 'POST':
        project = Project(name=form.name.data)

        db.session.add(project)
        db.session.commit()
        task = Task(project_id=project.id, url=form.url.data)
        db.session.add(task)
        db.session.commit()

        flash('Project created!')

        return redirect(url_for('admin'))
    return render_template('create.html', form=form)


@app.route('/select', methods=['GET', 'POST'])
def select():
    data = {}
    cursor = conn.cursor()

    if request.method == 'POST':
        form = request.form

        vote = Vote(url=form['url'], vote=form['vote'], user=current_user.id)
        db.session.add(vote)
        db.session.commit()

    cursor.execute(get_new)
    data['url'], data['id'] = cursor.fetchone()[0]

    return render_template('selectjs.html', data=data)


@app.route('/admin/')
def admin():
    projects = Project.query.all()
 
    return render_template('admin.html', projects=projects)


if __name__ == '__main__':
    app.debug = True
    app.config['SECRET_KEY'] = 'itsatrap'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + \
                                            config['user'] + ':' + \
                                            config['password'] + '@' + \
                                            config['host'] + '/' + \
                                            config['database']
    app.run(host='0.0.0.0', port=5432)

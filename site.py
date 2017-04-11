#!/home/enelson/flaskenv/bin/python
from flask import Flask
from flask import *
from flask.ext.login import *
from flask.ext.sqlalchemy import SQLAlchemy
import mysql.connector as sqlconn
from flask_wtf import FlaskForm
from wtforms import *


config = {
  'user': 'micro',
  'password': 'micro',
  'host': 'localhost',
  'database': 'micro',
}


conn = sqlconn.connect(**config)
cursor = conn.cursor()


###########################################################################
#   APP HANDLER                                                           #
###########################################################################
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + \
                                        config['user'] + ':' + \
                                        config['password'] + '@' + \
                                        config['host'] + '/' + \
                                        config['database']


###########################################################################
#   DATABASE HANDLER                                                      #
###########################################################################
db = SQLAlchemy(app)


###########################################################################
#   LOGIN HANDLER                                                         #
###########################################################################
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


###########################################################################
#   DATABASE CLASSES                                                      #
###########################################################################
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(64))
    admin = db.Column(db.Boolean, default=False)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def is_admin(self):
        return self.admin

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.username


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    instruction = db.Column(db.Text(400))
    description = db.Column(db.Text(1000))


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


###########################################################################
#   FORM CLASSES                                                          #
###########################################################################
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

    def validate(self):
        user = User.query.filter_by(username=self.username.data).count()

        if user != 0:
            flash('That name is already registered. Try a new one.')
            return False
        return True


class CreateForm(FlaskForm):
    name = TextField(u'Give it a name: ')
    instruction = TextField(u'Write the instructions to show on a task: ')

    def validate(self):
        project = Project.query.filter_by(name=self.name.data).count()

        if project != 0:
            flash('That project name already exists. Try a new one.')
            return False
        return True


class AddForm(FlaskForm):
    url = TextAreaField(u'Paste a comma, semicolon, or line return delimited list of urls to add.')


###########################################################################
#   PAGE MODELS                                                           #
###########################################################################
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
    flash('Logged out!')
    return redirect(url_for('home'))


@app.route('/user/', methods=['GET'])
@login_required
def user_profile():
    score = Result.query.filter(Result.user == current_user.id).count()

    return render_template('user.html', score=score)


@app.route('/leaderboard/', methods=['GET'])
def leaderboard():
    cursor = conn.cursor()
    cursor.execute('SELECT users.username,count(*) FROM results INNER JOIN users ON results.user=users.id GROUP BY results.user ORDER BY count(*) DESC;')
    data = cursor.fetchall()
    print data
    return render_template('leaderboard.html',
                           projects=['main'],
                           data={'main': [x for x in data]})


@app.route('/project/<int:project_id>/', methods=['GET', 'POST'])
@login_required
def project(project_id):
    if request.method == 'POST':
        form = request.form

        result = Result(task=form['url'],
                        result=form['vote'],
                        user=current_user.id)
        db.session.add(result)
        db.session.commit()

    project = Project.query.get(project_id)
    data = Task.query.filter_by(project_id=project_id).order_by(db.func.random()).first()

    return render_template('project.html', data=data, project=project)


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
    if form.validate_on_submit():
        project = Project(name=form.name.data, instruction=form.instruction.data)

        db.session.add(project)
        db.session.commit()

        flash('Project created!')

        return redirect('/admin/add/%i/' % (project.id,))
    return render_template('create.html', form=form)


@app.route('/admin/add/<int:project_id>/', methods=['GET', 'POST'])
@login_required
def add(project_id):
    if not current_user.admin:
        flash('Sorry, you do not have permission to do that.')
        return render_template('index.html')
    form = AddForm()
    if request.method == 'POST':
        data = form.url.data
        data = data.replace(',',' ').replace(';',' ').replace('\r\n',' ').replace('\n\r',' ').replace('\n',' ').replace('\r',' ').split()

        urls = db.session.query(Task.url).filter(Task.project_id==project_id).all()
        urls = [x[0] for x in urls]
        print urls
        for url in data:
            if url not in urls:
                db.session.add(Task(project_id=project_id,url=url))
        db.session.commit()

        if len(data) == 0:
            flash('No tasks added.')
        elif len(data) == 1:
            flash('Task added!')
        else:
            flash('Tasks added!')

        return redirect(url_for('admin'))
    return render_template('add.html', form=form, project_id=project_id)


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

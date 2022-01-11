from flask import Flask
from flask import *
from flask.ext.login import *
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.uploads import configure_uploads, IMAGES, UploadSet
from flask_wtf import FlaskForm
from wtforms import *
import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

# Layout:
# - Flask guts
# - Database guts
# - Login guts
# - Upload guts
# - Database definitions
# - Form definitions
# - App views

###########################################################################
#   APP HANDLER                                                           #
###########################################################################
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = 'itsatrap'
if app.config['SQLALCHEMY_DATABASE_URI'] is None:
    raise Exception('Server settings not set in environmental variable `DATABASE_URL`.')

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
#   UPLOAD HANDLER                                                        #
###########################################################################
# Important note: changing this config after uploading some files will
#  require manually changing the existing task definitions to the new URL
#  (or adding a custom app route of the old destination pointing to the new)
app.config['UPLOADS_DEFAULT_DEST'] = 'uploads/'
app.config['UPLOADS_DIRECTORY'] = 'photos'
photo_uploads = UploadSet(app.config['UPLOADS_DIRECTORY'], IMAGES)
configure_uploads(app, photo_uploads)

###########################################################################
#   DATABASE CLASSES                                                      #
###########################################################################
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    pw_hash = db.Column(db.String(300))
    admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, password, email='', admin=False):
        self.username = username
        self.set_password(password)
        self.email = email
        self.admin = admin

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password, method='pbkdf2:sha512:10000',salt_length=128)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

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
    name = db.Column(db.String(100), nullable=False)
    instruction = db.Column(db.String(200))
    description = db.Column(db.Text, default='')
    introduction = db.Column(db.Text, default='')
    hidden = db.Column(db.Boolean, default=False, nullable=False)
    classification_maximum = db.Column(db.Integer)


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    url = db.Column(db.String(200), nullable=False)


class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    project = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    task = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    result = db.Column(db.Integer, nullable=False)


class Introduction(db.Model):
    __tablename__ = 'introduction_completion'
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)


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
        if not check_password_hash(user.pw_hash, self.password.data):
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


class PasswordForm(FlaskForm):
    password = PasswordField(u'New password',
                             validators=[validators.input_required()])
    repeat_password = PasswordField(u'Confirm new password',
                                    validators=[validators.input_required()])

    def validate(self):
        if password != repeat_password:
            flash('Your new password did not match the confirmation. Please try again.')
            return False
        return True


class CreateForm(FlaskForm):
    name = TextField(u'Give it a name :  ',
                     validators=[validators.input_required()])
    description = TextField(u'Write a short description to show on the homepage : ',
                            validators=[validators.input_required()])
    instruction = TextAreaField(u'Write the instructions to show on a task : ',
                                validators=[validators.input_required()])
    introduction = TextAreaField(u'Write a detailed introduction that provides training and examples : ',
                                 validators=[validators.input_required()])
    classification_maximum = IntegerField(u'How many classifications should a task require before it is complete? ',
                                          validators=[validators.input_required()])

    def validate(self):
        project = Project.query.filter_by(name=self.name.data).count()

        if project != 0:
            flash('That project name already exists. Try a new one.')
            return False
        return True


class AddForm(FlaskForm):
    url = TextAreaField(u'Paste a comma, semicolon, or line return delimited list of urls to add.')


class UploadForm(FlaskForm):
    photos = FileField(u'Select files to upload.')


class IntroductionForm(FlaskForm):
    submitted = HiddenField()


###########################################################################
#   PAGE VIEWS                                                            #
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


@app.route('/user/password/', methods=['GET', 'POST'])
@login_required
def user_password():
    form = PasswordForm()
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('user_profile'))
    return render_template('password.html', form=form)


@app.route('/leaderboard/', methods=['GET'])
def leaderboard():
    data = db.session.query(User.username, db.func.count()) \
                     .join(Result, Result.user==User.id) \
                     .group_by(User.username) \
                     .order_by(db.func.count().desc()).all()

    return render_template('leaderboard.html',
                           projects=['main'],
                           data={'main': [x for x in data]})


@app.route('/introduction/<int:project_id>/', methods=['GET', 'POST'])
@login_required
def introduction(project_id):
    if request.method == 'POST':
        #form = IntroductionForm()
        user = User.query.get(current_user.id)
        completion = Introduction.query.filter(Introduction.user==current_user.id, Introduction.project==project_id).first()
        if completion is None:
            completion = Introduction(user=current_user.id, project=project_id)
            db.session.add(completion)
            db.session.commit()

        return redirect(url_for('project', project_id=project_id))

    project = Project.query.get(project_id)

    return render_template('introduction.html', project=project)

@app.route('/project/<int:project_id>/', methods=['GET', 'POST'])
@login_required
def project(project_id):
    if request.method == 'POST':
        form = request.form

        result = Result(task=form['url'],
                        result=form['vote'],
                        project=project_id,
                        user=current_user.id)
        db.session.add(result)
        db.session.commit()

    project = Project.query.get(project_id)

    tasks_user_completed = Result.query.filter(db.and_(Result.user==current_user.id, Result.project==project.id)).with_entities(Result.task).all()
    tasks_user_completed = [x[0] for x in tasks_user_completed]

    counts = Result.query.filter(Result.project==project_id).group_by(Result.task).with_entities(Result.task, db.func.count()).all()
    tasks_done = [x[0] for x in counts if x[1] >= project.classification_maximum]

    data = Task.query.filter(Task.project_id==project_id).filter(Task.id.notin_(tasks_user_completed)).filter(Task.id.notin_(tasks_done)).order_by(db.func.random()).first()

    return render_template('project.html', data=data, project=project)


@app.route('/admin/results/<int:project_id>/')
@login_required
def results(project_id):
    if not current_user.admin:
        flash('Sorry, you do not have permission to do that.')
        return render_template('index.html')
    data = {}
    data['data'] = db.session.query(Task).join(Result,Task.project_id==project_id).group_by(Task.url).with_entities(Task.url, db.func.count()).all()
    return render_template('results.html', data=data)


@app.route('/admin/create/', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.admin:
        flash('Sorry, you do not have permission to do that.')
        return render_template('index.html')
    form = CreateForm()
    if form.validate_on_submit():
        project = Project(name=form.name.data, instruction=form.instruction.data, description=form.description.data, introduction=form.introduction.data, classification_maximum=form.classification_maximum.data)

        db.session.add(project)
        db.session.commit()

        flash('Project created!')

        return redirect(url_for('add', project_id=project.id))
    return render_template('create.html', form=form)


@app.route('/admin/add/<int:project_id>/', methods=['GET', 'POST'])
@login_required
def add(project_id):
    if not current_user.admin:
        flash('Sorry, you do not have permission to do that.')
        return render_template('index.html')
    form = AddForm()
    if request.method == 'POST':
        skipped_files = []; added_files = [];
        data = form.url.data
        data = data.replace(',',' ').replace(';',' ').replace('\r\n',' ').replace('\n\r',' ').replace('\n',' ').replace('\r',' ').split()

        urls = db.session.query(Task.url).filter(Task.project_id==project_id).all()
        urls = [x[0] for x in urls]
        for url in data:
            if url not in urls:
                db.session.add(Task(project_id=project_id,url=url))
                added_files.append(url)
            else:
                skipped_files.append(url)
        db.session.commit()

        if len(data) == 0:
            flash('No tasks added.')
        else:
            flash('Add process completed. %i files added, %i duplicate files skipped.' % (len(added_files), len(skipped_files)))

        return redirect(url_for('admin'))
    return render_template('add.html', form=form, project_id=project_id)


@app.route('/admin/photo/upload/<int:project_id>', methods=['GET', 'POST'])
@login_required
def upload_photo(project_id):
    form = UploadForm()
    if not current_user.admin:
        flash('Sorry, you do not have permission to do that.')
        return render_template('index.html')
    if request.method == 'POST':
        skipped_files = []; uploaded_files = []; added_files = []
        if len(request.files.getlist('photos')) == 1 and request.files.getlist('photos')[0].filename == '':
            flash('No files selected to upload.')
            return redirect(url_for('admin'))
        try:
            existing_files = [x[0] for x in db.session.query(Task.url).filter(project_id==project_id).all()]
            for upload_file in request.files.getlist('photos'):
                if '/%s%s/%i/%s' % (app.config['UPLOADS_DEFAULT_DEST'], app.config['UPLOADS_DIRECTORY'], project_id, upload_file.filename) not in existing_files:
                    filename = photo_uploads.save(upload_file, folder='%s/' % (str(project_id)))
                    uploaded_files.append(filename)
                    db.session.add(Task(project_id=project_id,url='/%s%s/%s' % (app.config['UPLOADS_DEFAULT_DEST'], app.config['UPLOADS_DIRECTORY'], filename)))
                    added_files.append(filename)
                else:
                    skipped_files.append(upload_file)
            db.session.commit()
            flash('Upload process completed. %i files uploaded, %i duplicate files skipped.' % (len(added_files), len(skipped_files)))
        except Exception as e:
            flash('Tasks unable to be added.')
        return redirect(url_for('admin'))

    return render_template('upload.html', project_id=project_id, form=form)


@app.route('/admin/photo/delete/<int:project_id>/<filename>', methods=['POST'])
@login_required
def delete_photo(project_id, filename):
    if not current_user.admin:
        flash('Sorry, you do not have permission to do that.')
        return render_template('index.html')
    try:
        target = os.path.join(app.config['UPLOADS_DEFAULT_DEST'], '%s/%s' % (str(project_id), filename))
        os.remove(target)
    except:
        flash('Could not remove file %s' % (filename,))
    return url_for('results', project_id=project_id)


@app.route('/%s%s/<int:project_id>/<filename>' % (app.config['UPLOADS_DEFAULT_DEST'], app.config['UPLOADS_DIRECTORY']), methods=['GET'])
@login_required
def serve_photo(project_id, filename):
    return send_from_directory('%s%s' % (app.config['UPLOADS_DEFAULT_DEST'], app.config['UPLOADS_DIRECTORY']), '%s/%s' % (str(project_id), filename))


@app.route('/admin/hide/<int:project_id>/', methods=['GET', 'POST'])
@login_required
def hide(project_id):
    if not current_user.admin:
        flash('Sorry you do not have permission to do that.')
        return render_template('index.html')
    project = Project.query.get(project_id)
    project.hidden ^= True
    db.session.add(project)
    db.session.commit()
    return redirect(url_for('admin'))


@app.route('/admin/')
def admin():
    projects = Project.query.all()

    return render_template('admin.html', projects=projects)


def create_database():
    db.create_all()
    admin = User(username="admin",password="micro",admin=True)
    db.session.add(admin)
    db.session.commit()


if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'itsatrap'
    app.run(host='0.0.0.0', port=5432)

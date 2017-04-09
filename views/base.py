from flask import Blueprint
from flask import *
from flask.ext.login import *
from forms import (
  LoginForm,
  RegisterForm,
)
from login import login_manager
from models.base import db
from models.users import User
from models.task import Task
from models.result import Result

base = Blueprint("base", __name__)


@base.route('/')
def home():
    return render_template('index.html')


@base.route('/register', methods=['GET', 'POST'])
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

        return redirect(url_for('base.home'))
    return render_template('register.html', form=form)


@base.route('/login', methods=['GET', 'POST'])
@login_manager.unauthorized_handler
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = form.get_user()

        if user:
            login_user(user)

            if current_user.is_authenticated():
                flash('Logged in successfully.')

                return redirect(url_for('base.home'))
        return render_template('login.html', form=form)
    return render_template('login.html', form=form)



@base.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('base.home'))


@base.route('/profile')
@login_required
def profile():
    data = Result.query.filter(Result.user == current_user.id).count()

    return render_template('user.html', data=data)


@base.route('/project/<project_id>', methods=['GET', 'POST'])
@login_required
def project(project_id):
    data = Task.query.filter_by(project_id=project_id).first()
    
    return render_template('project.html', data=data)

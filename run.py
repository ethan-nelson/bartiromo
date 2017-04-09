from flask import Flask
from views import base
from login import login_manager
from models.users import User
from models.base import db

print dir(base)

app = Flask(__name__)
app.register_blueprint(base.base)
config = {
  'user': 'micro',
  'password': 'micro',
  'host': 'localhost',
  'database': 'micro',
}

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://' + \
                                        config['user'] + ':' + \
                                        config['password'] + '@' + \
                                        config['host'] + '/' + \
                                        config['database']


db.init_app(app)
#db.drop_all(app=app)
#db.create_all(app=app)

login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)

if __name__ == '__main__':
    app.debug = True
    app.config['SECRET_KEY'] = 'itsatrap'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.run(host='0.0.0.0', port=5432)


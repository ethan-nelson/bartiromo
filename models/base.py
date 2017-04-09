from flask.ext.sqlalchemy import SQLAlchemy

config = {
  'user': 'micro',
  'password': 'micro',
  'host': 'localhost',
  'database': 'micro',
}


db = SQLAlchemy()

engine = db.create_engine('mysql://' + \
                                        config['user'] + ':' + \
                                        config['password'] + '@' + \
                                        config['host'] + '/' + \
                                        config['database'], echo=True)
Session = db.sessionmaker(bind=engine)


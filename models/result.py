from base import *

class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.Integer, db.ForeignKey('task.id'))
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    result = db.Column(db.Integer)

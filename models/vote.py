from base import *

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Integer, db.ForeignKey('image.id'))
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    vote = db.Column(db.Integer)


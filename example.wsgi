python_home='/var/www/bartiromo/venv'
import sys
import os
import site

site_packages = python_home + '/lib/python3.6/site-packages'
site.addsitedir(site_packages)
site_packages = '/var/www/bartiromo/bartiromo'
site.addsitedir(site_packages)
os.environ['DATABASE_URL'] = 'postgresql://user:pass@host/db'
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'itsatrap'

import app

class Serve(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, env, start):
        env['SCRIPT_NAME'] = '/'
        return self.app(env, start)

application = Serve(app.app)

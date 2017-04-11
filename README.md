
This is a web application designed to assist in crowdsourced filtering and identification of features. The current focus is on weather and climate systems, but it can be applied to other situations as well.

## Design Structure

The application is built with [Flask](http://flask.pocoo.org), a Python web app module. Overall, the application is designed to be lean (in terms of codebase) and lightweight (in terms of user browser load).

* `app.py` holds the app initialization, database and form class definitions, and the app views (i.e. the queries used to populate pages).
* `static/` contains design files and eventually Javascript functions that will be used in image click classification projects.
* `templates/` holds html templates for all pages. The `default.html` file is the base template and that controls most of the branding.

## Installation

It is ideal to use a Python virtual environment to maintain a consistent library environment. Additionally, pip can be used to install all the required libraries with one command. Thus, once the repository has been cloned or downloaded and you have navigated into the directory:

~~~
$ virtualenv ./env
$ env/bin/pip install -r requirements.txt
~~~

The Python portion is now installed.

## Database

Next you need to tackle setting up a database to store all information for the website. The database can be Mysql, Postgresql, or another kind that is compatible with [SQLAlchemy](http://www.sqlalchemy.org/). Please follow the instructions of the database you want to use for installation.

Once it is configured, ensure you have a user and an empty database created. As an example for Postgresql,

~~~
$ sudo -u postgres psql
# CREATE USER "micro" PASSWORD 'micro';
# CREATE DATABASE "micro" OWNER "micro";
# \q
~~~

Database connection information is accessed via the environmental variable `DATABASE_URL` like the following form:

~~~
$ export DATABASE_URL="mysql://user:pass@host/db"
~~~

## Running the Application

With the Python modules and database configured, you are now ready to run the application.

The simplest way to run the app is to leverage Flask's internal web server, Werkzeug, using the python environment you installed:

~~~
$ env/bin/python app.py
~~~

By default, the app is served on 0.0.0.0:5432 using this mechanism, but that can be altered on the last line of the `app.py` file.

For deploying to Heroku, a PaaS, a Procfile is included in the repository that uses gunicorn to serve the website.

## Data Structure

* Projects are created with a given goal. Projects have a name, a description visible on the home page, and instructions displayed on the task page.
* Tasks are individual components of a project that are to be classified. In the case of image identification, a task is a single image.
* Results are user-chosen entries for a given task. In the case of image identification, a result would be "yes" in response to the instructions for a given project.

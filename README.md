
This is a web application designed to assist in crowdsourced filtering and identification of features. The current focus is on weather and climate systems, but it can be applied to other situations as well.

Installation
============

It is ideal to use a Python virtual environment to maintain a consistent library environment. Additionally, pip can be used to install all the required libraries with one command. Thus, once the repository has been cloned or downloaded and you have navigated into the directory:

~~~
$ virtualenv ./env
$ env/bin/pip install -r requirements.txt
~~~

The Python portion is now installed.

Database
========

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

Data Structure
==============

* Projects are created with a given goal. Projects have a name, a description visible on the home page, and instructions displayed on the task page.
* Tasks are individual components of a project that are to be classified. In the case of image identification, a task is a single image.
* Results are user-chosen entries for a given task. In the case of image identification, a result would be "yes" in response to the instructions for a given project.

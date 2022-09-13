from datetime import datetime

import click
from flask import current_app, g
from flask.cli import with_appcontext
from os import path, remove
import pandas as pd
import psycopg2


def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(current_app.config['DATABASE'])

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db_cur = db.cursor()

    db_cur.execute(
        "DROP TABLE IF EXISTS users CASCADE"
    )
    db_cur.execute(
        "DROP TABLE IF EXISTS predictions"
    )
    db_cur.execute(
        "DROP TABLE IF EXISTS submitted"
    )
    db_cur.execute(
        "DROP TABLE IF EXISTS estimators"
    )
    db_cur.execute(
        "CREATE TABLE users ("
        "id SERIAL PRIMARY KEY,"
        "username TEXT UNIQUE NOT NULL,"
        "password TEXT NOT NULL)"
    )
    db_cur.execute(
        "CREATE TABLE predictions ("
        "id SERIAL PRIMARY KEY,"
        "submitter_id INTEGER NOT NULL,"
        "first_name TEXT NOT NULL,"
        "gender TEXT NOT NULL CHECK(gender in ('Male', 'Female', 'Other')),"
        "age INTEGER NOT NULL,"
        "hypertension INTEGER NOT NULL CHECK(hypertension in (0, 1)),"
        "heart_disease INTEGER NOT NULL CHECK(heart_disease in (0, 1)),"
        "work_type TEXT NOT NULL CHECK(work_type in ('Private', 'Self-employed', 'Govt_job', 'children', 'Never_worked')),"
        "residence_type TEXT NOT NULL CHECK(Residence_type in ('Urban', 'Rural')),"
        "avg_glucose_level REAL NOT NULL,"
        "bmi REAL NOT NULL,"
        "smoking_status TEXT NOT NULL CHECK(smoking_status in ('formerly smoked', 'never smoked', 'smokes', 'Unknown')),"
        "stroke_prediction INTEGER NOT NULL CHECK(stroke_prediction in (0, 1)),"
        "FOREIGN KEY (submitter_id) REFERENCES users (id)"
        ")"
    )
    db_cur.execute(
        "CREATE TABLE submitted ("
        "id SERIAL PRIMARY KEY,"
        "gender TEXT NOT NULL CHECK(gender in ('Male', 'Female', 'Other')),"
        "age INTEGER NOT NULL,"
        "hypertension INTEGER NOT NULL CHECK(hypertension in (0, 1)),"
        "heart_disease INTEGER NOT NULL CHECK(heart_disease in (0, 1)),"
        "work_type TEXT NOT NULL CHECK(work_type in ('Private', 'Self-employed', 'Govt_job', 'children', 'Never_worked')),"
        "residence_type TEXT NOT NULL CHECK(Residence_type in ('Urban', 'Rural')),"
        "avg_glucose_level REAL NOT NULL,"
        "bmi REAL NOT NULL,"
        "smoking_status TEXT NOT NULL CHECK(smoking_status in ('formerly smoked', 'never smoked', 'smokes', 'Unknown')),"
        "stroke_prediction INTEGER NOT NULL CHECK(stroke_prediction in (0, 1)),"
        "stroke_actual INTEGER NOT NULL CHECK(stroke_actual in (0, 1)),"
        "used_to_improve INTEGER NOT NULL CHECK(used_to_improve in (0, 1))"
        ")"
    )
    db_cur.execute(
        "CREATE TABLE estimators ("
        "id SERIAL PRIMARY KEY,"
        "filename TEXT NOT NULL,"
        "create_date TIMESTAMP NOT NULL,"
        "object BYTEA NOT NULL)"
    )
    db_cur.execute(
        "INSERT INTO users (username, password)" # Password is p@55word!234
        "VALUES ('admin', 'pbkdf2:sha256:150000$IXrklqX2$8b03da10e3f2193a172dd21512931d5392bdf340a8347bdd3afd11b8cfcf2710')"
    )
    file = open('stroke-risk-log-model.joblib', 'rb').read()
    db_cur.execute(
        "INSERT INTO estimators (filename, create_date, object) "
        f"VALUES ('stroke-risk-log-model.joblib', '{datetime.now()}', "
        f"{psycopg2.Binary(file)})"
    )
    db.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

    patient_info = pd.read_csv('sdetectorapp/dataset/healthcare-dataset-stroke-data.csv')
    patient_info = patient_info.drop(['id', 'ever_married'], axis=1)

    patient_info['bmi'].fillna(patient_info['bmi'].mean(), inplace=True)

    db = get_db()
    db_cur = get_db().cursor()

    for i in range(0, patient_info['gender'].count()):

        db_cur.execute(
            "INSERT INTO submitted (gender, age, hypertension, heart_disease, work_type, residence_type, "
            "avg_glucose_level, bmi, smoking_status, stroke_prediction, stroke_actual, used_to_improve) "
            f"VALUES ('{patient_info['gender'][i]}', {int(patient_info['age'][i])}, "
            f"{int(patient_info['hypertension'][i])}, {int(patient_info['heart_disease'][i])}, "
            f"'{patient_info['work_type'][i]}', '{patient_info['Residence_type'][i]}', "
            f"{float(patient_info['avg_glucose_level'][i])}, {float(patient_info['bmi'][i])}, "
            f"'{patient_info['smoking_status'][i]}', {int(patient_info['stroke'][i])}, "
            f"{int(patient_info['stroke'][i])}, 1)"
        )

    db.commit()
    db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

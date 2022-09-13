import sys
from datetime import datetime
from io import BytesIO
from os import remove

import joblib
import pandas as pd
import psycopg2

from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_file
)
import sdetectorapp.estimator as estimator
from sdetectorapp.auth import login_required
from sdetectorapp.db import get_db
import sdetectorapp.visualizations as visuals

bp = Blueprint('index', __name__)

line_graph_img = None
bar_graph_img = None
heatmap_img = None


@bp.route('/', methods=['GET'])
@login_required
def index():
    db = get_db()
    db_cur = db.cursor()
    db_cur.execute(
        "SELECT id, submitter_id, first_name, age, stroke_prediction "
        f"FROM predictions WHERE submitter_id = {g.user['id']} "
        "ORDER BY id"
    )
    results = db_cur.fetchall()
    if len(results) == 0:
        patients = []
    else:
        patients = []
        for result in results:
            patient = {'id': result[0], 'submitter_id': result[1], 'first_name': result[2], 'age': result[3],
                       'stroke_prediction': result[4]}
            patients.append(patient)
    return render_template('saas_app/index.html', patients=patients)


@bp.route("/new", methods=['GET', 'POST'])
@login_required
def patient_info_input():
    if request.method == 'POST':
        first_name = request.form['first_name']
        gender = request.form['gender']
        age = request.form['age']
        hypertension = request.form['hypertension']
        heart_disease = request.form['heart_disease']
        work_type = request.form['work_type']
        residence_type = request.form['Residence_type']
        avg_glucose_level = request.form['avg_glucose_level']
        bmi = request.form['bmi']
        smoking_status = request.form['smoking_status']
        error = None

        if not first_name or not gender or not age or not hypertension or not heart_disease or not work_type or \
                not residence_type or not avg_glucose_level or not bmi or not smoking_status:
            error = "All fields are required."

        if error is not None:
            flash(error)
        else:
            data = {'gender': gender, 'age': age,
                    'hypertension': hypertension, 'heart_disease': heart_disease,
                    'work_type': work_type,
                    'Residence_type': residence_type,
                    'avg_glucose_level': avg_glucose_level, 'bmi': bmi,
                    'smoking_status': smoking_status}

            dataframe = pd.DataFrame(data, index=[0])

            result = {'result': True if estimator.lkm_model.predict(dataframe) == 1 else False,
                      'probability': round(estimator.lkm_model.predict_proba(dataframe)[0, 1] * 100, 2)}

            db = get_db()
            db_cur = db.cursor()
            db_cur.execute(
                "INSERT INTO predictions (submitter_id, first_name, gender, age, hypertension, heart_disease, "
                "work_type, residence_type, avg_glucose_level, bmi, smoking_status, stroke_prediction) "
                f"VALUES ({g.user['id']}, '{first_name.capitalize()}', '{gender}', {int(age)}, {int(hypertension)}, "
                f"{int(heart_disease)}, '{work_type}', '{residence_type}', {float(avg_glucose_level)}, "
                f"{float(bmi)}, '{smoking_status}', {1 if result['result'] else 0})"
            )
            db.commit()

            return render_template("saas_app/results.html", result=result)

    return render_template("saas_app/indicators.html")


@bp.route('/<int:id>/checkout', methods=['GET', 'POST'])
@login_required
def submit(id):
    if request.method == 'GET':
        db = get_db()
        db_cur = db.cursor()
        db_cur.execute(
            "SELECT id, stroke_prediction "
            f"FROM predictions WHERE submitter_id = {g.user['id']} AND id = {id}"
        )
        result = db_cur.fetchone()
        patient = {'id': result[0], 'stroke_prediction': result[1]}
        return render_template('saas_app/checkout.html', patient=patient)

    else:
        stroke_actual = request.form["stroke_actual"]
        error = None

        if not stroke_actual:
            error = "Need outcome of patient's visit before they can be checked out."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db_cur = db.cursor()
            db_cur.execute(
                "SELECT gender, age, hypertension, heart_disease, work_type, "
                "residence_type, avg_glucose_level, bmi, smoking_status, stroke_prediction FROM predictions "
                f"WHERE submitter_id = {g.user['id']} AND id = {id}"
            )
            patient_info = db_cur.fetchone()
            db_cur.execute(
                "INSERT INTO submitted(gender, age, hypertension, heart_disease, work_type, residence_type, "
                "avg_glucose_level, bmi, smoking_status, stroke_prediction, stroke_actual, used_to_improve) "
                f"VALUES ('{patient_info[0]}', {patient_info[1]}, {patient_info[2]}, "
                f"{patient_info[3]}, '{patient_info[4]}', '{patient_info[5]}', "
                f"{patient_info[6]}, {patient_info[7]}, '{patient_info[8]}', "
                f"{patient_info[9]}, {request.form['stroke_actual']}, 0)"
            )
            db.commit()

            # Drop the entry in the predictions table because the patient has been checked out of the system.
            db_cur.execute(
                f"DELETE FROM predictions WHERE id = {id}"
            )
            db.commit()

            return redirect(url_for('index.index'))


@bp.route('/maintenance', methods=['GET', 'POST'])
@login_required
def maintain():
    if request.method == 'GET':
        db = get_db()
        db_cur = db.cursor()
        db_cur.execute(
            'SELECT stroke_prediction, stroke_actual '
            'FROM submitted '
            'WHERE used_to_improve = 0'
        )
        stroke_pred_act = db_cur.fetchall()

        accuracy_measure = None
        if len(stroke_pred_act) > 0:
            correct = 0
            count = 0
            for entry in stroke_pred_act:
                if entry[0] == entry[1]:
                    correct += 1

                count += 1
            accuracy_measure = {'accuracy': correct / count, 'count': count}

        # TODO Fix the template for the case when accuracy is 0 but there are entries.
        return render_template('saas_app/maintenance.html', accuracy_measure=accuracy_measure)
    else:  # For POST requests
        db = get_db()
        db_cur = db.cursor()
        db_cur.execute(
            'SELECT * FROM submitted'
        )
        data_raw = db_cur.fetchall()

        data = {'gender': [], 'age': [],
                'hypertension': [], 'heart_disease': [],
                'work_type': [],
                'Residence_type': [],
                'avg_glucose_level': [], 'bmi': [],
                'smoking_status': [], 'stroke': []}

        for dr in data_raw:
            data['gender'].append(dr[1])
            data['age'].append(dr[2])
            data['hypertension'].append(dr[3])
            data['heart_disease'].append(dr[4])
            data['work_type'].append(dr[5])
            data['Residence_type'].append(dr[6])
            data['avg_glucose_level'].append(dr[7])
            data['bmi'].append(dr[8])
            data['smoking_status'].append(dr[9])
            data['stroke'].append(dr[10])

        dataframe = pd.DataFrame(data)

        X = dataframe.drop('stroke', axis=1)
        y = dataframe['stroke']

        estimator.lkm_model.fit(X, y)

        joblib.dump(estimator.lkm_model, 'updated-model.joblib')
        file = open('updated-model.joblib', 'rb').read()

        db_cur.execute(
            "INSERT INTO estimators (filename, create_date, object) "
            f"VALUES ('model-updated-{datetime.now().strftime('%d-%m-%y-%H%M')}.joblib', '{datetime.now()}', "
            f"{psycopg2.Binary(file)})"
        )

        remove('updated-model.joblib')

        db_cur.execute(
            'UPDATE submitted SET used_to_improve = 1 '
            'WHERE used_to_improve = 0'
        )
        db.commit()

        return redirect(url_for('index.index'))


def render_visuals():
    global line_graph_img, bar_graph_img, heatmap_img
    line_graph_img = visuals.get_age_risk_line_graph()
    bar_graph_img = visuals.get_ht_hd_bar_graph()
    heatmap_img = visuals.get_heatmap()


@bp.route('/how-it-works', methods=['GET'])
def visualizations():
    render_visuals()

    return render_template('saas_app/how-it-works.html')


@bp.route('/line')
def display_line_graph():
    return send_file(line_graph_img, mimetype='img/png')


@bp.route('/bargraph')
def display_bar_graph():
    return send_file(bar_graph_img, mimetype='img/png')


@bp.route('/heatmap')
def display_heatmap():
    return send_file(heatmap_img, mimetype='img/png')

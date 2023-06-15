import os
from io import BytesIO

import joblib
from sdetectorapp.db import get_db

lkm_model = None


def init_estimator():
    global lkm_model

    lkm_model = None

    db = get_db()
    try:
        result = db.query("SELECT * FROM Stroke_Detector_App.estimators").result()
    except:
        result = None

    if result is None or result.total_rows == 0:
        lkm_model = joblib.load('stroke-risk-log-model.joblib')
        print('Database uninitialized, loading model from file: stroke-risk-log-model.joblib')
    else:
        job = db.query(
            "SELECT * FROM Stroke_Detector_App.estimators ORDER BY create_date DESC"
        ).result()
        latest_model = next(job)

        if latest_model is None:
            estimator_data = 'stroke-risk-log-model.joblib'
        else:
            estimator_data = BytesIO(latest_model[3])

        lkm_model = joblib.load(estimator_data)

        print(f'Currently loaded model: {estimator_data if latest_model is None else latest_model[1]}')

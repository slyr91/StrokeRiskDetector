import os
from io import BytesIO

import joblib
from sdetectorapp.db import get_db

lkm_model = None

def init_estimator():
    global lkm_model

    lkm_model = None

    db = get_db()
    db_cur = db.cursor()
    db_cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name = 'estimators'"
    )
    result = db_cur.fetchone()

    if result is None:
        lkm_model = joblib.load('stroke-risk-log-model.joblib')
        print('Database uninitialized, loading model from file: stroke-risk-log-model.joblib')
    else:
        db_cur.execute(
            "SELECT * FROM estimators ORDER BY create_date DESC"
        )
        latest_model = db_cur.fetchone()

        if latest_model is None:
            estimator_data = 'stroke-risk-log-model.joblib'
        else:
            estimator_data = BytesIO(latest_model[3])

        lkm_model = joblib.load(estimator_data)

        print(f'Currently loaded model: {estimator_data if latest_model is None else latest_model[1]}')

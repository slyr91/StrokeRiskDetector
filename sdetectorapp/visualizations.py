import io

import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.pyplot as plt
import seaborn as sns

import sdetectorapp.estimator as estimator
from sdetectorapp.db import get_db


def get_age_risk_line_graph():
    db = get_db()
    ages = range(10, 120, 10)
    avg_predictions = []

    for i in ages:
        dataset = db.query(
            f"SELECT * FROM Stroke_Detector_App.submitted WHERE age BETWEEN {i - 9} AND {i}"
        )

        if len(dataset) < 1:
            avg_predictions.append(0)
            continue

        dataset_df = {'gender': [], 'age': [],
                      'hypertension': [], 'heart_disease': [],
                      'work_type': [],
                      'Residence_type': [],
                      'avg_glucose_level': [], 'bmi': [],
                      'smoking_status': [], 'stroke': []}

        for dr in dataset:
            dataset_df['gender'].append(dr[1])
            dataset_df['age'].append(dr[2])
            dataset_df['hypertension'].append(dr[3])
            dataset_df['heart_disease'].append(dr[4])
            dataset_df['work_type'].append(dr[5])
            dataset_df['Residence_type'].append(dr[6])
            dataset_df['avg_glucose_level'].append(dr[7])
            dataset_df['bmi'].append(dr[8])
            dataset_df['smoking_status'].append(dr[9])
            dataset_df['stroke'].append(dr[11])

        dataframe = pd.DataFrame(dataset_df)

        x = dataframe.drop('stroke', axis=1)
        prediction = estimator.lkm_model.predict_proba(x)

        avg_predictions.append(prediction[:, 1].mean() * 100)

    risk_age_data = {'age': ages, 'risk': avg_predictions}
    risk_age_data = pd.DataFrame(risk_age_data)
    risk_age_data = risk_age_data[risk_age_data['risk'] != 0]

    fig = plt.figure(figsize=(14, 7))
    plt.title('Age VS Stroke Risk')
    sns.lineplot(x='age', y='risk', data=risk_age_data)
    canvas = FigureCanvas(fig)
    img = io.BytesIO()
    fig.savefig(img)
    img.seek(0)
    plt.close(fig)
    return img


def get_ht_hd_bar_graph():
    db = get_db()
    ages = range(10, 120, 10)
    occurrences = {'age_group': [], 'percentage_of_sample': [], 'risk_factor': []}

    for i in ages:
        dataset = db.query(
            f"SELECT * FROM Stroke_Detector_App.submitted WHERE age BETWEEN {i - 9} AND {i}"
        )

        if len(dataset) == 0:
            continue

        dataset_df = {'gender': [], 'age': [],
                      'hypertension': [], 'heart_disease': [],
                      'work_type': [],
                      'Residence_type': [],
                      'avg_glucose_level': [], 'bmi': [],
                      'smoking_status': [], 'stroke': []}

        for dr in dataset:
            dataset_df['gender'].append(dr[1])
            dataset_df['age'].append(dr[2])
            dataset_df['hypertension'].append(dr[3])
            dataset_df['heart_disease'].append(dr[4])
            dataset_df['work_type'].append(dr[5])
            dataset_df['Residence_type'].append(dr[6])
            dataset_df['avg_glucose_level'].append(dr[7])
            dataset_df['bmi'].append(dr[8])
            dataset_df['smoking_status'].append(dr[9])
            dataset_df['stroke'].append(dr[11])

        dataframe = pd.DataFrame(dataset_df)

        occurrences['age_group'].append(i)
        occurrences['percentage_of_sample'].append((dataframe[dataframe['hypertension'] == 1]['hypertension'].count() /
                                                   dataframe['hypertension'].count()) * 100)
        occurrences['risk_factor'].append('hypertension')

        occurrences['age_group'].append(i)
        occurrences['percentage_of_sample'].append((dataframe[dataframe['heart_disease'] == 1]['heart_disease'].count() /
                                                   dataframe['heart_disease'].count()) * 100)
        occurrences['risk_factor'].append('heart_disease')

    occurrences = pd.DataFrame(occurrences)
    fig = plt.figure(figsize=(14, 7))
    plt.title('Risk Factor Development as Age Increases')
    sns.barplot(x='age_group', y='percentage_of_sample', hue='risk_factor', data=occurrences)
    canvas = FigureCanvas(fig)
    img = io.BytesIO()
    fig.savefig(img)
    img.seek(0)
    plt.close(fig)
    return img


def get_heatmap():
    db = get_db()
    data_raw = db.query(
        'SELECT * FROM Stroke_Detector_App.submitted'
    )

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
        data['stroke'].append(dr[11])

    dataframe = pd.DataFrame(data)

    dataframe['bmi'].fillna(dataframe['bmi'].mean(), inplace=True)

    cols_with_multiple_cats = [col for col in dataframe.columns if dataframe[col].nunique() > 2 and
                               dataframe[col].dtype == 'object']

    for col in cols_with_multiple_cats:
        oh_encoded_col = pd.get_dummies(dataframe[col], prefix=col)
        dataframe = dataframe.drop(col, axis=1)
        dataframe = pd.concat([dataframe, oh_encoded_col], axis=1)

    fig = plt.figure(figsize=(20, 24))
    plt.title('Correlation Heatmap')
    sns.heatmap(dataframe.corr(), annot=True)
    canvas = FigureCanvas(fig)
    img = io.BytesIO()
    fig.savefig(img)
    img.seek(0)
    plt.close(fig)
    return img

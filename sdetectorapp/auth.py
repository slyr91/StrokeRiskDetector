import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from sdetectorapp.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        result = db.query(
            f"SELECT id FROM Stroke_Detector_App.users WHERE username = '{username}'"
        ).result()

        result = next(result)

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif result[0] is not None:
            error = 'User {} is already registered.'.format(username)

        if error is None:
            db.query(
                f"INSERT INTO Stroke_Detector_App.users (username, password) "
                f"VALUES ('{username}', '{generate_password_hash(password)}')"
            )
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.query(
            f"SELECT * FROM Stroke_Detector_App.users WHERE username = '{username}'"
        ).result()

        user = next(user)

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user[2], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user[0]
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        db = get_db()
        user = db.query(
            f"SELECT * FROM Stroke_Detector_App.users WHERE id = '{user_id}'"
        ).result()
        user = next(user)
        g.user = {'id': user[0], 'username': user[1]}


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

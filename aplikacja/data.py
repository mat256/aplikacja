from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from aplikacja.auth import login_required
from aplikacja.db import get_db

bp = Blueprint('data', __name__, url_prefix='/data')

@bp.route('/all')
@login_required
def all():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, created, author_id, username'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC',(g.user['id'],)
    ).fetchall()
    return render_template('data/all.html', all_data=all_data)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        glucose = request.form['glucose']
        activity = request.form['activity']
        info = request.form['info']
        custom_date = request.form['date']
        error = None

        if not glucose:
            error = 'Glucose is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO data (glucose, activity, info, custom_date, author_id)'
                ' VALUES (?, ?, ?, ?, ?)',
                (glucose, activity, info, custom_date, g.user['id'])
            )
            db.commit()
            return redirect(url_for('data.all'))

    return render_template('data/create.html')

def get_single_data(id, check_author=True):
    s_data = get_db().execute(
        'SELECT p.id, glucose, activity, info, created, author_id, username'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if s_data is None:
        abort(404, f"Entry id {id} doesn't exist.")

    if check_author and s_data['author_id'] != g.user['id']:
        abort(403)

    return s_data

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    data = get_single_data(id)

    if request.method == 'POST':
        glucose = request.form['glucose']
        activity = request.form['activity']
        info = request.form['info']
        error = None

        if not glucose:
            error = 'Glucose is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE data SET glucose = ?, activity = ?, info = ?'
                ' WHERE id = ?',
                (glucose, activity, info, id)
            )
            db.commit()
            return redirect(url_for('data.all'))

    return render_template('data/update.html', data=data)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    print('id:')
    get_single_data(id)
    db = get_db()
    db.execute('DELETE FROM data WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('data.all'))
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from aplikacja.auth import login_required
from aplikacja.db import get_db

bp = Blueprint('data', __name__, url_prefix='/data')

@bp.route('/all')
def all():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, created, author_id, username'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('data/all.html', all_data=all_data)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
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
                'INSERT INTO data (glucose, activity, info, author_id)'
                ' VALUES (?, ?, ?, ?)',
                (glucose, activity, info, g.user['id'])
            )
            db.commit()
            return redirect(url_for('data.all'))

    return render_template('data/create.html')
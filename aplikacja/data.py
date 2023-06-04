from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from aplikacja.auth import login_required
from aplikacja.db import get_db

from aplikacja import files
import pandas as pd

import sqlite3
from flask_uploads import IMAGES, UploadSet, configure_uploads
import os

bp = Blueprint('data', __name__, url_prefix='/data')


@bp.route('/all')
@login_required
def all():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, created, author_id, username'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    return render_template('data/all.html', all_data=all_data)

@bp.route('/files')
@login_required
def files():
    db = get_db()
    all_files = db.execute(
        'SELECT p.id, name, author_id, uploaded'
        ' FROM file p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY uploaded DESC', (g.user['id'],)
    ).fetchall()
    return render_template('data/files.html', all_files=all_files)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        #files.save(file)
        db = get_db()
        cur = db.execute(
            'INSERT INTO file (author_id, name)'
            ' VALUES (?, ?)'
            ' RETURNING id,name',
            (g.user['id'], file.filename)
        )
        file_id = cur.fetchone()[0]
        #print(cur)
        #print(next(cur))
        #print(cur.fetchone()[0])
        #file_id = f.fetchall()
        #print(file_id)
        db.commit()

        df = pd.read_excel(file)
        df['author_id'] = [g.user['id']] * df.shape[0]
        df['custom_date'] = df['Date']
        df['from_file'] = [1] * df.shape[0]
        df['file_id'] = [file_id] * df.shape[0]
        df.fillna("", inplace=True)

        df = df.drop(columns = ['ID', 'Date', 'Time'])

        df.to_sql(name='data', con=db, if_exists='append', index=False)
        db.commit()

        return redirect(url_for('data.all'))

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
                (glucose, activity, info, custom_date + ' 00:00:00', g.user['id'])
            )
            db.commit()
            return redirect(url_for('data.all'))

    return render_template('data/create.html')


"""
@bp.route('/upload', methods=('GET', 'POST'))
@login_required
def upload():
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
"""


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
    #print('id:')
    get_single_data(id)
    db = get_db()
    db.execute('DELETE FROM data WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('data.all'))

@bp.route('/<int:id>/delete_file', methods=('POST',))
@login_required
def delete_file(id):
    #print('id:')
    #get_single_data(id)
    db = get_db()
    db.execute('DELETE FROM file WHERE id = ?', (id,))
    db.execute('DELETE FROM data WHERE file_id = ?', (id,))
    db.commit()
    return redirect(url_for('data.files'))
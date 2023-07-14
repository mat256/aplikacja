from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from aplikacja.auth import login_required
from aplikacja.db import get_db

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Select
from bokeh.models import CustomJS, DatePicker
import random
from datetime import date

import pygal
from aplikacja import files
import pandas as pd
from pygal.style import DarkStyle, DefaultStyle

import sqlite3
from flask_uploads import IMAGES, UploadSet, configure_uploads
import os

#bp_parent = Blueprint('data', __name__, url_prefix='/data')
bp = Blueprint('insulin', __name__, url_prefix='/insulin')

@bp.route('/all')
@login_required
def all():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, amount, period, type, custom_date, created, f.name'
        ' FROM insulin p JOIN user u ON p.author_id = u.id JOIN file f ON p.file_id = f.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    return render_template('data/insulin/all.html', data=all_data)



"""
@bp.route('/graph', methods=('GET', 'POST'))
@login_required
def graph():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, created, stat, author_id'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'created', 'stat', 'author_id'])
    # print(df)
    df = df.filter(['glucose', 'custom_date'], axis=1)
    df.sort_values(by='custom_date', ascending=False, inplace=True)
    today = date.today()
    choosen_date=today
    chart_data = df.loc[(df['custom_date'] >= str(today)+' 00:00:00')
                             & (df['custom_date'] < str(today) +' 23:59:59')]

    if request.method == 'POST':
        choosen_date = request.form['date']
        chart_data = df.loc[(df['custom_date'] >= choosen_date+' 00:00:00')
                             & (df['custom_date'] < choosen_date+' 23:59:59')
        ]


    #chart_data_1 = chart_data[:100]
    #chart_data_2 = chart_data[100:]
    #print(chart_data_1)
    #print(chart_data_2)
    source = ColumnDataSource(chart_data)


    hover_tool = HoverTool(
        tooltips=[("index", "@glucose"),
        ("desc", "@custom_date{%T}")], mode='vline', formatters={"@custom_date": "datetime"}
    )

    p3 = figure(height=350, sizing_mode="stretch_width", x_axis_type="datetime")
    p3.add_tools(hover_tool)
    p3.line(
        x='custom_date', y='glucose', source=source,
        line_width=2,
        color="olive",
        alpha=0.5
    )
    script, div = components(p3)

    return render_template(
        'data/graph.html',
        script=[script],
        div=[div],
        date=choosen_date
    )"""


"""

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
"""

"""
@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        # files.save(file)
        db = get_db()
        cur = db.execute(
            'INSERT INTO file (author_id, name)'
            ' VALUES (?, ?)'
            ' RETURNING id,name',
            (g.user['id'],
             file.filename
             )
        )
        file_id = cur.fetchone()[0]
        # print(cur)
        # print(next(cur))
        # print(cur.fetchone()[0])
        # file_id = f.fetchall()
        # print(file_id)
        db.commit()

        df = pd.read_excel(file)
        df['author_id'] = [g.user['id']] * df.shape[0]
        df['custom_date'] = df['Date']
        df['from_file'] = [1] * df.shape[0]
        df['file_id'] = [file_id] * df.shape[0]
        df.fillna("", inplace=True)

        df = df.drop(columns=['ID', 'Date', 'Time'])

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

    return render_template('data/add.html')"""


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        # files.save(file)
        db = get_db()
        cur = db.execute(
            'INSERT INTO file (author_id, name)'
            ' VALUES (?, ?)'
            ' RETURNING id,name',
            (g.user['id'],
             file.filename
             )
        )
        file_id = cur.fetchone()[0]
        # print(cur)
        # print(next(cur))
        # print(cur.fetchone()[0])
        # file_id = f.fetchall()
        # print(file_id)
        db.commit()

        df = pd.read_excel(file)
        df['author_id'] = [g.user['id']] * df.shape[0]
        df['custom_date'] = df['Date']
        df['from_file'] = [1] * df.shape[0]
        df['file_id'] = [file_id] * df.shape[0]
        df.fillna("", inplace=True)

        df = df.drop(columns=['ID', 'Date'])

        df.to_sql(name='insulin', con=db, if_exists='append', index=False)
        db.commit()

        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        amount = request.form['amount']
        period = request.form['period']
        type = request.form['type']
        custom_date = request.form['date']
        error = None

        if not amount:
            error = 'Insulin amount is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO insulin (amount, period, type, custom_date, author_id)'
                ' VALUES (?, ?, ?, ?, ?)',
                (amount, period, type, custom_date + ' 00:00:00', g.user['id'])
            )
            db.commit()
            return redirect(url_for('dashboard.dashboard'))

    return render_template('data/insulin/add.html')

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

    return render_template('data/add.html')
"""

"""
def get_single_data_glucose(id, check_author=True):
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

    return s_data"""

def get_single_data(id, check_author=True):
    s_data = get_db().execute(
        'SELECT p.id, amount, period, type, custom_date, author_id'
        ' FROM insulin p JOIN user u ON p.author_id = u.id'
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
        amount = request.form['amount']
        period = request.form['period']
        type = request.form['type']
        error = None

        if not amount:
            error = 'Insulin amount is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE insulin SET amount = ?, period = ?, type = ?'
                ' WHERE id = ?',
                (amount, period, type, id)
            )
            db.commit()
            return redirect(url_for('data.insulin.all'))

    return render_template('data/insulin/update.html', data=data)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    # print('id:')
    get_single_data(id)
    db = get_db()
    db.execute('DELETE FROM insulin WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('data.insulin.all'))

"""
@bp.route('/<int:id>/delete_file', methods=('POST',))
@login_required
def delete_file(id, check_author=True):
    # print('id:')
    # get_single_data(id)
    s_data = get_db().execute(
        'SELECT p.id'
        ' FROM files p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if s_data is None:
        abort(404, f"Entry id {id} doesn't exist.")

    if check_author and s_data['author_id'] != g.user['id']:
        abort(403)

    db = get_db()
    db.execute('DELETE FROM file WHERE id = ?', (id,))
    db.execute('DELETE FROM data WHERE file_id = ?', (id,))
    db.commit()
    return redirect(url_for('data.files'))
"""
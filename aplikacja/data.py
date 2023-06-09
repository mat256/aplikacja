from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from aplikacja.auth import login_required
from aplikacja.db import get_db

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
import random

import pygal
from aplikacja import files
import pandas as pd
from pygal.style import DarkStyle, DefaultStyle

import sqlite3
from flask_uploads import IMAGES, UploadSet, configure_uploads
import os

bp = Blueprint('data', __name__, url_prefix='/data')


@bp.route('/all')
@login_required
def all():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, created, stat, author_id, username'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    return render_template('data/all.html', all_data=all_data)


@bp.route('/graph')
@login_required
def graph():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, created, stat, author_id'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    # print(all_data[0][0])
    tab = pd.read_sql('SELECT p.id, glucose, activity, info, custom_date, created, stat, author_id'
                      ' FROM data p JOIN user u ON p.author_id = u.id'
                      ' ORDER BY created DESC', db)
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'created', 'stat', 'author_id'])
    # print(df)
    chart_data = df.filter(['glucose', 'custom_date'], axis=1)
    chart_data.sort_values(by='custom_date', ascending=False, inplace=True)
    source = ColumnDataSource(chart_data)

    p1 = figure(height=350, sizing_mode="stretch_width")

    TOOLTIPS = [
        ("index", "@glucose"),
        ("desc", "@custom_date{%F}"),
    ]
    hover_tool = HoverTool(
        tooltips=[("index", "@glucose"),
        ("desc", "@custom_date{%T}")], mode='vline', formatters={"@custom_date": "datetime"}
    )
    p1.circle(
        [i for i in range(10)],
        [random.randint(1, 50) for j in range(10)],
        size=20,
        color="navy",
        alpha=0.5
    )

    # Second Chart - Line Plot
    language = ['Python', 'JavaScript', 'C++', 'C#', 'Java', 'Golang']
    popularity = [85, 91, 63, 58, 80, 77]

    p2 = figure(
        x_range=language,
        height=350,
        title="Popularity",
    )
    p2.vbar(x=language, top=popularity, width=0.5)
    p2.xgrid.grid_line_color = None
    p2.y_range.start = 0

    # Third Chart - Line Plot
    p3 = figure(height=350, sizing_mode="stretch_width", x_axis_type="datetime")
    p3.add_tools(hover_tool)
    p3.line(
        x='custom_date', y='glucose', source=source,
        line_width=2,
        color="olive",
        alpha=0.5
    )

    script1, div1 = components(p1)
    script2, div2 = components(p2)
    script3, div3 = components(p3)

    return render_template(
        'data/graph.html',
        script=[script1, script2, script3],
        div=[div1, div2, div3],
    )


@bp.route('/charts')
@login_required
def charts():
    config = pygal.Config()
    config.style = pygal.style.DefaultStyle
    config.defs.append('''
      <linearGradient id="gradient-0" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="#f71505" />
        <stop offset="64%" stop-color="#f7e305" />
        <stop offset="80%" stop-color="#0aed02" />
        <stop offset="92%" stop-color="#f7e305" />
        <stop offset="100%" stop-color="#f71505" />
      </linearGradient>
    ''')
    config.defs.append('''
      <linearGradient id="gradient-1" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stop-color="#b6e354" />
        <stop offset="100%" stop-color="#8cedff" />
      </linearGradient>
    ''')
    config.css.append('''inline:
      .color-0 {
        fill: url(#gradient-0) !important;
        stroke: url(#gradient-0) !important;
      }''')
    config.css.append('''inline:
      .color-1 {
        fill: url(#gradient-1) !important;
        stroke: url(#gradient-1) !important;
      }''')

    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, created, stat, author_id'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    # print(all_data[0][0])
    tab = pd.read_sql('SELECT p.id, glucose, activity, info, custom_date, created, stat, author_id'
                      ' FROM data p JOIN user u ON p.author_id = u.id'
                      ' ORDER BY created DESC', db)
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'created', 'stat', 'author_id'])
    # print(df)
    chart_data = df.filter(['glucose', 'custom_date'], axis=1)
    chart_data.sort_values(by='custom_date', ascending=False, inplace=True)

    # chart_data['custom_date'] = pd.to_datetime(chart_data['custom_date']).dt.time
    # ch = chart_data.to_numpy()
    # chart_data['glucose'] = chart_data['glucose'].astype('int32')
    # print(type(chart_data['custom_date'][0]))
    # print(type(chart_data['glucose'][0]))
    # print(chart_data['custom_date'][0])
    # print(chart_data)
    # print([(x[0],x[1]) for x in ch])
    bar_chart = pygal.DateTimeLine(
        # config,
        # interpolate='cubic',
        dots_size=0.5,
        # fill=True,
        stroke_style={'width': 5},
        x_label_rotation=35, x_labels_major_every=3, truncate_label=-1, max_scale=10, range=(50, 300),
        x_value_formatter=lambda dt: dt.strftime('%d, %b %Y at %H:%M:%S'))
    # print([(type(x)) for x in chart_data.T.items()])
    # [print(x[1][0],x[1][1]) for x in chart_data.T.items()]
    # print([(x[1][0]) for x in chart_data.T.items()])
    bar_chart.x_labels = [(x[1][1].date()) for x in chart_data.T.items()]
    # bar_chart.x_labels = ["00:00","12:00"]
    bar_chart.add("Glucose", [(x[1][1], x[1][0]) for x in chart_data.T.items()])

    chart = bar_chart.render_data_uri()
    # bar_chart.render()
    return render_template('data/charts.html', chart=chart)


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
        # files.save(file)
        db = get_db()
        cur = db.execute(
            'INSERT INTO file (author_id, name)'
            ' VALUES (?, ?)'
            ' RETURNING id,name',
            (g.user['id'], file.filename)
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
    # print('id:')
    get_single_data(id)
    db = get_db()
    db.execute('DELETE FROM data WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('data.all'))


@bp.route('/<int:id>/delete_file', methods=('POST',))
@login_required
def delete_file(id):
    # print('id:')
    # get_single_data(id)
    db = get_db()
    db.execute('DELETE FROM file WHERE id = ?', (id,))
    db.execute('DELETE FROM data WHERE file_id = ?', (id,))
    db.commit()
    return redirect(url_for('data.files'))

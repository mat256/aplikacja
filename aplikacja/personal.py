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
from datetime import date
import pygal
import pandas as pd
from pygal.style import DarkStyle, DefaultStyle

import sqlite3
from flask_uploads import IMAGES, UploadSet, configure_uploads
import os

bp = Blueprint('personal', __name__, url_prefix='/personal')


def get_user_data(id, check_author=True):
    s_data = get_db().execute(
        'SELECT name, surname, pesel, birth_date, day_start, day_end, phone, email, adress, author_id'
        ' FROM personal p'
        ' WHERE p.user_id = ?', (id,)
    ).fetchone()
    if s_data is None:
        user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (id,)
        ).fetchone()
        if user is None:
            abort(404, f"Entry user id {id} doesn't exist.")
        else:
            return False

    if check_author and s_data['author_id'] != g.user['id']:
        abort(403)

    return s_data

@bp.route('/show')
@login_required
def show():
    #db = get_db()
    data = get_user_data(g.user['id'])
    if data==False:
        return redirect(url_for('data.personal.create'))
    age = int((date.today() - data['birth_date']).days/365.2425)
    #print(int(age))
    return render_template('data/personal/show.html', data=data, age=age)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():

    if request.method == 'POST' and 'file' not in request.files:
        name = request.form['name']
        surname = request.form['surname']
        pesel = request.form['pesel']
        #info = request.form['info']
        birth_date = request.form['date']
        day_start = request.form['day_start']
        day_end = request.form['day_end']
        phone = request.form['phone']
        email = request.form['email']
        adress = request.form['adress']
        error = None

        if not name:
            error = 'Name is required.'
        if not surname:
            error = 'Surname is required.'
        if not birth_date:
            error = 'Birth date is required.'

        if error is not None:
            flash(error, 'alert alert-danger')
        else:
            db = get_db()
            db.execute(
                'INSERT INTO personal (name, surname, pesel, birth_date, day_start, day_end, phone, email, adress, author_id, user_id)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (name, surname, pesel, birth_date, day_start, day_end, phone, email, adress, g.user['id'], g.user['id'])
            )
            db.commit()
            flash('Information successfully added', 'alert alert-success')
            return redirect(url_for('data.personal.show'))

    return render_template('data/personal/add.html')

@bp.route('/update', methods=('GET', 'POST'))
@login_required
def update():
    data = get_user_data(g.user['id'])
    birth_date=data['birth_date']
    if request.method == 'POST':
        name = request.form['name']
        surname = request.form['surname']
        pesel = request.form['pesel']
        # info = request.form['info']
        birth_date = request.form['date']
        day_start = request.form['day_start']
        day_end = request.form['day_end']
        phone = request.form['phone']
        email = request.form['email']
        adress = request.form['adress']
        error = None

        if not name:
            error = 'Name is required.'
        if not surname:
            error = 'Surname is required.'
        if not birth_date:
            error = 'Birth date is required.'

        if error is not None:
            flash(error, 'alert alert-danger')

        else:
            db = get_db()
            db.execute(
                'UPDATE personal SET name = ?, surname = ?, pesel = ?, birth_date = ?, day_start = ?, day_end = ?, phone = ?, email = ?, adress = ?'
                ' WHERE user_id = ?',
                (name, surname, pesel, birth_date, day_start, day_end, phone, email, adress, g.user['id'])
            )
            db.commit()
            return redirect(url_for('data.personal.show'))

    return render_template('data/personal/update.html', data=data,date=birth_date)
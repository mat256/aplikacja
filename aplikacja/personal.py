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
import pandas as pd
from pygal.style import DarkStyle, DefaultStyle

import sqlite3
from flask_uploads import IMAGES, UploadSet, configure_uploads
import os

bp = Blueprint('personal', __name__, url_prefix='/personal')

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
                'INSERT INTO personal (name, surname, pesel, birth_date, day_start, day_end, phone, email, adress, author_id)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (name, surname, pesel, birth_date, day_start, day_end, phone, email, adress, g.user['id'])
            )
            db.commit()
            flash('Entry successfully added', 'alert alert-success')
            return redirect(url_for('dashboard.dashboard'))

    return render_template('data/personal/add.html')
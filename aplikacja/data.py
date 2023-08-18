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

bp = Blueprint('data', __name__, url_prefix='/data')







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
    return render_template('data/files.html', data=all_files)






@bp.route('/<int:id>/delete_file', methods=('POST',))
@login_required
def delete_file(id, check_author=True):
    # print('id:')
    # get_single_data(id)
    s_data = get_db().execute(
        'SELECT p.id,author_id'
        ' FROM file p JOIN user u ON p.author_id = u.id'
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

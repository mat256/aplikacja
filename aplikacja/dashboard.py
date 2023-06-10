from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from aplikacja.auth import login_required
from aplikacja.db import get_db

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, TableColumn, DataTable, DateFormatter,HTMLTemplateFormatter
from bokeh.io import show

import random

import pygal
from aplikacja import files
import pandas as pd
from pygal.style import DarkStyle, DefaultStyle

import sqlite3
from flask_uploads import IMAGES, UploadSet, configure_uploads
import os

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def dashboard():
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
    source2 = ColumnDataSource(chart_data)

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
    p3 = figure( sizing_mode="scale_width", x_axis_type="datetime")
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

    formatter = HTMLTemplateFormatter()

    columns = [
        TableColumn(field='glucose', title='glucose'),
        TableColumn(field='custom_date', title='custom_date',  formatter=DateFormatter(format="%m/%d/%Y %H:%M:%S")),
    ]

    myTable = DataTable(source=source2, columns=columns, autosize_mode = 'fit_viewport')
    #show(myTable)
    #print(myTable)
    #print(components(myTable))
    script4, div4 = components(myTable)
    #print(div3)
    #print(div4)
    return render_template(
        'dashboard/main.html',
        script=[script1, script2, script3, script4],
        div=[div1, div2, div3, div4],
    )

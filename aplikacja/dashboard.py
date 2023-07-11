from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from aplikacja.auth import login_required
from aplikacja.db import get_db

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, TableColumn, DataTable, DateFormatter,HTMLTemplateFormatter,DatetimeTickFormatter,BoxAnnotation, Toggle
from bokeh.models.widgets import DataTable, StringFormatter, TableColumn
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

def create_avg_data(df):
    """  db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, created, stat, author_id'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    # print(all_data[0][0])
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'created', 'stat', 'author_id'])
    # print(df)
    df = df.filter(['glucose', 'custom_date'], axis=1)"""
    #print(df)
    #new=df.groupby(pd.Grouper(key='custom_date', axis=0, freq='15min', sort=True)).mean()
    #new = df.groupby(df["custom_date"].dt.hour)["glucose"].mean()
    #new['date']=list(new.index.values)

    df1 = df.set_index('custom_date')
    #print(df1)
    new=pd.DataFrame()
    #for i in pd.timedelta_range(start='1 day', end='2 days', freq='15min'):
        #print(str(i).split()[-1])
    #new["glucose"]=[df.between_time('0:15', str(x).split()[-1]) for x in pd.timedelta_range(start='1 day', end='2 days', freq='15min')]

    #print(df1.between_time('00:00:00', '01:00:00')['glucose'].mean())
    timing = [str(x).split()[-1] for x in pd.timedelta_range(start='1 day', end='2 days', freq='15min')]
    new['time']=timing[:-1]
    new['time'] = new['time'].apply(lambda x: f"2022-06-10 {x}")
    new['time'] = pd.to_datetime(new['time'])
    #print(timing)
    new["glucose"] = [df1.between_time(timing[x], timing[x+1])['glucose'].mean() for x in range(len(timing)-1)]
    new.fillna(method="bfill", inplace=True)
    #print(new)
    new['glucose'] = new['glucose'].astype(int)
    #print(list(new.columns.values))
    #print(list(new.index.values))
    #print(type(new['time'][0]))
    #print(new.to_string())
    return new

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
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'created', 'stat', 'author_id'])
    # print(df)
    chart_data = df.filter(['glucose', 'custom_date'], axis=1)
    chart_data.sort_values(by='custom_date', ascending=False, inplace=True)
    source = ColumnDataSource(create_avg_data(df))
    source2 = ColumnDataSource(chart_data)
    avg_g = int(df['glucose'].mean())
    proc_over = int(len(df[df["glucose"]>=180])/df.shape[0]*100)
    stat = [avg_g,proc_over]





    hover_tool = HoverTool(
        tooltips=[("Glucose", "@glucose"),
        ("Time", "@time{%T}")], mode='vline', formatters={"@time": "datetime"}
    )


    p3 = figure( sizing_mode="scale_width", x_axis_type="datetime")

    p3.add_tools(hover_tool)
    p3.line(
        x='time', y='glucose', source=source,
        line_width=3,
        color="darkblue",
        alpha=0.5
    )

    """super_low_box = BoxAnnotation(top=60, fill_alpha=0.1, fill_color='bisque')
    low_box = BoxAnnotation(bottom=60, top=75, fill_alpha=0.1, fill_color='cornsilk')
    mid_box = BoxAnnotation(bottom=75, top=140, fill_alpha=0.1, fill_color='honeydew')
    high_box = BoxAnnotation(bottom=140, top=180, fill_alpha=0.1, fill_color='cornsilk')
    super_high_box = BoxAnnotation(bottom=180, fill_alpha=0.1, fill_color='bisque')
    p3.add_layout(super_low_box)
    p3.add_layout(low_box)
    p3.add_layout(mid_box)
    p3.add_layout(high_box)
    p3.add_layout(super_high_box)"""

    #p3.xaxis[0].formatter = DatetimeTickFormatter(months="%b %Y")

    script1, div1 = components(p3)


    formatter = HTMLTemplateFormatter()

    columns = [
        TableColumn(field='glucose', title='glucose'),
        TableColumn(field='custom_date', title='custom_date',  formatter=DateFormatter(format="%m/%d/%Y %H:%M:%S")),
    ]

    myTable = DataTable(source=source2, columns=columns, autosize_mode = 'fit_viewport')
    #show(myTable)
    #print(myTable)
    #print(components(myTable))
    script2, div2 = components(myTable)
    #print(div3)
    #print(div4)
    return render_template(
        'dashboard/main.html',
        script=[script1],
        div=[div1],
        stat=stat,
    )


@bp.route('/glucose')
@login_required
def glucose():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, created, stat, f.author_id, f.name'
        ' FROM data p JOIN user u ON p.author_id = u.id JOIN file f ON p.file_id = f.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    #print(all_data[0][0])
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'created', 'stat', 'author_id', 'name'])

    #df['name'] = df['name'].astype('string')
    #print(df.dtypes)
    #print(df)
    #chart_data = df.filter(['glucose', 'custom_date'], axis=1)
    #chart_data=df
    df = df.drop_duplicates(subset=['id'])
    chart_data = df.filter(['id','glucose', 'custom_date','name', 'author_id'], axis=1)
    chart_data.insert(2, "info", ["inf" for x in range(df.shape[0])], True)
    chart_data.sort_values(by='custom_date', ascending=True, inplace=True)
    #chart_data['name'] = chart_data['name'].astype('string')
    #print(chart_data.dtypes)
    #print(chart_data.to_string())

    #print(chart_data.shape)
    source2 = ColumnDataSource(chart_data)

    hover_tool = HoverTool(
        tooltips=[("Glucose", "@glucose"),
                  ("Time", "@time{%T}")], mode='vline', formatters={"@time": "datetime"}
    )


    """super_low_box = BoxAnnotation(top=60, fill_alpha=0.1, fill_color='bisque')
    low_box = BoxAnnotation(bottom=60, top=75, fill_alpha=0.1, fill_color='cornsilk')
    mid_box = BoxAnnotation(bottom=75, top=140, fill_alpha=0.1, fill_color='honeydew')
    high_box = BoxAnnotation(bottom=140, top=180, fill_alpha=0.1, fill_color='cornsilk')
    super_high_box = BoxAnnotation(bottom=180, fill_alpha=0.1, fill_color='bisque')
    p3.add_layout(super_low_box)
    p3.add_layout(low_box)
    p3.add_layout(mid_box)
    p3.add_layout(high_box)
    p3.add_layout(super_high_box)"""

    # p3.xaxis[0].formatter = DatetimeTickFormatter(months="%b %Y")



    formatter = HTMLTemplateFormatter()

    columns = [
        TableColumn(field='info', title='info'),
        TableColumn(field='glucose', title='glucose'),
        #TableColumn(field='custom_date', title='custom_date', formatter=DateFormatter(format="%m/%d/%Y %H:%M:%S")),
        TableColumn(field='author_id', title='author_id'),
        #TableColumn(field='stat', title='stat'),
        #TableColumn(field='name', title='name'),


    ]

    myTable = DataTable(source=source2, columns=columns, autosize_mode='fit_columns',
                        reorderable = False
                        )

    # show(myTable)
    # print(myTable)
    # print(components(myTable))
    script, div = components(myTable)
    # print(div3)
    # print(div4)
    return render_template(
        'dashboard/glucose.html',
        script=[script],
        div=[div],
        data = all_data,
    )
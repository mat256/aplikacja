from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from datetime import date, timedelta
from math import pi
from aplikacja.auth import login_required
from aplikacja.db import get_db
from bokeh.layouts import gridplot
import datetime
from bokeh.models import Title

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, TableColumn, DataTable, DateFormatter,HTMLTemplateFormatter,DatetimeTickFormatter,BoxAnnotation, Toggle
from bokeh.models.widgets import DataTable, StringFormatter, TableColumn
from bokeh.transform import cumsum
from bokeh.palettes import Category10_10, Category20
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
    new['time'] = new['time'].apply(lambda x: f"1900-01-01 {x}")
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

    #print(all_data)
    if not all_data:
        #abort(404, f"Entry id {id} doesn't exist.")
        return render_template(
            'dashboard/main.html',
        script=None,
        div=None,
        stat=None,)


    # print(all_data[0][0])
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'created', 'stat', 'author_id'])

    all_data_ins = db.execute(
        'SELECT p.id, amount, period, type, custom_date, created, f.name'
        ' FROM insulin p JOIN user u ON p.author_id = u.id JOIN file f ON p.file_id = f.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()

    df_ins=pd.DataFrame(all_data_ins,
                      columns=['id', 'amount', ' period', 'type', 'custom_date', 'created', 'name'])
    # print(df)

    doses_per_day = df_ins[['amount','custom_date']].set_index('custom_date').groupby(pd.Grouper(freq='D')).count().mean()
    #print(data_ins.mean())
    amount_per_day=df_ins[['amount','custom_date']].groupby(pd.Grouper(key='custom_date',
                          freq='D')).sum().mean()

    #amount_per_day=float(amount_per_day)
    amount_per_day = float(amount_per_day.iloc[0])
    if amount_per_day.is_integer():
        amount_per_day=int(amount_per_day)

    doses_per_day = float(doses_per_day.iloc[0])
    if doses_per_day.is_integer():
        doses_per_day = int(doses_per_day)
    #print(s.mean())
    #ratio = (df < 1.0).sum()
    ratio = df['glucose'].value_counts(bins = [0,70, 120,180,500])
    num_of_values = df.shape[0]

    chart_data = df.filter(['glucose', 'custom_date'], axis=1)
    chart_data.sort_values(by='custom_date', ascending=False, inplace=True)
    source = ColumnDataSource(create_avg_data(df))
    source2 = ColumnDataSource(chart_data)
    avg_g = int(df['glucose'].mean())
    proc_over = int(len(df[df["glucose"]>=180])/df.shape[0]*100)
    stat = [avg_g,proc_over,amount_per_day,doses_per_day]
    #print(ratio.index)
    #print(ratio.sum())

    values = [x/num_of_values for x in ratio]
    ratio_proc=pd.DataFrame()
    ratio_proc['range'] = ['>180', '120-180', '70-120','<70']
    ratio_proc['value'] = pd.Series(values)*100
    ratio_proc['value']=ratio_proc['value'].astype(int)
    ratio_proc['angle'] = pd.Series(values) * 2 * pi
    ratio_proc['color'] = pd.Series(['lightcoral','moccasin','palegreen','paleturquoise'])
    p = figure(sizing_mode="scale_width", toolbar_location=None,
               outline_line_width=0 ,tools="hover", tooltips="@range: @value%")

    p.wedge(x=0, y=1, radius=0.9,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_width=0,fill_color='color', source=ratio_proc)
    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    script2, div2 = components(p)


    hover_tool = HoverTool(
        tooltips=[("Glucose", "@glucose"),
        ("Time", "@time{%T}")], mode='vline', formatters={"@time": "datetime"}
    )


    p3 = figure(height = 400,  sizing_mode="scale_width", x_axis_type="datetime")
    night_end = pd.Timestamp('1900-01-01T07')  # pd.Timedelta(hours=7)
    night_start = pd.Timestamp('1900-01-01T22')  # pd.Timedelta(hours=22)
    green_box1 = BoxAnnotation(right=night_end, fill_color='#009E73', fill_alpha=0.1)
    green_box2 = BoxAnnotation(left=night_start, fill_color='#009E73', fill_alpha=0.1)
    p3.add_layout(green_box1)
    p3.add_layout(green_box2)

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
    #script2, div2 = components(myTable)
    #print(div3)
    #print(div4)
    return render_template(
        'dashboard/main.html',
        script=[script1,script2],
        div=[div1,div2],
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

    all_data_ins = db.execute(
        'SELECT p.id, amount, period, type, custom_date, created, f.name'
        ' FROM insulin p JOIN user u ON p.author_id = u.id JOIN file f ON p.file_id = f.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()

    df_ins = pd.DataFrame(all_data_ins,
                          columns=['id', 'amount', ' period', 'type', 'custom_date', 'created', 'name'])
    # print(df)
    df = df.filter(['glucose', 'custom_date'], axis=1)
    df.sort_values(by='custom_date', ascending=False, inplace=True)

    df_ins = df_ins.filter(['amount','period','type', 'custom_date'], axis=1)
    df_ins.sort_values(by='custom_date', ascending=False, inplace=True)
    df_ins['val']=100

    #print(df_ins)
    today = date.today()
    choosen_date=today
    chart_data = df.loc[(df['custom_date'] >= str(today)+' 00:00:00')
                             & (df['custom_date'] < str(today) +' 23:59:59')]

    chart_data_2 = df_ins.loc[(df_ins['custom_date'] >= str(today) + ' 00:00:00')
                        & (df_ins['custom_date'] < str(today) + ' 23:59:59')]

    if request.method == 'POST':
        choosen_date = request.form['date']
        chart_data = df.loc[(df['custom_date'] >= choosen_date+' 00:00:00')
                             & (df['custom_date'] < choosen_date+' 23:59:59')]

        chart_data_2 = df_ins.loc[(df_ins['custom_date'] >= choosen_date+' 00:00:00')
                             & (df_ins['custom_date'] < choosen_date+' 23:59:59')]


    #chart_data_1 = chart_data[:100]
    #chart_data_2 = chart_data[100:]
    #print(chart_data)
    #print(chart_data_2)
    source = ColumnDataSource(chart_data)
    source2 = ColumnDataSource(chart_data_2)


    hover_tool = HoverTool(
        tooltips=[("glucose", "@glucose"),
        ("desc", "@custom_date{%T}")], mode='vline', formatters={"@custom_date": "datetime"}
    )

    p = figure(height=450, sizing_mode="stretch_width", x_axis_type="datetime")

    p1=p.line(
        x='custom_date', y='glucose', source=source,
        line_width=2,
        color="olive",
        alpha=0.5
    )
    p.add_tools(HoverTool(
        renderers=[p1],
        tooltips=[("glucose", "@glucose"),
        ("time", "@custom_date{%T}")], mode='vline', formatters={"@custom_date": "datetime"}
    ))
    p2=p.circle(x='custom_date', y='val', source=source2, size=10, color="sienna", alpha=0.5)


    p.add_tools(HoverTool(
        renderers=[p2],
        tooltips=[("amount", "@amount"),
                  ("period", "@period"),
                  ("time", "@custom_date{%T}")], mode='vline', formatters={"@custom_date": "datetime"}
    ))
    script, div = components(p)

    return render_template(
        'dashboard/graph.html',
        script=[script],
        div=[div],
        date=choosen_date
    )

def create_plots(days):
    plots=[]
    hover_tool = HoverTool(
        tooltips=[("glucose", "@glucose"),
                  ("time", "@custom_date{%T}")], mode='vline', formatters={"@custom_date": "datetime"}
    )


    for n,i in enumerate(days):
        a1 = figure(x_axis_type="datetime")
        a1.line(x='custom_date', y='glucose', source=days[n][1], line_width=3, alpha=0.6)
        #print(days[n][0])
        #print(type(days[n][0]))
        #print(days[n][0]+ pd.Timedelta(hours=5, minutes=10, seconds=3))
        night_end = days[n][0]+ pd.Timedelta(hours=7)
        night_start = days[n][0]+ pd.Timedelta(hours=22)
        green_box1 = BoxAnnotation(right=night_end, fill_color='#009E73', fill_alpha=0.1)
        green_box2 = BoxAnnotation(left=night_start, fill_color='#009E73', fill_alpha=0.1)
        a1.xaxis[0].formatter = DatetimeTickFormatter(hourmin="%H:%M")
        a1.add_layout(green_box1)
        a1.add_layout(green_box2)
        a1.add_tools(hover_tool)
        a1.add_layout(Title(text=str(datetime.datetime.date(days[n][0])), align="center"), "above")
        plots.append(a1)
    return plots

@bp.route('/lastweeks', methods=('GET', 'POST'))
@login_required
def twoWeeksGraph():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, stat, author_id'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ? and custom_date>=date("now","-14 day")'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'stat', 'author_id'])

    all_data_ins = db.execute(
        'SELECT p.id, amount, period, type, custom_date, created, f.name'
        ' FROM insulin p JOIN user u ON p.author_id = u.id JOIN file f ON p.file_id = f.id'
        ' WHERE p.author_id = ? and custom_date>=date("now","-14 day")'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()

    df_ins = pd.DataFrame(all_data_ins,
                          columns=['id', 'amount', ' period', 'type', 'custom_date', 'created', 'name'])
    #print(df)
    df = df.filter(['glucose', 'custom_date'], axis=1)
    df.sort_values(by='custom_date', ascending=False, inplace=True)

    df_ins = df_ins.filter(['amount','period','type', 'custom_date'], axis=1)
    df_ins.sort_values(by='custom_date', ascending=False, inplace=True)
    df_ins['val']=100

    #print(df_ins)
    p = figure(height=450, sizing_mode="stretch_width", x_axis_type="datetime")
    #df['date'] = pd.to_datetime(df["date"].dt.strftime('%Y-%m'))
    single_days = df.groupby(pd.Grouper(key='custom_date',freq='D'))
    days = [i for i in single_days]

    grid = gridplot(create_plots(days), ncols=2, height=250,sizing_mode="stretch_width")


    color = Category10_10.__iter__()
    for i in single_days:
        #print(i[0])
        #print(type(i))
        single = i[1]
        single.loc[:, 'custom_date'] = pd.to_datetime(single.loc[:, 'custom_date'].dt.strftime('%H:%M:%S'), format="%H:%M:%S")
        line = p.line(
            x='custom_date', y='glucose', source=single,
            line_width=2,
            color = next(color),
            alpha=0.5
        )
        #print(i)
        #print('---')
    #plots = [figure().line(x='custom_date', y='glucose', source=i[1],line_width=2,alpha=0.5) for i in single_days]
    #for i in single_days:
       #print(i)
    #print(single_days.first())
    night_end = pd.Timestamp('1900-01-01T07')#pd.Timedelta(hours=7)
    night_start = pd.Timestamp('1900-01-01T22')#pd.Timedelta(hours=22)
    green_box1 = BoxAnnotation(right=night_end, fill_color='#009E73', fill_alpha=0.1)
    green_box2 = BoxAnnotation(left=night_start, fill_color='#009E73', fill_alpha=0.1)
    p.add_layout(green_box1)
    p.add_layout(green_box2)

    p.xaxis[0].formatter = DatetimeTickFormatter(hourmin ="%H:%M")

    hover_tool = HoverTool(
        tooltips=[
        ("TIme", "@custom_date{%T}")], mode='vline', formatters={"@custom_date": "datetime"}
        , renderers=[line]
    )
    p.add_tools(hover_tool)
    today = date.today()
    choosen_date = today
    script, div = components(p)
    script1, div1 = components(grid)

    return render_template(
        'dashboard/lastweeks.html',
        script=[script,script1],
        div=[div,div1],
        date=choosen_date
    )
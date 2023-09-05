from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, send_file
)
from werkzeug.exceptions import abort
from datetime import date, timedelta, datetime
from math import pi
from aplikacja.auth import login_required
from aplikacja.db import get_db
from bokeh.layouts import gridplot
import datetime
from bokeh.models import Title
from fpdf import FPDF
import io
import uuid
import os

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, TableColumn, DataTable, DateFormatter, HTMLTemplateFormatter, \
    DatetimeTickFormatter, BoxAnnotation, Toggle
from bokeh.models.widgets import DataTable, StringFormatter, TableColumn
from bokeh.transform import cumsum
from bokeh.palettes import Category10_10, Category20
from bokeh.models import TabPanel, Tabs
from bokeh.models import CheckboxGroup, CustomJS
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


def create_avg_data(df,date='1900-01-01'):
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
    # print(df)
    # new=df.groupby(pd.Grouper(key='custom_date', axis=0, freq='15min', sort=True)).mean()
    # new = df.groupby(df["custom_date"].dt.hour)["glucose"].mean()
    # new['date']=list(new.index.values)

    df1 = df.set_index('custom_date')
    # print(df1)
    new = pd.DataFrame()
    # for i in pd.timedelta_range(start='1 day', end='2 days', freq='15min'):
    # print(str(i).split()[-1])
    # new["glucose"]=[df.between_time('0:15', str(x).split()[-1]) for x in pd.timedelta_range(start='1 day', end='2 days', freq='15min')]

    # print(df1.between_time('00:00:00', '01:00:00')['glucose'].mean())
    timing = [str(x).split()[-1] for x in pd.timedelta_range(start='1 day', end='2 days', freq='15min')]
    new['time'] = timing[:-1]
    new['orginal_time'] = timing[:-1]
    new['time'] = new['time'].apply(lambda x: f"'1900-01-01' {x}")
    new['orginal_time'] = new['orginal_time'].apply(lambda x: f"{date} {x}")
    new['time'] = pd.to_datetime(new['time'])
    # print(timing)
    new["glucose"] = [df1.between_time(timing[x], timing[x + 1])['glucose'].mean() for x in range(len(timing) - 1)]
    new.fillna(method="bfill", inplace=True)
    #print(new)
    new['glucose'] = new['glucose'].astype(int)
    # print(list(new.columns.values))
    # print(list(new.index.values))
    # print(type(new['time'][0]))
    # print(new.to_string())
    return new


def getStartEnd(db, id):
    data = db.execute(
        'SELECT day_start,day_end'
        ' FROM personal p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?', (id,)
    ).fetchall()
    if not data:
        return ['07:00', '23:00']
    return list(data[0])


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

    # print(all_data)
    if not all_data:
        # abort(404, f"Entry id {id} doesn't exist.")
        flash('User needs to upload glucose data.', 'alert alert-danger')
        return render_template(
            'dashboard/main.html',
            script=None,
            div=None,
            stat=None, )

    # print(all_data[0][0])
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'created', 'stat', 'author_id'])

    all_data_ins = db.execute(
        'SELECT p.id, amount, period, type, custom_date, created'
        ' FROM insulin p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ?'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()

    if not all_data_ins:
        # abort(404, f"Entry id {id} doesn't exist.")
        flash('User needs to upload insulin data.', 'alert alert-danger')
        return render_template(
            'dashboard/main.html',
            script=None,
            div=None,
            stat=None, )

    df_ins = pd.DataFrame(all_data_ins,
                          columns=['id', 'amount', ' period', 'type', 'custom_date', 'created'])
    # print(df)

    doses_per_day = df_ins[['amount', 'custom_date']].set_index('custom_date').groupby(
        pd.Grouper(freq='D')).count().mean()
    # print(data_ins.mean())
    amount_per_day = df_ins[['amount', 'custom_date']].groupby(pd.Grouper(key='custom_date',
                                                                          freq='D')).sum().mean()

    # amount_per_day=float(amount_per_day)
    amount_per_day = round(float(amount_per_day.iloc[0]), 2)
    if amount_per_day.is_integer():
        amount_per_day = int(amount_per_day)

    doses_per_day = round(float(doses_per_day.iloc[0]), 2)
    if doses_per_day.is_integer():
        doses_per_day = int(doses_per_day)
    # print(s.mean())
    # ratio = (df < 1.0).sum()
    ratio = df['glucose'].value_counts(bins=[0, 70, 120, 180, 500])
    num_of_values = df.shape[0]

    chart_data = df.filter(['glucose', 'custom_date'], axis=1)
    chart_data.sort_values(by='custom_date', ascending=False, inplace=True)
    source = ColumnDataSource(create_avg_data(df))
    source2 = ColumnDataSource(chart_data)
    avg_g = int(df['glucose'].mean())
    proc_over = int(len(df[df["glucose"] >= 180]) / df.shape[0] * 100)
    stat = [avg_g, proc_over, amount_per_day, doses_per_day]
    # print(ratio.index)
    # print(ratio.sum())

    values = [x / num_of_values for x in ratio]
    ratio_proc = pd.DataFrame()
    ratio_proc['range'] = ['>180', '120-180', '70-120', '<70']
    ratio_proc['value'] = pd.Series(values) * 100
    ratio_proc['value'] = ratio_proc['value'].astype(int)
    ratio_proc['angle'] = pd.Series(values) * 2 * pi
    ratio_proc['color'] = pd.Series(['lightcoral', 'moccasin', 'palegreen', 'paleturquoise'])
    p = figure(sizing_mode="scale_width", toolbar_location=None,
               outline_line_width=0, tools="hover", tooltips="@range: @value%")

    p.wedge(x=0, y=1, radius=0.9,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_width=0, fill_color='color', source=ratio_proc)
    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    script2, div2 = components(p)

    hover_tool = HoverTool(
        tooltips=[("Glucose", "@glucose"),
                  ("Time", "@time{%T}")], mode='vline', formatters={"@time": "datetime"}
    )

    p3 = figure(height=400, sizing_mode="scale_width", x_axis_type="datetime")

    dstart, dend = getStartEnd(db, g.user['id'])
    night_end = pd.Timestamp('1900-01-01T' + dstart[:2])  # pd.Timedelta(hours=7)
    night_start = pd.Timestamp('1900-01-01T' + dend[:2])  # pd.Timedelta(hours=22)
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

    # p3.xaxis[0].formatter = DatetimeTickFormatter(months="%b %Y")

    script1, div1 = components(p3)

    formatter = HTMLTemplateFormatter()

    columns = [
        TableColumn(field='glucose', title='glucose'),
        TableColumn(field='custom_date', title='custom_date', formatter=DateFormatter(format="%m/%d/%Y %H:%M:%S")),
    ]

    myTable = DataTable(source=source2, columns=columns, autosize_mode='fit_viewport')
    # show(myTable)
    # print(myTable)
    # print(components(myTable))
    # script2, div2 = components(myTable)
    # print(div3)
    # print(div4)
    return render_template(
        'dashboard/main.html',
        script=[script1, script2],
        div=[div1, div2],
        stat=stat,
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
                          columns=['id', 'amount', 'period', 'type', 'custom_date', 'created', 'name'])
    # print(df_ins)
    df = df.filter(['glucose', 'custom_date'], axis=1)
    df.sort_values(by='custom_date', ascending=False, inplace=True)

    df_ins = df_ins.filter(['amount', 'period', 'type', 'custom_date'], axis=1)
    # print(df_ins)
    df_ins.sort_values(by='custom_date', ascending=False, inplace=True)
    df_ins['val'] = 100
    df_ins.loc[df_ins.type=='base', 'val'] = 50

    # print(df_ins)
    today = date.today()
    choosen_date = today
    chart_data = df.loc[(df['custom_date'] >= str(today) + ' 00:00:00')
                        & (df['custom_date'] < str(today) + ' 23:59:59')]

    chart_data_2 = df_ins.loc[(df_ins['custom_date'] >= str(today) + ' 00:00:00')
                              & (df_ins['custom_date'] < str(today) + ' 23:59:59')]

    if request.method == 'POST':
        choosen_date = request.form['date']
        chart_data = df.loc[(df['custom_date'] >= choosen_date + ' 00:00:00')
                            & (df['custom_date'] < choosen_date + ' 23:59:59')]

        chart_data_2 = df_ins.loc[(df_ins['custom_date'] >= choosen_date + ' 00:00:00')
                                  & (df_ins['custom_date'] < choosen_date + ' 23:59:59')]

    # chart_data_1 = chart_data[:100]
    # chart_data_2 = chart_data[100:]
    # print(chart_data)
    # print(chart_data_2)
    source = ColumnDataSource(chart_data)
    source2 = ColumnDataSource(chart_data_2)
    # print(chart_data_2)

    p = figure(height=450, sizing_mode="stretch_width", x_axis_type="datetime")

    p1 = p.line(
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
    p2 = p.circle(x='custom_date', y='val', source=source2, size=10, color="sienna", alpha=0.5)

    p.add_tools(HoverTool(
        renderers=[p2],
        tooltips=[("amount", "@amount"),
                  ("period", "@period h"),
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
    plots = []
    hover_tool = HoverTool(
        tooltips=[("glucose", "@glucose"),
                  ("time", "@custom_date{%T}")], mode='vline', formatters={"@custom_date": "datetime"}
    )

    for n, i in enumerate(days):
        a1 = figure(x_axis_type="datetime")
        a1.line(x='custom_date', y='glucose', source=days[n][1], line_width=3, alpha=0.6)
        # print(days[n][0])
        # print(type(days[n][0]))
        # print(days[n][0]+ pd.Timedelta(hours=5, minutes=10, seconds=3))
        night_end = days[n][0] + pd.Timedelta(hours=7)
        night_start = days[n][0] + pd.Timedelta(hours=22)
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
        'SELECT p.id, amount, period, type, custom_date, created'
        ' FROM insulin p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ? and custom_date>=date("now","-14 day")'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()

    if not all_data or not all_data_ins:
        return redirect(url_for('dashboard.dashboard'))

    df_ins = pd.DataFrame(all_data_ins,
                          columns=['id', 'amount', ' period', 'type', 'custom_date', 'created'])
    # print(df)
    df = df.filter(['glucose', 'custom_date'], axis=1)
    df.sort_values(by='custom_date', ascending=False, inplace=True)

    df_ins = df_ins.filter(['amount', 'period', 'type', 'custom_date'], axis=1)
    df_ins.sort_values(by='custom_date', ascending=False, inplace=True)
    df_ins['val'] = 100

    # print(df_ins)
    p = figure(height=450, sizing_mode="stretch_width", x_axis_type="datetime")
    # df['date'] = pd.to_datetime(df["date"].dt.strftime('%Y-%m'))
    single_days = df.groupby(pd.Grouper(key='custom_date', freq='D'))
    days = [i for i in single_days]

    grid = gridplot(create_plots(days), ncols=2, height=250, sizing_mode="stretch_width")

    color = Category10_10.__iter__()
    for i in single_days:
        # print(i[0])
        # print(type(i))
        single = i[1]
        single.loc[:, 'custom_date'] = pd.to_datetime(single.loc[:, 'custom_date'].dt.strftime('%H:%M:%S'),
                                                      format="%H:%M:%S")
        line = p.line(
            x='custom_date', y='glucose', source=single,
            line_width=2,
            color=next(color),
            alpha=0.5
        )
        # print(i)
        # print('---')
    # plots = [figure().line(x='custom_date', y='glucose', source=i[1],line_width=2,alpha=0.5) for i in single_days]
    # for i in single_days:
    # print(i)
    # print(single_days.first())
    night_end = pd.Timestamp('1900-01-01T07')  # pd.Timedelta(hours=7)
    night_start = pd.Timestamp('1900-01-01T22')  # pd.Timedelta(hours=22)
    green_box1 = BoxAnnotation(right=night_end, fill_color='#009E73', fill_alpha=0.1)
    green_box2 = BoxAnnotation(left=night_start, fill_color='#009E73', fill_alpha=0.1)
    p.add_layout(green_box1)
    p.add_layout(green_box2)

    p.xaxis[0].formatter = DatetimeTickFormatter(hourmin="%H:%M")

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
        script=[script, script1],
        div=[div, div1],
        date=choosen_date
    )


@bp.route('/base', methods=('GET', 'POST'))
@login_required
def base():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, stat, author_id'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ? and custom_date>=date("now","-14 day")'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    if not all_data:
        # abort(404, f"Entry id {id} doesn't exist.")
        flash('User needs to upload glucose data.', 'alert alert-danger')
        return redirect(url_for('dashboard.dashboard'))
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'stat', 'author_id'])

    all_data_ins = db.execute(
        'SELECT p.id, amount, type, custom_date'
        ' FROM insulin p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ? and custom_date>=date("now","-14 day") and p.type="base"'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()

    if not all_data_ins:
        # abort(404, f"Entry id {id} doesn't exist.")
        flash('User needs to upload insulin data.', 'alert alert-danger')
        return redirect(url_for('dashboard.dashboard'))

    df_ins = pd.DataFrame(all_data_ins,
                          columns=['id', 'amount', 'type', 'custom_date'])
    grouped = df_ins.groupby(pd.Grouper(key='custom_date', freq='D'))
    for name, group in grouped:
        if group.shape[0] == 24:
            # print(group['custom_date'][1].time())
            group['custom_date'] = group['custom_date'].apply(lambda x: f"1900-01-01 {x.time()}")
            group['custom_date'] = pd.to_datetime(group['custom_date'])
            group['val'] = group['amount']*50
            #group['amount'] = group['amount']*50
            # print(type(group))
            # print(group)
            break


    #print(create_avg_data(df))
    source = ColumnDataSource(create_avg_data(df))
    source2 = ColumnDataSource(group)

    p = figure(height=450, sizing_mode="stretch_width", x_axis_type="datetime")
    p1 = p.line(
        x='time', y='glucose', source=source,
        line_width=2,
        color="brown",
        alpha=0.5
    )
    p.add_tools(HoverTool(
        renderers=[p1],
        tooltips=[("glucose", "@glucose"),
                  ("time", "@time{%T}")], mode='vline', formatters={"@time": "datetime"}
    ))
    #p2 = p.line(x='custom_date', y='val', source=source2, line_width=2, color="olive", alpha=0.5)
    #p2 = p.circle(x='custom_date', y='val', source=source2, size=10, color="sienna", alpha=0.5)
    p2 = p.vbar(x='custom_date', top='val', source=source2, width=3000000, color="darkblue")

    p.add_tools(HoverTool(
        renderers=[p2],
        tooltips=[("amount", "@amount{0.00}"),
                  ("time", "@custom_date{%T}")], mode='vline', formatters={"@custom_date": "datetime"}
    ))

    dstart, dend = getStartEnd(db, g.user['id'])
    night_end = pd.Timestamp('1900-01-01T' + dstart[:2])  # pd.Timedelta(hours=7)
    night_start = pd.Timestamp('1900-01-01T' + dend[:2])  # pd.Timedelta(hours=22)
    green_box1 = BoxAnnotation(right=night_end, fill_color='#009E73', fill_alpha=0.1)
    green_box2 = BoxAnnotation(left=night_start, fill_color='#009E73', fill_alpha=0.1)
    p.add_layout(green_box1)
    p.add_layout(green_box2)

    script1, div1 = components(p)



    return render_template(
        'dashboard/base.html',
        script=[script1],
        div=[div1],
    )

def createAvgPlots(df,freq):
    grouped = df.groupby(pd.Grouper(key='custom_date', freq=freq))
    p = figure(height=450, min_width=800, sizing_mode="stretch_width", x_axis_type="datetime")
    i=0
    color = Category10_10.__iter__()
    for name,group in grouped:
        if i==6:
            break
        i+=1
        if group.shape[0]>50:
            single = create_avg_data(group,name.date())
            line = p.line(
                x='time', y='glucose', source=single,
                line_width=3,
                color=next(color),
                alpha=0.5
            )

    date = "@orginal_time{%F}"
    if freq=='M':
        date = "@orginal_time{%b}"
    hover_tool = HoverTool(
        tooltips=[
            ("Time", "@orginal_time{%T}"),("Date", date)], mode='mouse', formatters={"@orginal_time": "datetime"}

    )
    p.add_tools(hover_tool)
    return p



@bp.route('/compare', methods=('GET', 'POST'))
@login_required
def compare():
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, stat, author_id'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ? and custom_date>=date("now","-6 months")'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    if not all_data:
        # abort(404, f"Entry id {id} doesn't exist.")
        flash('User needs to upload glucose data.', 'alert alert-danger')
        return redirect(url_for('dashboard.dashboard'))
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'stat', 'author_id'])

    freq_list = [('D','Days'),('W','Weeks'),('M','Months')]


    #script1, div1 = components(createAvgPlots(df,'M'))
    tabs = [TabPanel(child=createAvgPlots(df, f), title=name) for f,name in freq_list]
    p3 = Tabs(tabs=tabs)

    script1, div1 = components(p3)

    return render_template(
        'dashboard/compare.html',
        script=[script1],
        div=[div1],
    )


title = 'User information report'
class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Calculate width of title and position
        w = self.get_string_width(title) + 6
        #self.set_x((210 - w) / 2)
        # Colors of frame, background and text
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 230)
        #self.set_text_color(220, 50, 50)
        # Thickness of frame (1 mm)
        self.set_line_width(1)
        # Title
        date = datetime.date.today()
        self.cell(0, 9, title, 0, 1, 'C', 1)
        self.set_font('Arial', 'B', 12)
        self.cell(0, 9, 'date: ' + str(date), 0, 1, 'R', 0)
        # Line break
        self.ln(10)

    def part_name(self,name):
        # Arial bold 15
        self.set_font('Arial', 'B', 12)
        # Calculate width of title and position
        w = self.get_string_width(title) + 6
        #self.set_x((210 - w) / 2)
        # Colors of frame, background and text
        self.set_draw_color(230, 230, 230)
        #self.set_fill_color(230, 230, 230)
        #self.set_text_color(220, 50, 50)
        # Thickness of frame (1 mm)
        self.set_line_width(1)
        # Title
        #date = datetime.date.today()
        self.cell(0, 9, name, 1, 1, 'L', 0)
        #self.cell(0, 9, 'date: ' + str(date), 0, 1, 'R', 0)
        # Line break
        self.ln(5)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Text color in gray
        self.set_text_color(128)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def column1(self,text):
        self.cell(10, 7, '', 0, 0, 'L', 0)
        self.cell(100, 7, text, 0, 0, 'L', 0)

    def column2(self, text):
            self.cell(0, 7, text, 0, 1, 'L', 0)

def partPersonal(p):
    p.part_name('Personal info')
    db=get_db()
    data = db.execute(
        'SELECT name, surname, pesel, birth_date, phone, email'
        ' FROM personal p'
        ' WHERE p.user_id = ?', (g.user['id'],)
    ).fetchone()
    p.column1('Name: ' + str(data['name']))
    p.column2('Surname: ' + str(data['surname']))
    p.column1('Pesel: ' + str(data['pesel']))
    p.column2('Birth date: ' + str(data['birth_date']))
    p.column1('Phone: ' + str(data['phone']))
    p.column2('Email: ' + str(data['email']))

def partGlucose(p):
    p.part_name('Glucose info')
    db = get_db()
    all_data = db.execute(
        'SELECT p.id, glucose, activity, info, custom_date, stat, author_id'
        ' FROM data p JOIN user u ON p.author_id = u.id'
        ' WHERE p.author_id = ? and custom_date>=date("now","-14 day")'
        ' ORDER BY created DESC', (g.user['id'],)
    ).fetchall()
    df = pd.DataFrame(all_data,
                      columns=['id', 'glucose', ' activity', 'info', 'custom_date', 'stat', 'author_id'])


    df = df.filter(['glucose', 'custom_date'], axis=1)
    df.sort_values(by='custom_date', ascending=False, inplace=True)
    source = ColumnDataSource(create_avg_data(df))
    p3 = figure(height=400, width=800, x_axis_type="datetime")
    dstart, dend = getStartEnd(db, g.user['id'])
    night_end = pd.Timestamp('1900-01-01T' + dstart[:2])  # pd.Timedelta(hours=7)
    night_start = pd.Timestamp('1900-01-01T' + dend[:2])  # pd.Timedelta(hours=22)
    green_box1 = BoxAnnotation(right=night_end, fill_color='#009E73', fill_alpha=0.1)
    green_box2 = BoxAnnotation(left=night_start, fill_color='#009E73', fill_alpha=0.1)
    p3.add_layout(green_box1)
    p3.add_layout(green_box2)
    p3.line(
        x='time', y='glucose', source=source,
        line_width=3,
        color="darkblue",
        alpha=0.5
    )
    p3.legend.click_policy = "hide"
    from bokeh.io import export_png
    export_png(p3, filename="plot.png")



@bp.route('/download', methods=('GET', 'POST'))
@login_required
def download():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    if request.method == 'POST':
        if request.form.get('personal'):
            partPersonal(pdf)
        if request.form.get('glucose'):
            partGlucose(pdf)
        if request.form.get('base'):
            print('ok')
    pdf.set_title(title)
    #pdf.cell(40, 10, 'Hello World!')

    name = uuid.uuid4().hex
    file_path = 'temp_files/' + name + '.pdf'
    pdf.output(name = file_path)
    return_data = io.BytesIO()
    with open(file_path, 'rb') as fo:
        return_data.write(fo.read())
    # (after writing, cursor will be at last byte, so move it to start)
    return_data.seek(0)

    os.remove(file_path)
    #print(file.decode(encoding='latin-1'))
    #upload = Upload.query.filter_by(id=upload_id).first()
    return send_file(return_data, mimetype='application/pdf', download_name='report.pdf')
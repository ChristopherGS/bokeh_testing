import pandas as pd
import numpy as np
from bokeh.io import output_notebook, push_notebook, show, curdoc
from bokeh.layouts import row, column, widgetbox, gridplot, layout
from bokeh.plotting import figure, ColumnDataSource, curdoc
from bokeh.models import BoxAnnotation, Span, Title, Label, HoverTool, Legend, ColumnDataSource
from bokeh.models.widgets import (Button, RadioButtonGroup, Select, Slider,
                                  CheckboxButtonGroup, DataTable, DateFormatter, TableColumn)

from bokeh.models.callbacks import CustomJS

import datetime
import time
from random import randint

# Prepare the data
df = pd.read_csv('abort_rate.csv', index_col=0, parse_dates=['date'])

df['date_string'] = df['date'].apply(lambda date: date.strftime('%Y-%m-%d'))
df.drop(['Unnamed: 3'], axis=1, inplace=True)

df['dc_51_count'] = df['count'].apply(lambda count: count * 5)

# Prepare the charts and widgets

date_selection = df['date_string']

# These timeframes are not correct, more to demonstrate functionality
timeframe_options = {
    "Q1 2017": (datetime.datetime(2017, 3, 21) - datetime.timedelta(days=60)).date(),
    "Last 6 Months": (datetime.datetime(2017, 3, 21) - datetime.timedelta(days=230)).date(),
    "This Year": (datetime.datetime(2017, 3, 21) - datetime.timedelta(days=365)).date(),
    "All Time": df['date_string'].iloc[-1]
}

dc_options = {
    "All": ['count', 'dc_51_count'],
    "DC_50": ['count'],
    "DC_51": ['dc_51_count'],
}

timeframe = Select(title="Timeframe", options=sorted(timeframe_options.keys()), value="All Time")

radios = RadioButtonGroup(labels=sorted(dc_options.keys()), active=1)

alert_slider = Slider(title="Number of alerts", start=0, end=800, value=0, step=1)

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(
    data=dict(
        x=df['date'],
        y=df['count'],
        DateString=df['date_string'],
    )
)

dc_51_source = ColumnDataSource(
    data=dict(
        x=df['date'],
        y=df['dc_51_count'],
        DateString=df['date_string'],
    )
)

hover = HoverTool(
    tooltips=[
        ("Date", "@DateString"),
        ("Count", "$y"),
    ]
)

my_plot = figure(x_axis_type="datetime", plot_width=800, plot_height=400, tools=[hover])
dc_50_line = my_plot.line('x', 'y', line_color="gray", line_width=1, legend="DC_50", source=source)
dc_51_line = my_plot.line('x', 'y', line_color="green", line_width=1, legend="DC_51", source=dc_51_source)

ok_box = BoxAnnotation(bottom=-10, top=20, fill_alpha=0.1, fill_color='green')
alert_box = BoxAnnotation(bottom=21, fill_alpha=0.1, fill_color='red')

my_plot.add_layout(ok_box)
my_plot.add_layout(alert_box)

my_plot.title.text = "Abort Trigger Rate"
my_plot.xgrid[0].grid_line_color = None
my_plot.ygrid[0].grid_line_alpha = 0.5
my_plot.xaxis.axis_label = 'Date'
my_plot.yaxis.axis_label = 'Count'


def select_dates():
    timeframe_value = timeframe_options[timeframe.value]
    selected = df[(df.date >= (pd.to_datetime(timeframe_value, dayfirst=True)))]

    return selected


def update(attr=None, old=None, new=None):
    df = select_dates()

    x_name = timeframe_options[timeframe.value]
    my_plot.xaxis.axis_label = timeframe.value

    source.data = dict(
        x=df['date'],
        y=df['count'],
        DateString=df['date_string'],
    )

    table_source.data = dict(
        dates=df['date'],
        count=df['count']
    )


timeframe.on_change('value', lambda attr, old, new: update(attr, old, new))
# radios.on_change('active', lambda attr, old, new: update(attr, old, new))


radios.callback = CustomJS(args=dict(line0=dc_50_line, line1=dc_51_line), code="""
    console.log(cb_obj.active);
    line0.visible = false;
    line1.visible = false;
    if (cb_obj.active == 1) {
        line1.visible = false;
        line0.visible = true;
    } else if (cb_obj.active == 2){
        line1.visible = true;
        line0.visible = false;
    } else if (cb_obj.active == 0){
        line1.visible = true;
        line0.visible = true;
    }
    """)

# Datatable functionality
table_data = dict(
    dates=df['date'],
    count=df['count']
)
table_source = ColumnDataSource(table_data)

columns = [
    TableColumn(field="dates", title="Date", formatter=DateFormatter()),
    TableColumn(field="count", title="Abort Count"),
]
data_table = DataTable(source=table_source, columns=columns, width=400, height=280)

# Structure the widgets/charts in a layout

show(widgetbox(data_table))

inputs = widgetbox([timeframe, radios])
l = layout([
    [inputs, my_plot],
    [data_table],
])

update()

# Add the layout to curdoc
curdoc().add_root(l)
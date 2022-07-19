from dash import Dash, dcc, html, Input, Output, dash_table
from datetime import date, datetime
from dkbl.dkbl import _distribute_occurences, _handle_import
import os
import pathlib
import plotly.express as px
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta
import datetime


def style_chart(fig, style):
    if style == "vbar":
        fig.update_xaxes(showgrid=False, gridcolor=color_scheme["font"], zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor=color_scheme["font"], zeroline=False)
        fig.update_layout(yaxis_ticksuffix="€", yaxis_tickformat=",.")
    elif style == "bar":
        fig.update_xaxes(showgrid=True, gridcolor=color_scheme["font"], zeroline=False)
        fig.update_yaxes(showgrid=False, gridcolor=color_scheme["font"], zeroline=False)
        fig.update_layout(xaxis_ticksuffix="€", xaxis_tickformat=",.")
    elif style == "line":
        fig.update_xaxes(showgrid=False, gridcolor=color_scheme["font"], zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor=color_scheme["font"], zeroline=False)
        fig.update_layout(yaxis_ticksuffix="€", yaxis_tickformat=",.")

    fig.update_layout(
        yaxis_title=None,
        xaxis_title=None,
        font_color=color_scheme["font"],
        title_font_color=color_scheme["font"],
        legend_title_font_color=color_scheme["font"],
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="rgba(0, 0, 0, 0)",
    )
    fig.update_traces(marker=dict(line=dict(width=0)))

    return fig


def add_timecols(df):
    if "date" in df.columns:
        for col in ["week", "month", "quarter", "year"]:
            df[col] = (
                pd.to_datetime(df.date).dt.to_period(col.upper()[0]).dt.to_timestamp()
            )
        return df
    elif "date_custom" in df.columns:
        for col in ["week", "month", "quarter", "year"]:
            df[col] = (
                pd.to_datetime(df.date_custom)
                .dt.to_period(col.upper()[0])
                .dt.to_timestamp()
            )
    return df


semanticui_js = [
    "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.js",
    "/assets/index.js",
]
semanticui_css = [
    "https://cdnjs.cloudflare.com/ajax/libs/semantic-ui/2.4.1/semantic.min.css"
]


# dracula:
color_scheme = {
    "bg": "#282A36",
    "red": "#FF5555",
    "green": "#50FA7B",
    "hl": "#8BE9FD",
    "font": "#F8F8F2",
}

# regular
# color_scheme = {"bg":"#f3f3f3","red":"#ff0000","green":"#00ff00","hl":"#148dea","font":"#000000"}
ei_colors = {"Expense": color_scheme["red"], "Income": color_scheme["green"]}

app = Dash(
    __name__, external_stylesheets=semanticui_css, external_scripts=semanticui_js
)
app.layout = html.Div(
    [
        html.Div(
            [
                # menu
                html.Div(
                    [
                        html.Div(
                            [
                                html.Br(),
                                html.Div(
                                    [
                                        html.A(
                                            "Overview",
                                            className="inverted item",
                                            href="#overview",
                                        ),
                                        html.A(
                                            "Categories",
                                            className="item",
                                            href="#categories",
                                        ),
                                        html.A(
                                            "NN / ES", className="item", href="#nnes"
                                        ),
                                        html.A(
                                            "About", className="item", href="#about"
                                        ),
                                    ],
                                    className="ui vertical menu",
                                ),
                            ],
                            className="ui fixed sticky",
                        )
                    ],
                    className="ui container",
                ),
            ],
            className="three wide column",
        ),
        html.Div(
            [
                html.Div(
                    [html.Div([html.H1("DKBL Viz")])], className="ui centered grid"
                ),
                # overview
                html.H4(
                    [html.I(className="tag icon"), " Overview"],
                    id="overview",
                    className="ui horizontal divider",
                ),
                dcc.Checklist(
                    [
                        "date",
                        "recipient_clean",
                        "amount",
                        "occurence",
                        "label1",
                        "label2",
                        "label3",
                    ],
                    id="coalesce_input",
                    inline=False,
                    labelStyle=dict(display="block"),
                ),
                html.Br(),
                dcc.DatePickerRange(
                    id="ovw_timerange",
                    # min_date_allowed=date(2020,10,1),
                    # max_date_allowed=date(2022, 6, 18),
                    # start_date =date(2020,10,1),
                    # end_date=date(2022, 6, 18)
                ),
                html.Div(
                    html.Div(
                        [
                            html.Div(dcc.Graph(id="netio_fig"), className="column"),
                            html.Div(dcc.Graph(id="io_fig"), className="column"),
                            html.Div(dcc.Graph(id="history"), className="column"),
                        ],
                        className="three column row",
                    ),
                    className="ui grid",
                ),
                # categories
                html.H4(
                    [html.I(className="file alternate icon"), " Categories"],
                    id="categories",
                    className="ui horizontal divider",
                ),
                dcc.DatePickerRange(
                    id="cat_timerange",
                    # min_date_allowed=date(2022,3,1),
                    # max_date_allowed=date(2022, 5, 31),
                    # initial_visible_month=date(2022, 6, 18),
                    # start_date =date(2020,10,1),
                    # end_date=date(2022, 5, 31)
                ),
                html.Div(
                    html.Div(
                        [
                            html.Div(dcc.Graph(id="label1"), className="column"),
                            html.Div(dcc.Graph(id="label2"), className="column"),
                        ],
                        className="two column row",
                    ),
                    className="ui grid",
                ),
                # spending types
                html.Br(),
                html.P(""),
                html.Br(),
                html.H4(
                    [html.I(className="file alternate icon"), " ES / NN"],
                    id="nnes",
                    className="ui horizontal divider",
                ),
                html.Div(
                    html.Div(
                        [
                            html.Div(dcc.Graph(id="rank"), className="column"),
                            html.Div(dcc.Graph(id="rank_s"), className="column"),
                        ],
                        className="two column row",
                    ),
                    className="ui grid",
                ),
                html.Div(
                    html.Div(
                        [
                            html.Div(dcc.Graph(id="st"), className="column"),
                            html.Div(dcc.Graph(id="nn"), className="column"),
                            html.Div(dcc.Graph(id="es"), className="column"),
                        ],
                        className="three column row",
                    ),
                    className="ui grid",
                ),
                # html.Div(id="l2_cat"),
                dcc.Dropdown(id="l2_cat", multi=True, style={"width": "50%"}),
                dcc.Graph(id="l2_ot"),
                # self service
                html.H4(
                    [html.I(className="filter icon"), " Self Service"],
                    className="ui horizontal divider",
                ),
                html.Div(
                    html.Div(
                        [
                            html.Div("left", className="blue column"),
                            html.Div("middle", className="column"),
                            html.Div("right", className="blue column"),
                        ],
                        className="three column row",
                    ),
                    className="ui centered grid",
                ),
                # about
                html.H4(
                    [html.I(className="id card icon"), " About"],
                    id="about",
                    className="ui horizontal divider",
                ),
                html.Div(
                    html.Div(
                        [
                            html.Div("left", className="blue column"),
                            html.Div("middle", className="column"),
                            html.Div("right", className="blue column"),
                        ],
                        className="three column row",
                    ),
                    className="ui centered grid",
                ),
            ],
            id="context",
            className="thirteen wide column",
        ),
        dcc.Store(id="ledger_data"),
        dcc.Store(id="history_data"),
        dcc.Store(id="dist_data"),
    ],
    style={
        "padding": "50px 50px 50px 100px",
        "backgroundColor": color_scheme["bg"],
        "color": color_scheme["font"],
    },
    className="ui grid",
)


@app.callback(
    Output("ledger_data", "data"),
    Output("history_data", "data"),
    Output("dist_data", "data"),
    Input("coalesce_input", "value"),
    Input("ovw_timerange", "start_date"),
    Input("ovw_timerange", "end_date"),
    Input("cat_timerange", "start_date"),
    Input("cat_timerange", "end_date"),
)
def data_pipeline(coalesce_input, ovw_start, ovw_end, cat_start, cat_end):

    # import data
    output_folder = pathlib.Path("/home/til/03_code/til-dkbl")
    # output_folder = pathlib.Path("/home/til/code/jonas/jonas-py/")
    ledger = _handle_import(output_folder, "ledger")
    history = _handle_import(output_folder, "history")
    # TODO this step is manual
    history["date"] = history["date_custom"]

    # parse datetime
    for df in [ledger, history]:
        for date_col in ["date", "date_custom"]:
            if set([date_col]).issubset(df.columns):
                df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d")

    # coalesce
    if coalesce_input is not None:
        for df in [ledger]:
            for col in coalesce_input:
                if set([col, f"{col}_custom"]).issubset(df.columns):
                    df[col] = np.where(
                        df[f"{col}_custom"].isnull(), df[col], df[f"{col}_custom"]
                    )

    # add timecols
    ledger = add_timecols(ledger)
    history = add_timecols(history)

    # create branch df: dist
    dist = _distribute_occurences(ledger)
    dist = add_timecols(dist)
    dist = dist[dist["type"] == "Expense"]
    dist["st"] = np.where(dist["occurence"] == 0, "Expendable", "Non-Negotiable")

    # filter time ranges
    if ovw_start is not None and ovw_end is not None:
        ledger = ledger[(ledger["month"] >= ovw_start) & (ledger["month"] <= ovw_end)]
        history = history[
            (history["month"] >= ovw_start) & (history["month"] <= ovw_end)
        ]
        dist = dist[(dist["month"] >= ovw_start) & (dist["month"] <= ovw_end)]

    return (
        ledger.to_json(date_format="iso", orient="split"),
        history.to_json(date_format="iso", orient="split"),
        dist.to_json(date_format="iso", orient="split"),
    )


@app.callback(
    Output("l2_cat", "options"),
    Output("l2_cat", "value"),
    Input("ledger_data", "data"),
)
def dyn_dropdown(ledger):
    ledger = pd.read_json(ledger, orient="split")

    label2_cats = ledger.drop_duplicates(subset="label2").fillna("nan")
    label2_cats = sorted(label2_cats["label2"])

    return label2_cats, label2_cats




@app.callback(
    Output("netio_fig", "figure"),
    Output("io_fig", "figure"),
    Output("history", "figure"),
    Output("label2", "figure"),
    Output("label1", "figure"),
    Output("rank", "figure"),
    Output("rank_s", "figure"),
    Output("nn", "figure"),
    Output("es", "figure"),
    Output("st", "figure"),
    Output("l2_ot", "figure"),
    Input("ledger_data", "data"),
    Input("history_data", "data"),
    Input("dist_data", "data"),
    Input("l2_cat", "value"),
)
def update_output(df, history, dist, l2_cat):
    df = pd.read_json(df, orient="split")
    history = pd.read_json(history, orient="split")
    dist = pd.read_json(dist, orient="split")

    ## overview
    # last 3 months
    netio = df.groupby(["month"], as_index=False).sum()
    netio["type"] = np.where(netio["amount"] >= 0, "Income", "Expense")
    netio_fig = px.bar(
        netio,
        x="month",
        y="amount",
        color="type",
        title="Net Income",
        color_discrete_map=ei_colors,
    )
    netio_fig = style_chart(netio_fig, "vbar")

    # io last 3 months
    io = df.groupby(["month", "type"], as_index=False)["amount"].apply(
        lambda c: c.abs().sum()
    )
    io_fig = px.bar(
        io,
        x="month",
        y="amount",
        barmode="group",
        color="type",
        title="Income / Spending",
        color_discrete_map=ei_colors,
    )
    io_fig = style_chart(io_fig, "vbar")

    # history

    datahis = history.groupby(["date"], as_index=False).mean()

    ymin = datahis["balance"].min() * 1.1 if datahis["balance"].min() < 0 else 0
    ymax = datahis["balance"].max() * 1.1 if datahis["balance"].max() > 0 else 0
    his_ylimits = [ymin, ymax]

    hisplot = px.area(
        datahis,
        x="date",
        y="balance",
        range_y=his_ylimits,
        title="Weekly Balance",
        color_discrete_sequence=["#148dea"],
    )
    hisplot = style_chart(hisplot, "line")

    ## cat view
    # label2
    dat_l2 = (
        df.groupby(["label2"], as_index=False)["amount"].sum().sort_values(by="amount")
    )
    dat_l2["type"] = np.where(dat_l2["amount"] >= 0, "Income", "Expense")
    p_l2 = px.bar(
        dat_l2,
        y="label2",
        x="amount",
        color="type",
        title="Spending per Label2",
        color_discrete_map=ei_colors,
    )
    p_l2 = style_chart(p_l2, "bar")

    # label1
    dat_l1 = (
        df.groupby(["label1"], as_index=False)["amount"].sum().sort_values(by="amount")
    )
    dat_l1["type"] = np.where(dat_l1["amount"] >= 0, "Income", "Expense")
    p_l1 = px.bar(
        dat_l1,
        y="label1",
        x="amount",
        color="type",
        title="Spending per Label1",
        color_discrete_map=ei_colors,
    )
    p_l1 = style_chart(p_l1, "bar")

    ## st
    # nn
    data_nn = dist[dist["occurence"] != 0]
    data_nn = data_nn.groupby("month", as_index=False).sum()
    data_nn["color"] = "#148dea"
    plot_nn = px.bar(
        data_nn,
        x="month",
        y="amount",
        title="Non Negotiable Spending",
        color_discrete_sequence=["#148dea"],
    )
    plot_nn = style_chart(plot_nn, "vbar")

    # expendable spending
    data_es = dist[dist["st"] == "Expendable"]
    data_es = data_es.groupby("month", as_index=False).sum()
    plot_es = px.bar(
        data_es,
        x="month",
        y="amount",
        title="Expendable Spending",
        color_discrete_sequence=["#148dea"],
    )
    plot_es = style_chart(plot_es, "vbar")

    # spending type
    data_st = dist.groupby(["month", "st"], as_index=False)["amount"].apply(
        lambda c: c.abs().sum()
    )
    plot_st = px.bar(
        data_st,
        x="month",
        y="amount",
        barmode="group",
        color="st",
        title="Spendings by ",
    )
    plot_st = style_chart(plot_st, "vbar")

    ## ranking
    # top spending
    data_rank = df[df["occurence"] == 0]
    data_rank = (
        data_rank[data_rank["type"] == "Expense"]
        .sort_values("amount")
        .head(10)
        .sort_values("amount", ascending=False)
    )
    plot_rank = px.bar(
        data_rank,
        x="amount",
        y="recipient_clean",
        title="Top 10 Expendable Expenses",
        color_discrete_sequence=["#148dea"],
    )
    plot_rank = style_chart(plot_rank, "bar")

    # top income
    data_rank_s = df[df["occurence"] == 0]
    data_rank_s = (
        data_rank_s[data_rank_s["type"] == "Income"].sort_values("amount").head(10)
    )
    plot_rank_s = px.bar(
        data_rank_s,
        x="amount",
        y="recipient_clean",
        title="Top 10 Income",
        color_discrete_sequence=["#148dea"],
    )
    plot_rank_s = style_chart(plot_rank_s, "bar")

    ## cats over time
    l2_ot_d = (
        df[df["label2"].isin(l2_cat)].groupby(["month", "label2"], as_index=False).sum()
    )

    ymin2 = l2_ot_d["amount"].min() * 1.1 if l2_ot_d["amount"].min() < 0 else 0
    ymax2 = l2_ot_d["amount"].max() * 1.1 if l2_ot_d["amount"].max() > 0 else 0
    l2_ylimits = [ymin2, ymax2]

    # TODO filter für label1-3, occurence, recipient_clean, timerange, amounts

    plot_l2ot = px.bar(
        l2_ot_d,
        x="month",
        y="amount",
        title="Expendable Spending",
        color="label2",
        range_y=l2_ylimits,
    )
    plot_l2ot = style_chart(plot_l2ot, "vbar")

    return (
        netio_fig,
        io_fig,
        hisplot,
        p_l2,
        p_l1,
        plot_rank,
        plot_rank_s,
        plot_nn,
        plot_es,
        plot_st,
        plot_l2ot,
    )


if __name__ == "__main__":
    app.run_server(debug=True)

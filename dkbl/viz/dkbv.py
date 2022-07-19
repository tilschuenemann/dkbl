import pandas as pd
import matplotlib.pyplot as plt
import datetime
from datetime import date
import numpy as np
import dkbl.dkbl as d


def prepare_data(
    output_folder: str,
    fname: str,
    start: str,
    end: str,
    custom_date: bool = False,
    custom_label1: bool = False,
    custom_label2: bool = False,
    custom_label3: bool = False,
    custom_amount: bool = False,
    custom_occurence: bool = False,
    custom_recipient_clean: bool = False,
) -> pd.DataFrame:
    df = d._handle_import(output_folder, fname)
    for date_col in ["date", "date_custom"]:
        try:
            df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d")
        except:
            None

    # filter df
    df = df[(df["date"] >= np.datetime64(start)) & (df["date"] <= np.datetime64(end))]

    # TODO coalesce according to custom flags

    # add ymd colums
    for col in ["week", "month", "quarter", "year"]:
        df[col] = pd.to_datetime(df.date).dt.to_period(col.upper()[0]).dt.to_timestamp()
    return df


def filter_data(df: pd.DataFrame, col, key):
    df = df[df["label2"] == "Groceries"]


def sum_time(df: pd.DataFrame, t_col: str):
    spendings = df.groupby([t_col], as_index=False).sum()
    return spendings.plot.bar(x=t_col, y="amount")


def cat_plot_sum(ledger: pd.DataFrame, cat: str):

    colors = {"spending": "#ff0000", "income": "#00ff00"}
    # TODO try catch error if label empty

    cat_plot = ledger.groupby([cat], as_index=False).sum()
    cat_plot = cat_plot.sort_values("amount", ascending=True)
    cat_plot["net"] = cat_plot["amount"].apply(
        lambda x: "income" if x >= 0 else "spending"
    )
    return cat_plot.plot.barh(x=cat, y="amount", color=cat_plot["net"].map(colors))


def cat_plot_count(ledger: pd.DataFrame, cat: str):
    cat_plot = ledger.groupby([cat], as_index=False).size()
    cat_plot = cat_plot.sort_values("size", ascending=True)
    return cat_plot.plot.barh(x=cat, y="size")


def hist_plot(df: pd.DataFrame, timekey: str):
    hist = df.groupby(timekey, as_index=False)["balance"].mean()
    p = hist.plot.line(x=timekey, y="balance", grid=True)
    p = p.set_ylim(bottom=0)
    return p

# # hist_plot(ledger, "date")
# ax = hist_plot(ledger, "week")
# # ax.xaxis.grid(True, which="major", linestyle="solid")
# # ax.yaxis.grid(True, which="major", linestyle="solid")
# ax.yaxis.set_major_formatter("{x:,.0f}€")
# ax.set_facecolor("#e3e3e3")
# ax.get_figure().savefig("hist_week.png")

import pandas as pd

import datetime
from datetime import datetime
import locale
import re


def import_dkb_header(path: str) -> dict:
    """Reads CSV from path and extracts header data: start and end date as well
    as the amount at the end of the report.
    """
    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

    df = pd.read_csv(path, encoding="iso-8859-1", nrows=4, sep=";", header=None)

    header = {
        "start": datetime.strptime(df.iloc[1, 1], "%d.%m.%Y"),
        "end": datetime.strptime(df.iloc[2, 1], "%d.%m.%Y"),
        "amount_end": locale.atof(df.iloc[3, 1].replace(" EUR", "")),
    }

    return header


def import_dkb_content(path: str) -> pd.DataFrame:
    """Reads the CSV from path, selects date, recipient and amount columns,
    formats them as date, float and string respectively.
    """

    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

    df = pd.read_csv(path, encoding="iso-8859-1", skiprows=5, sep=";")
    df = df[["Buchungstag", "Auftraggeber / Begünstigter", "Betrag (EUR)"]]
    df.columns = ["date", "recipient", "amount"]

    df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y")
    df["amount"] = df["amount"].apply(lambda a: locale.atof(a))
    df["recipient"] = df["recipient"].astype(str)

    return df


def add_initial_record(df: pd.DataFrame(), amount_end: float, date) -> pd.DataFrame:
    """Adds initial record with original amount for setting up the balance correctly.
    Returns dataframe sorted by asc. date.
    """

    amount = amount_end - df["amount"].sum(axis=0)

    ini_row = {"amount": amount, "recipient": "~~INIT", "date": date}

    ini_df = pd.DataFrame([ini_row])
    df = pd.concat([df, ini_df], axis=0, ignore_index=True)

    df = df.sort_values(by="date")
    return df


def format_content(df: pd.DataFrame()) -> pd.DataFrame:
    """Takes basic dataframe and adds extra columns."""

    # TODO cast date_custom as date
    df["date_custom"] = None
    df["amount_custom"] = float()
    df["balance"] = float()
    df["type"] = df["amount"].apply(lambda a: "Income" if a > 0 else "Expense")
    df["occurence_custom"] = int()
    df["recipient_clean"] = str()
    df["recipient_clean_custom"] = str()
    df["label1_custom"] = str()
    df["label2_custom"] = str()
    df["label3_custom"] = str()
    df["label1"] = str()
    df["label2"] = str()
    df["label3"] = str()

    df = df[sorted(df.columns)]
    df = df.sort_values(by="date")
    return df


def create_ledger(fp_export):
    df = import_dkb_content(fp_export)
    header = import_dkb_header(fp_export)

    df = add_initial_record(df, header["amount_end"], header["start"])
    df = format_content(df)
    # TODO replace with update_balance(df)
    df["balance"] = df["amount"].cumsum()

    df.to_csv("files/ledger.csv", sep=";", index=False, encoding="UTF-8")
    print("printed to disk")

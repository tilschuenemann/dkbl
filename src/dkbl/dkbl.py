import pandas as pd

import datetime
from datetime import datetime
from datetime import timedelta
import locale
import os
import re


def _import_dkb_header(path: str) -> dict:
    """Reads CSV from path and extracts header data: start and end date as well
    as the amount at the end of the report.


    Parameters
    -----
    path: str
        path to CSV export file

    Returns
    -------
    dict
        dict containing report start, end date, end amount
    """

    if os.path.exists(path):
        df = pd.read_csv(path, encoding="iso-8859-1", nrows=4, sep=";", header=None)
    else:
        exit("file doesnt exist")

    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

    header = {
        "start": datetime.strptime(df.iloc[1, 1], "%d.%m.%Y"),
        "end": datetime.strptime(df.iloc[2, 1], "%d.%m.%Y"),
        "amount_end": locale.atof(df.iloc[3, 1].replace(" EUR", "")),
    }

    return header


def _import_dkb_content(path: str) -> pd.DataFrame:
    """Reads the CSV from path, selects date, recipient and amount columns,
    formats them as date, float and string respectively.

    Parameters
    ------
    path: str
        path to export

    Returns
    -------
    pd.DataFrame
        df containing date, recipient and amount columns
    """

    if os.path.exists(path):
        df = pd.read_csv(path, encoding="iso-8859-1", skiprows=5, sep=";")
    else:
        exit("file doesnt exist")

    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

    df = df[["Buchungstag", "Auftraggeber / Begünstigter", "Betrag (EUR)"]]

    df.columns = ["date", "recipient", "amount"]
    df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y")
    df["amount"] = df["amount"].apply(lambda a: locale.atof(a))
    df["recipient"] = df["recipient"].astype(str)

    return df


def _format_content(df: pd.DataFrame) -> pd.DataFrame:
    """Takes basic dataframe and adds extra columns.

    Df needs to have columns "amount", "date", "recipient".

    Parameters
    -------
    df: pd.DataFrame
        input dataframe

    Returns
    -------
    pd.DataFrame
        formatted df

    """

    if set(["date", "recipient", "amount"]).issubset(df.columns) == False:
        exit("supplied malformed df - date, recipient or amount columns dont exist!")

    df["date_custom"] = str()
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

    df = df.astype(
        {
            "amount": float,
            "recipient": str,
            "date": str,
            "date_custom": str,
            "amount_custom": float,
            "balance": float,
            "type": str,
            "occurence_custom": int,
            "recipient_clean": str,
            "recipient_clean_custom": str,
            "label1_custom": str,
            "label2_custom": str,
            "label3_custom": str,
            "label1": str,
            "label2": str,
            "label3": str,
        }
    )

    df = df[sorted(df.columns)]
    df = df.sort_values(by="date")
    return df


def _write_ledger_to_disk(ledger: pd.DataFrame, output_folder: str):
    """Helper function for standardized writing to disk.

    Parameters
    -------
    ledger: pd.DataFrame
        ledger df
    output_folder: str
        path to output folder
    """
    ledger.to_csv(
        f"{output_folder}/ledger.csv",
        sep=";",
        index=False,
        encoding="UTF-8",
        date_format="%Y-%m-%d",
        float_format="%.2f",
        decimal=",",
    )


def _user_input(phrase: str) -> bool:
    """Helper function to get boolean user input.

    Parameter
    -------
    phrase: str
        question that asks for input
    Returns
    -------
    bool
        user choice
    """
    user_input = input(f"{phrase} [y/n] \n")
    if user_input == ("y"):
        return True
    elif user_input == ("n"):
        return False
    else:
        return _user_input("Please enter y or n " + phrase)


def create_ledger(export: str, output_folder: str) -> pd.DataFrame:
    """Reads the export and its header info, adds the initial record
    and formats the base ledger.

    Ledger is written to disk in the output_folder and returned.

    Parameters
    -------
    export: str
        path to export
    output_folder: str
        path to output folder

    Returns
    -------
    pd.DataFrame
        ledger dataframe

    """
    if os.path.exists(f"{output_folder}/ledger.csv"):
        if _user_input("Do you want to overwrite the existing ledger.csv?") == False:
            exit("not overwriting ledger. aborting.")

    df = _import_dkb_content(export)
    header = _import_dkb_header(export)

    df = _format_content(df)

    _write_ledger_to_disk(df, output_folder)

    update_maptab(output_folder)

    initial_balance = header["amount_end"] - df["amount"].sum(axis=0)
    update_history(output_folder, initial_balance, False, False)

    return df


def append_ledger(export: str, output_folder: str):
    """

    Parameters
    -------
    export: str

    output_folder: str
        where should result be stored?
    """

    ledger = pd.read_csv(
        f"{output_folder}/ledger.csv", sep=";", encoding="UTF-8", decimal=","
    )

    cutoff_date = ledger["date"].max()
    ledger = ledger.loc[ledger["date"] < cutoff_date]

    df = _import_dkb_content(export)

    df = _format_content(df)
    df = df.loc[df["date"] >= cutoff_date]

    appended_ledger = pd.concat([ledger, df], axis=0, ignore_index=True)

    _write_ledger_to_disk(appended_ledger, output_folder)

    return appended_ledger


def update_maptab(output_folder: str) -> pd.DataFrame:
    """Gets fresh list of ledger recipients, adds delta to current maptab
    if it exists

    Parameters
    -------
    output_folder: str

    Returns
    -------
    pd.DataFrame
        updated mapping table


    """

    maptab_path = f"{output_folder}/maptab.csv"
    ledger = pd.read_csv(f"{output_folder}/ledger.csv", sep=";")

    fresh_recipients = pd.DataFrame(ledger.recipient.unique(), columns=["recipient"])

    fresh_recipients["recipient_clean"] = str()
    fresh_recipients["label1"] = str()
    fresh_recipients["label2"] = str()
    fresh_recipients["label3"] = str()
    fresh_recipients["occurence"] = int()

    if os.path.exists(maptab_path):
        stale_recipients = pd.read_csv(maptab_path, sep=";")

        updated_maptab = fresh_recipients.merge(
            stale_recipients, on="recipient", how="left", suffixes=["_new", None]
        )
        updated_maptab.drop(
            [
                "label1_new",
                "label2_new",
                "label3_new",
                "recipient_clean_new",
                "occurence_new",
            ],
            axis=1,
            inplace=True,
        )
    else:
        updated_maptab = fresh_recipients

    updated_maptab = updated_maptab.sort_values(by="recipient")

    updated_maptab = updated_maptab.astype(
        {
            "recipient": str,
            "recipient_clean": str,
            "label1": str,
            "label2": str,
            "label3": str,
            "occurence": str,
        }
    )
    updated_maptab = updated_maptab.replace("nan", "")
    updated_maptab.to_csv(maptab_path, sep=";", encoding="UTF-8", index=False)
    return updated_maptab


def update_history(
    output_folder: str,
    initial_balance: float,
    use_custom_date: bool,
    use_custom_amount: bool,
) -> pd.DataFrame:
    """Creates a simple history dataframe from implicit ledger in output folder.

    Parameters
    -------
    output_folder : str
        folder where ledger.csv resides in
    initial_balance : float
        initial account balance
    use_custom_date: bool
        should date_custom be considered?
    use_custom_amount: bool
        should amount_custom be considered?

    Returns
    -------
    pd.DataFrame
        history df with columns date, balance
    """
    ledger_path = f"{output_folder}/ledger.csv"

    df = pd.read_csv(ledger_path, sep=";", encoding="UTF-8", decimal=",")

    date_col = "date_custom" if use_custom_date else "date"
    amount_col = "amount" if use_custom_amount else "amount"

    if use_custom_amount or use_custom_date:
        # TODO coalesce values
        None

    history = df[[date_col, amount_col]].copy()

    history = history.sort_values(by=date_col)

    # check this first
    history[amount_col].iloc[0] = history[amount_col].iloc[0] + initial_balance

    history["balance"] = history[amount_col].cumsum()

    history.to_csv(
        f"{output_folder}/history.csv",
        sep=";",
        index=False,
        encoding="UTF-8",
        date_format="%Y-%m-%d",
        float_format="%.2f",
        decimal=",",
    )

    return history


def update_ledger_mappings(output_folder: str):

    ledger_path = f"{output_folder}/ledger.csv"
    mp_path = f"{output_folder}/maptab.csv"

    ledger = pd.read_csv(ledger_path, sep=";", encoding="UTF-8", decimal=",")
    mp = pd.read_csv(mp_path, sep=";", encoding="UTF-8")

    ledger.drop(
        ["label1", "label2", "label3", "recipient_clean", "occurence"],
        axis=1,
        inplace=True,
        errors="ignore",
    )
    ledger = ledger.merge(mp, how="left", on="recipient")

    _write_ledger_to_disk(ledger, output_folder)

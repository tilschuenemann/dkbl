import pandas as pd  # ignore
import numpy as np

from datetime import datetime
import locale
import math
import os


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

    df["date_custom"] = str()
    df["amount_custom"] = float()
    df["balance"] = float()
    df["type"] = (
        df["amount"].apply(lambda a: "Income" if a > 0 else "Expense").astype(str)
    )
    df["occurence_custom"] = int(1)
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
        if _user_input("Do you want to overwrite the existing ledger.csv?") is False:
            exit("not overwriting ledger. aborting.")

    if os.path.exists(export) is False:
        exit("supplied export doesn't exist. aborting.")

    if os.path.exists(output_folder) is False:
        output_folder = os.getcwd()
        print(
            "output_folder doesnt exist. writing to working directory: "
            + f"{output_folder}"
        )

    df = _import_dkb_content(export)
    header = _import_dkb_header(export)
    _write_ledger_to_disk(df, output_folder)

    update_maptab(output_folder)

    initial_balance = header["amount_end"] - df["amount"].sum(axis=0)
    update_history(output_folder, initial_balance, False, False)

    return df


def append_ledger(export: str, output_folder: str) -> pd.DataFrame:
    """

    Parameters
    -------
    export: str

    output_folder: str
        path to output folder

    Returns
    -------
    pd.DataFrame
        new ledger with appendage
    """

    ledger = pd.read_csv(
        f"{output_folder}/ledger.csv", sep=";", encoding="UTF-8", decimal=","
    )

    cutoff_date = ledger["date"].max()
    ledger = ledger.loc[ledger["date"] < cutoff_date]

    df = _import_dkb_content(export)
    df = df.loc[df["date"] >= cutoff_date]

    appended_ledger = pd.concat([ledger, df], axis=0, ignore_index=True)

    appended_ledger["date"] = pd.to_datetime(appended_ledger["date"], format="%Y-%m-%d")
    _write_ledger_to_disk(appended_ledger, output_folder)

    return appended_ledger


def update_maptab(output_folder: str) -> pd.DataFrame:
    """Reads all unique recipients from ledger and adds new ones to the mapping
    table.

    Parameters
    -------
    output_folder: str
        path to output folder

    Returns
    -------
    pd.DataFrame
        updated mapping table
    """

    maptab_path = f"{output_folder}/maptab.csv"
    ledger = pd.read_csv(f"{output_folder}/ledger.csv", sep=";")

    fresh_recipients = pd.DataFrame(ledger.recipient.unique(), columns=["recipient"])

    if os.path.exists(maptab_path):
        stale_maptab = pd.read_csv(maptab_path, sep=";")

        updated_maptab = fresh_recipients.merge(
            stale_maptab, on="recipient", how="left", suffixes=["_new", None]
        )

    else:
        fresh_recipients["recipient_clean"] = str()
        fresh_recipients["label1"] = str()
        fresh_recipients["label2"] = str()
        fresh_recipients["label3"] = str()
        fresh_recipients["occurence"] = int()
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

    If supplied initial_balance is nan, it's attempted to read the existing
    history and grab the initial balance from there.

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
        history df with columns date, amount, balance, initial_balance
    """
    if initial_balance == float() and os.path.exists(f"{output_folder}/history.csv"):
        old_history = pd.read_csv(
            f"{output_folder}/history.csv", sep=";", encoding="UTF-8"
        )
        initial_balance = old_history["initial_balance"][0]
    elif math.isnan(initial_balance):
        exit("supplied initial balance is nan.")

    ledger_path = f"{output_folder}/ledger.csv"

    df = pd.read_csv(ledger_path, sep=";", encoding="UTF-8", decimal=",")

    date_col = "date_custom" if use_custom_date else "date"
    amount_col = "amount_custom" if use_custom_amount else "amount"

    history = df[["date", "amount"]].copy()
    if use_custom_amount and use_custom_date:
        history["amount_custom"] = np.where(
            df["amount_custom"].isnull(), df["amount"], df["amount_custom"]
        )
        history["date_custom"] = np.where(
            df["date_custom"].isnull(), df["date"], df["date_custom"]
        )
        history.drop(["amount", "date"], axis=1, inplace=True)
    elif use_custom_amount:
        history["amount_custom"] = np.where(
            df["amount_custom"].isnull(), df["amount"], df["amount_custom"]
        )
        history.drop("amount", axis=1, inplace=True)
    elif use_custom_date:
        history["date_custom"] = np.where(
            df["date_custom"].isnull(), df["date"], df["date_custom"]
        )
        history.drop("date", axis=1, inplace=True)

    history = history.sort_values(by=date_col)
    history = history.reset_index(drop=True)
    history["initial_balance"] = 0
    history.at[0, "initial_balance"] = initial_balance
    history["balance"] = history[amount_col] + history["initial_balance"]
    history["balance"] = history["balance"].cumsum()

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


def update_ledger_mappings(output_folder: str) -> pd.DataFrame:
    """

    Parameters
    -------
    output_folder: str
        path to output folder

    Returns
    -------
    pd.DataFrame
        ledger with updated mappings
    """

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

    return ledger

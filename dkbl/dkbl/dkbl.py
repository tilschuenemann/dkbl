import pandas as pd  # ignore
import numpy as np

from datetime import datetime
import locale
import math
import os
import pathlib


def _handle_import(path: pathlib.Path, filetype: str) -> pd.DataFrame:
    try:
        if filetype == "header":
            df = pd.read_csv(path, encoding="iso-8859-1", nrows=4, sep=";", header=None)
        elif filetype == "content":
            df = pd.read_csv(path, encoding="iso-8859-1", skiprows=5, sep=";")
        elif filetype == "maptab":
            df = pd.read_csv(path / "maptab.csv", sep=";", encoding="UTF-8")
        elif filetype == "ledger" or filetype == "dist_ledger":
            df = pd.read_csv(
                path / f"{filetype}.csv", sep=";", encoding="UTF-8", decimal=","
            )
        elif filetype == "history":
            df = pd.read_csv(
                path / "history.csv", sep=";", encoding="UTF-8", decimal=","
            )

    except FileNotFoundError:
        exit("export file not found!")

    # TODO check for rows
    # TODO check for columns and their names

    return df


def _import_dkb_header(export_path: pathlib.Path) -> dict:
    """Reads CSV from path and extracts header data: start date, end date as well
    as the amount at the end of the report.

    Parameters
    -----
    export_path: pathlib.Path
        path to CSV export file

    Returns
    -------
    dict
        dict containing report start, end date, end amount
    """

    df = _handle_import(export_path, "header")

    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

    header = {
        "start": datetime.strptime(df.iloc[1, 1], "%d.%m.%Y"),
        "end": datetime.strptime(df.iloc[2, 1], "%d.%m.%Y"),
        "amount_end": locale.atof(df.iloc[3, 1].replace(" EUR", "")),
    }

    return header


def _import_dkb_content(export_path: pathlib.Path) -> pd.DataFrame:
    """Reads the CSV from path, selects date, recipient and amount columns,
    formats them as date, float and string respectively.

    Parameters
    ------
    export_path: pathlib.Path
        path to export

    Returns
    -------
    pd.DataFrame
        df containing date, recipient and amount columns
    """
    df = _handle_import(export_path, "content")

    locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

    df = df[["Buchungstag", "Auftraggeber / Begünstigter", "Betrag (EUR)"]]

    df.columns = ["date", "recipient", "amount"]
    df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y")
    df["amount"] = df["amount"].apply(lambda a: locale.atof(a))
    df["recipient"] = df["recipient"].astype(str)

    df["date_custom"] = str()
    df["amount_custom"] = str()
    df["type"] = (
        df["amount"].apply(lambda a: "Income" if a > 0 else "Expense").astype(str)
    )
    df["occurence_custom"] = str()
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


def _write_ledger_to_disk(
    ledger: pd.DataFrame, output_folder: pathlib.Path, fname: str
):
    """Helper function for standardized writing to disk.

    Parameters
    -------
    ledger: pd.DataFrame
        ledger df
    output_folder: pathlib.Path
        path to output folder
    fname: str
        name of file to write (.csv will get appended)
    """

    if pathlib.Path(output_folder).exists() is False:
        output_folder = os.getcwd()
        print(
            "output_folder doesnt exist. writing to working directory: "
            + f"{output_folder}"
        )

    name = output_folder / f"{fname}.csv"

    if name.exists():
        if _user_input(f"Do you want to overwrite the existing {fname}.csv?") is False:
            exit(f"not overwriting {fname}. aborting.")

    ledger.to_csv(
        name,
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


def create_ledger(export: pathlib.Path, output_folder: pathlib.Path) -> pd.DataFrame:
    """Reads the export and its header info, adds the initial record
    and formats the base ledger.

    Ledger is written to disk in the output_folder and returned.

    Parameters
    -------
    export: pathlib.Path
        path to export
    output_folder: pathlib.Path
        path to output folder

    Returns
    -------
    pd.DataFrame
        ledger dataframe

    """
    df = _import_dkb_content(export)
    header = _import_dkb_header(export)

    _write_ledger_to_disk(df, output_folder, "ledger")

    update_maptab(output_folder)

    initial_balance = header["amount_end"] - df["amount"].sum(axis=0)
    update_history(output_folder, initial_balance, False, False)

    return df


def append_ledger(export: pathlib.Path, output_folder: pathlib.Path) -> pd.DataFrame:
    """

    Parameters
    -------
    export: pathlib.Path
        path to export
    output_folder: pathlib.Path
        path to output folder

    Returns
    -------
    pd.DataFrame
        new ledger with appendage
    """
    ledger = _handle_import(output, "ledger")
    cutoff_date = ledger["date"].max()
    ledger = ledger.loc[ledger["date"] < cutoff_date]

    df = _import_dkb_content(export)
    df = df.loc[df["date"] >= cutoff_date]

    appended_ledger = pd.concat([ledger, df], axis=0, ignore_index=True)

    appended_ledger["date"] = pd.to_datetime(appended_ledger["date"], format="%Y-%m-%d")
    _write_ledger_to_disk(appended_ledger, output_folder, "ledger")

    return appended_ledger


def update_maptab(output_folder: pathlib.Path) -> pd.DataFrame:
    """Reads all unique recipients from ledger and adds new ones to the mapping
    table.

    Parameters
    -------
    output_folder: pathlib.Path
        path to output folder

    Returns
    -------
    pd.DataFrame
        updated mapping table
    """

    maptab_path = output_folder / "maptab.csv"
    ledger = _handle_import(output_folder, "ledger")

    fresh_recipients = pd.DataFrame(ledger.recipient.unique(), columns=["recipient"])

    if os.path.exists(maptab_path):
        stale_maptab = _handle_import(output_folder, "maptab")

        # TODO this will lose old entries incase of new ledger and old maptab
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
    updated_maptab["recipient"] = updated_maptab["recipient"].replace("nan", "")
    updated_maptab.to_csv(maptab_path, sep=";", encoding="UTF-8", index=False)
    return updated_maptab


def update_history(
    output_folder: pathlib.Path,
    initial_balance: float,
    use_custom_date: bool,
    use_custom_amount: bool,
) -> pd.DataFrame:
    """Creates a simple history dataframe from implicit ledger in output folder.

    If supplied initial_balance is nan, it's attempted to read the existing
    history and grab the initial balance from there.

    Parameters
    -------
    output_folder : pathlib.Path
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

    if initial_balance == float():
        old_history = _handle_import(path, "history")
        initial_balance = old_history["initial_balance"][0]

    df = _handle_import(output_folder, "ledger")

    date_col = "date_custom" if use_custom_date else "date"
    amount_col = "amount_custom" if use_custom_amount else "amount"

    history = df[["date", "amount"]].copy()
    if use_custom_amount:
        # TODO float(0) will be coerced
        history["amount_custom"] = np.where(
            df["amount_custom"].isnull(),
            df["amount"],
            df["amount_custom"],
        )
        history.drop("amount", axis=1, inplace=True)
    if use_custom_date:
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

    _write_ledger_to_disk(history, output_folder, "history")

    return history


def update_ledger_mappings(output_folder: pathlib.Path) -> pd.DataFrame:
    """

    Parameters
    -------
    output_folder: pathlib.Path
        path to output folder

    Returns
    -------
    pd.DataFrame
        ledger with updated mappings
    """

    ledger = _handle_import(output_folder, "ledger")
    mp = _handle_import(output_folder, "maptab")

    ledger = ledger[
        ledger.columns.difference(
            ["label1", "label2", "label3", "recipient_clean", "occurence"]
        )
    ].merge(mp, how="left", on="recipient")

    _write_ledger_to_disk(ledger, output_folder, "ledger")

    return ledger


def distribute_occurences(output_folder: pathlib.Path) -> pd.DataFrame:
    """Reads the ledger from the output_folder and creates timeseries
    for all line items that have an occurence that is not 1, 0 or -1.
    All their amounts get divided by the occurence and the dates get set to the
    start of that month.

    Parameters
    -------

    Returns
    -------

    """

    df = _handle_import(output_folder, "ledger")

    if not (set(df).issuperset(["date", "amount", "occurence"])) or df.shape[0] == 0:
        exit("malformed input df")

    # TODO coalesce occurence_custom

    mask = df["occurence"].between(-1, 1, inclusive="both")
    no_rep = df[mask]
    rep = df[~mask]

    # create new dates, which will get appended later
    new_dates = pd.DataFrame()

    for row in rep.itertuples():
        date = row.date
        n = row.occurence

        if n > 0:
            tmp = pd.DataFrame(
                pd.date_range(start=date, periods=n, freq="MS").tolist(),
                columns=["date"],
            )
        else:
            tmp = pd.DataFrame(
                pd.date_range(end=date, periods=abs(n), freq="MS").tolist(),
                columns=["date"],
            )
        new_dates = pd.concat([new_dates, tmp], axis=0, ignore_index=True)

    # repeat rows by occurence value and add new dates
    rep = rep.reset_index(drop=True)
    rep = rep.reindex(rep.index.repeat(abs(rep["occurence"])))
    rep = rep.reset_index(drop=True)
    rep["amount"] = rep["amount"] / abs(rep["occurence"])
    rep["date"] = new_dates["date"]

    dis = pd.concat([no_rep, rep], axis=0)
    dis["date"] = pd.to_datetime(dis["date"], format="%Y-%m-%d")

    _write_ledger_to_disk(dis, output_folder, "dist_leder")

    return dis

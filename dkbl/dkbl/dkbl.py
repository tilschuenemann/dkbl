import pandas as pd  # ignore
import numpy as np

import argparse
from datetime import datetime
import locale
import os
import pathlib


def _handle_import(path: pathlib.Path, filetype: str, bank = None) -> pd.DataFrame:
    """ 

    :param path:
    :param filetype:
    :param bank:
    :returns: 
    """
    try:
        if filetype == "header":
            if bank == "dkb":
                df = pd.read_csv(
                    path, encoding="iso-8859-1", nrows=4, sep=";", header=None
                )

                locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

                df = pd.DataFrame.from_dict(
                    {
                        "start": [datetime.strptime(df.iloc[1, 1], "%d.%m.%Y")],
                        "end": [datetime.strptime(df.iloc[2, 1], "%d.%m.%Y")],
                        "amount_end": [locale.atof(df.iloc[3, 1].replace(" EUR", ""))],
                    }
                )
            elif bank == "bbb":
                df = pd.read_csv(path, encoding="iso-8859-1", sep=";").tail(2)
                locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

                df = pd.DataFrame.from_dict(
                    {
                        "start": datetime.strptime(df.iloc[1, 0], "%d.%m.%Y"),
                        "end": datetime.strptime(df.iloc[0, 0], "%d.%m.%Y"),
                        "amount_end": locale.atof(df.iloc[1, 12]),
                    }
                )
        elif filetype == "content":
            if bank == "dkb":
                df = pd.read_csv(path, encoding="iso-8859-1", skiprows=5, sep=";")
                locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

                df = df[["Buchungstag", "Auftraggeber / Begünstigter", "Betrag (EUR)"]]
                df.columns = ["date", "recipient", "amount"]
                df["amount"] = df["amount"].apply(lambda a: locale.atof(a))

            elif bank == "bbb":
                df = pd.read_csv(
                    path,
                    encoding="iso-8859-1",
                    skiprows=13,
                    sep=";",
                    skipfooter=3,
                    engine="python",
                )

                locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

                df["Soll/Haben"].replace({"S": -1, "H": 1}, inplace=True)
                df["Umsatz"] = (
                    df["Umsatz"].apply(lambda x: locale.atof(x)) * df["Soll/Haben"]
                )

                df = df[["Buchungstag", "Zahlungsempfänger", "Umsatz"]]
                df.columns = ["date", "recipient", "amount"]

        if filetype == "maptab":
            df = pd.read_csv(path / "maptab.csv", sep=";", encoding="UTF-8")
        elif filetype == "ledger" or filetype == "dist_ledger":
            fn = f"{filetype}.csv"

            df = pd.read_csv(path / fn, sep=";", encoding="UTF-8", decimal=",")
        elif filetype == "history":
            df = pd.read_csv(
                path / "history.csv", sep=";", encoding="UTF-8", decimal=","
            )

    except FileNotFoundError:
        exit("export file not found!")

    if df.empty:
        exit("import is empty")
    elif df.shape[0] == 0:
        exit("import has no rows")
    elif df.shape[1] == 0:
        exit("import has no columns")

    return df


def _format_base(export_path: pathlib.Path, bank: str) -> pd.DataFrame:
    """Imports CSV from path and adds ledger columns.

    :param export_path: path to export
    :param bank:
    :returns: df with ledger columns
    """
    df = _handle_import(export_path, "content", bank)

    df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y")
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


def _write_ledger_to_disk(df: pd.DataFrame, output_folder: pathlib.Path, fname: str):
    """Helper function for standardized writing to disk.

    If output_folder doesn't exit it falls back to the current working directory.
    Incase the file to be written already exists, the user is asked for permission.

    :param df: df to write
    :param output_folder: path to output folder
    :param fname: name of file to write (.csv will get appended)
    """

    if pathlib.Path(output_folder).exists() is False:
        output_folder = pathlib.Path(os.getcwd())
        print(
            "output_folder doesnt exist. writing to working directory: "
            + f"{output_folder}"
        )

    name = output_folder / fname

    if name.exists():
        if _user_input(f"Do you want to overwrite the existing {fname}?") is False:
            exit(f"not overwriting {fname}. aborting.")

    df.to_csv(
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

    :param phrase: question that asks for input
    :returns bool: user choice        
    """
    user_input = input(f"{phrase} [y/n] \n")
    if user_input == ("y"):
        return True
    elif user_input == ("n"):
        return False
    else:
        return _user_input("Please enter y or n " + phrase)


def create_ledger(
    export: pathlib.Path, output_folder: pathlib.Path, bank: str
) -> pd.DataFrame:
    """Reads the export and its header info, adds the initial record
    and formats the base ledger.

    Ledger is written to disk in the output_folder and returned.

    :param export: path to export
    :param output_folder: path to output folder
    :returns: ledger dataframe
    """
    df = _format_base(export, bank)
    header = _handle_import(export, "header", bank)

    _write_ledger_to_disk(df, output_folder, "ledger.csv")

    update_maptab(output_folder)

    initial_balance = header["amount_end"].iloc[0] - df["amount"].sum(axis=0)
    update_history(output_folder, initial_balance, False, False)

    return df


def append_ledger(
    export: pathlib.Path, output_folder: pathlib.Path, bank: str
) -> pd.DataFrame:
    """

    :param export: path to export
    :param output_folder: path to output folder
    :param returns: new ledger with appendage
    """
    ledger = _handle_import(output_folder, "ledger", bank)
    cutoff_date = ledger["date"].max()
    ledger = ledger.loc[ledger["date"] < cutoff_date]

    df = _format_base(export, bank)
    df = df.loc[df["date"] >= cutoff_date]

    appended_ledger = pd.concat([ledger, df], axis=0, ignore_index=True)

    appended_ledger["date"] = pd.to_datetime(appended_ledger["date"], format="%Y-%m-%d")
    _write_ledger_to_disk(appended_ledger, output_folder, "ledger.csv")

    return appended_ledger


def update_maptab(output_folder: pathlib.Path) -> pd.DataFrame:
    """Reads all unique recipients from ledger and adds new ones to the mapping
    table.

    :param output_folder: path to output folder
    :returns: updated mapping table
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

    :param output_folder: folder where ledger.csv resides in
    :param initial_balance: initial account balance
    :param use_custom_date: should date_custom be considered?
    :param use_custom_amount: should amount_custom be considered?
    :returns: history df with columns date, amount, balance, initial_balance
    """

    if initial_balance == float():
        old_history = _handle_import(output_folder, "history")
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

    _write_ledger_to_disk(history, output_folder, "history.csv")

    return history


def update_ledger_mappings(output_folder: pathlib.Path) -> pd.DataFrame:
    """Joins maptab onto ledger and writes to disk.

    :param output_folder: path to output folder
    :returns: ledger with updated mappings
    """

    ledger = _handle_import(output_folder, "ledger")
    mp = _handle_import(output_folder, "maptab")

    ledger = ledger[
        ledger.columns.difference(
            ["label1", "label2", "label3", "recipient_clean", "occurence"]
        )
    ].merge(mp, how="left", on="recipient")

    _write_ledger_to_disk(ledger, output_folder, "ledger.csv")

    return ledger


def _distribute_occurences(df: pd.DataFrame) -> pd.DataFrame:
    """Reads the ledger from the output_folder and creates timeseries
    for all line items that have an occurence that is not 1, 0 or -1.
    All their amounts get divided by the occurence and the dates get set to the
    start of that month.

    :param df:
    :returns: 

    """

    if not (set(df).issuperset(["date", "amount", "occurence"])) or df.shape[0] == 0:
        exit("malformed input df")

    # TODO coalesce occurence_custom

    mask = df["occurence"].between(-1, 1, inclusive="both")
    no_rep = df[mask]
    rep = df[~mask].reset_index(drop=True)

    if len(rep.index) > 0:
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
    else:
        return no_rep

    return dis


def main():
    parser = argparse.ArgumentParser(prog="dkbl")
    subparsers = parser.add_subparsers(dest="action")

    output_folder = argparse.ArgumentParser(add_help=False)
    output_folder.add_argument(
        "--output_folder", nargs=1, dest="output_folder", type=pathlib.Path
    )

    export = argparse.ArgumentParser(add_help=False)
    export.add_argument("export", nargs=1, type=pathlib.Path)

    bank = argparse.ArgumentParser(add_help=False)
    bank.add_argument("bank", nargs=1, choices=["dkb", "bbb"])

    # create subparsers
    ulm = subparsers.add_parser(
        "update-ledger-mappings",
        help="update ledger mappings with fresh mapping table",
        parents=[output_folder],
    )

    um = subparsers.add_parser(
        "update-maptab",
        help="update mapping table with fresh recipients",
        parents=[output_folder],
    )

    al = subparsers.add_parser(
        "append-ledger",
        help="add new export to existing ledger",
        parents=[export, bank, output_folder],
    )

    cl = subparsers.add_parser(
        "create-ledger",
        help="create ledger from export",
        parents=[export, bank, output_folder],
    )

    uh = subparsers.add_parser(
        "update-history",
        help="update history from ledger",
        parents=[output_folder],
    )
    uh.add_argument("--initial_balance", type=float, default=float())
    uh.add_argument("--use_custom_date", action="store_true")
    uh.add_argument("--use_custom_amount", action="store_true")

    dl = subparsers.add_parser(
        "distribute-ledger",
        help="distribute occurences and copy ledger",
        parents=[output_folder],
    )

    args = parser.parse_args()

    if args.action in ["create-ledger", "append-ledger"]:
        export = args.export[0]
        bank = args.bank[0]

    if args.output_folder is None:
        output_folder = pathlib.Path(os.getcwd())
    else:
        output_folder = args.output_folder[0]

    if args.action == "create-ledger":
        create_ledger(export, output_folder, bank)
    elif args.action == "append-ledger":
        append_ledger(export, output_folder, bank)
    elif args.action == "update-history":
        update_history(
            output_folder,
            args.initial_balance,
            args.use_custom_date,
            args.use_custom_amount,
        )
    elif args.action == "update-ledger-mappings":
        update_ledger_mappings(output_folder)
    elif args.action == "update-maptab":
        update_maptab(output_folder)
    elif args.action == "distribute-ledger":
        _distribute_occurences(output_folder)

if __name__ == "__main__":
    main()
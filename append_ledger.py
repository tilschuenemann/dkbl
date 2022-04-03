import pandas as pd

from dev_import import *


def main():
    ledger_path = "files/simpleledger.csv"
    ledger = pd.read_csv(ledger_path, sep=";", encoding="UTF-8")

    cutoff_date = ledger["date"].max()
    ledger = ledger.loc[ledger["date"] < cutoff_date]

    new_file = "files/export_2019_2022_2.csv"
    nu_df = import_dkb_content(new_file)
    nu_header = import_dkb_header(new_file)

    df = add_initial_record(nu_df, nu_header["amount_end"], nu_header["start"])
    df = format_content(df)
    df = df.loc[df["date"] >= cutoff_date]

    appended_ledger = pd.concat([ledger, df], axis=0, ignore_index=True)

    appended_ledger.to_csv(
        "files/app_ledger.csv", sep=";", encoding="UTF-8", index=False
    )

    return appended_ledger


if __name__ == "__main__":
    main()

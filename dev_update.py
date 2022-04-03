import pandas as pd


def update_balance(ledger_path):
    df = pd.read_csv(ledger_path, sep=";")

    try:
        init_amount = df["recipient"].value_counts()["~~INIT"]
    except KeyError:
        print("no init entry found")
        exit()

    if init_amount != 1:
        print("more than one init entry found")
        exit()

    # TODO check if init is first entry
    df = df.sort_values(by="date")
    df["balance"] = df["amount"].cumsum()

    df.to_csv("files/simpleledger.csv", sep=";", index=False, encoding="UTF-8")


wd = "/home/til/code2/2022-04-03-simpleledger/files/"
ledger = wd + "simpleledger.csv"

update_balance(ledger)


def update_ledger_mappings(fp_ledger, fp_mp):
    ledger = pd.read_csv(fp_ledger, sep=";", encoding="UTF-8")
    mp = pd.read_csv(fp_mp, sep=";", encoding="UTF-8")

    ledger.drop(
        ["label1", "label2", "label3", "recipient_clean", "occurence"],
        axis=1,
        inplace=True,
    )
    ledger = ledger.merge(mp, how="left", on="recipient")

    ledger.to_csv("files/simpleledger.csv", sep=";", index=False, encoding="UTF-8")

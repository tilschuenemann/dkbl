import pandas as pd


def update_maptab(fp_ledger, fp_mp):
    ledger = pd.read_csv(fp_ledger, sep=";")

    fresh_recipients = pd.DataFrame(ledger.recipient.unique(), columns=["recipient"])

    fresh_recipients["recipient_clean"] = str()
    fresh_recipients["label1"] = str()
    fresh_recipients["label2"] = str()
    fresh_recipients["label3"] = str()
    fresh_recipients["occurence"] = int()

    fresh_recipients = fresh_recipients.sort_values(by="recipient")

    if os.path.exists(fp_mp):
        stale_recipients = pd.read_csv(fp_mp, sep=";")

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

    updated_maptab.to_csv("files/maptab.csv", sep=";", encoding="UTF-8", index=False)


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

import pandas as pd

import os


def main():
    wd = "files/"
    fp_mp = wd + "maptab.csv"
    fp_ledger = wd + "simpleledger.csv"
    ##

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


if __name__ == "__main__":
    main()

import pandas as pd
import datetime as dt


def distribute_occurences(output_folder: str) -> pd.DataFrame:
    """Reads the ledger from the output_folder and creates timeseries
    for all line items that have an occurence that is not 1.

    All their amounts get divided by the occurence and the dates get set to the
    start of that month.

    #TODO coalesce occurence_custom
    """

    df = pd.read_csv(
        f"{output_folder}/ledger.csv", sep=";", encoding="UTF-8", decimal=","
    )

    if not (set(df).issuperset(["date", "amount", "occurence"])) or df.shape[0] == 0:
        exit("malformed input df")

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

    dis.to_csv(
        f"{output_folder}/dist_ledger.csv",
        sep=";",
        index=False,
        encoding="UTF-8",
        date_format="%Y-%m-%d",
        float_format="%.2f",
        decimal=",",
    )
    return dis

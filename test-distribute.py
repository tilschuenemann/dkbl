import pandas as pd

tr = {"date": ["2022-05-01"],"recipient": ["abo"],"amount":[100],"occurence": [0]}
tr1 = {"date": ["2022-05-01"],"recipient": ["abo"],"amount":[100],"occurence": [5]}
tr2 = {"date": ["2022-05-01"],"recipient": ["abo"],"amount":[100],"occurence": [-5]}
tr3 = {"date": ["2022-05-01"],"recipient": ["abo"],"amount":[100],"occurence": [1]}
tr4 = {"date": ["2022-05-01"],"recipient": ["abo"],"amount":[100],"occurence": [-1]}


df0 = pd.DataFrame(tr)
df1 = pd.DataFrame(tr1)
df2 = pd.DataFrame(tr2)
df3 = pd.DataFrame(tr3)
df4 = pd.DataFrame(tr4)

df = pd.concat([df0,df1,df2,df3,df4],axis=0)
print(df)

# ----


def distribute(df: pd.DataFrame) -> pd.DataFrame:
    """For each transaction in df, the rows get repeated by the absolute
    occurence value and their amount gets divided by occurence.

    Parameters
    -------
    df: pd.DataFrame
        ledger df

    Returns
    -------
    df: pd.DataFrame
        ledger df 

    TODO :
    * start of month frequency is hardcoded

    """

    if not(set(df).issuperset(['date', "amount","occurence"])) or df.shape[0]==0:
        exit("malformed input df")

    mask = df["occurence"].between(-1,1,inclusive="both")
    no_rep = df[mask]
    rep = df[~mask]

    # create new dates, which will get appended later
    new_dates = pd.DataFrame()

    for row in rep.itertuples():
        date = row.date
        n = row.occurence

        if n > 0:
            tmp = pd.DataFrame(pd.date_range(start=date, periods=n,freq="MS").tolist(),columns=["date"])
        else:
            tmp = pd.DataFrame(pd.date_range(end=date, periods=abs(n),freq="MS").tolist(),columns=["date"])
        new_dates = pd.concat([new_dates,tmp],axis=0,ignore_index=True)

    #  repeat rows by occurence value and add new dates
    rep = rep.reset_index(drop=True)
    rep = rep.reindex(rep.index.repeat(abs(rep["occurence"])))
    rep = rep.reset_index(drop=True)
    rep["amount"] = rep["amount"] /  abs(rep["occurence"])
    rep["date"] = new_dates["date"]

    dis = pd.concat([no_rep,rep],axis = 0)
    dis["date"] = pd.to_datetime(dis["date"],format="%Y-%m-%d")
    return dis

#print(distribute(pd.DataFrame(columns=["date","recipient","amount","occurence"])))

print(distribute(df))
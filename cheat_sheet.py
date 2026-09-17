import pandas as pd

df = pd.read_csv("data/raw/Sample - Superstore.csv", encoding="cp1252", dtype={"Postal Code": "str"})

df["Sales"]                  # one column
df[["Sales", "Profit"]]      # multiple columns
df[condition]                # filtered rows
df.loc[rows, columns]        # filtered rows and columns

df.head()                    # run method
df.head(10)                  # run method with input
df.sort_values("Sales")      # run method with input
df.isna().sum()              # run two methods

df.shape                     # attribute
df.columns                   # attribute
df.dtypes                    # attribute

len(df)                      # function call
pd.to_datetime(...)          # function call

df.loc[
    df["Ship Mode"] == "Same Day",
    ["Order ID", "Sales"]
]                            # From df, locate rows where ship mode is Same Day, and return this list of columns.

(
    df[df["Profit"] > 0]                                # WHERE
      .groupby("Ship Mode")                             # GROUP BY
      .agg(                                             # SELECT aggregates
          sales=("Sales", "sum"),
          orders=("Order ID", "nunique"),
      )
      .reset_index()
      .sort_values("sales", ascending=False)            # ORDER BY
)
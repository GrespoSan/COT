import pandas as pd
import requests


def load_cot_data(asset):

    url = (
        "https://www.cftc.gov/dea/"
        "newcot/Disaggregated_Futures.txt"
    )

    df = pd.read_csv(url)


    if asset=="GOLD":

        data=df[
            df["Market_and_Exchange_Names"]
            .str.contains("GOLD",case=False)
        ]


    row=data.iloc[-1]


    return {

        "open_interest":
            int(row["Open_Interest_All"]),

        "oi_change":
            int(row["Change_in_Open_Interest_All"]),

        "mm_long_change":
            int(row["M_Money_Positions_Long_All"]),

        "mm_short_change":
            int(row["M_Money_Positions_Short_All"]),

        "comm_long_change":
            int(row["Prod_Merc_Positions_Long_All"]),

        "comm_short_change":
            int(row["Prod_Merc_Positions_Short_All"])

    }

import pandas as pd
import streamlit as st


@st.cache_data(ttl=86400)
def load_cot_data(asset):

    url = "https://www.cftc.gov/dea/newcot/Disaggregated_Futures.txt"

    df = pd.read_csv(url)


    # controllo colonne
    st.write("Colonne COT disponibili:")
    st.write(df.columns)


    data = df[
        df["Market_and_Exchange_Names"]
        .str.contains(asset, case=False, na=False)
    ]


    if data.empty:
        raise Exception(
            f"Nessun dato COT trovato per {asset}"
        )


    row = data.iloc[-1]


    return {

        "open_interest":
            row["Open_Interest_All"],

        "oi_change":
            row["Change_in_Open_Interest_All"],

        "mm_long_change":
            row["M_Money_Positions_Long_All"],

        "mm_short_change":
            row["M_Money_Positions_Short_All"],

        "comm_long_change":
            row["Prod_Merc_Positions_Long_All"],

        "comm_short_change":
            row["Prod_Merc_Positions_Short_All"]

    }

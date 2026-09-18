import pandas as pd
import geopandas as gpd
import streamlit as st


@st.cache_data
def load_data():

    df1 = gpd.read_parquet("df_grid_1.parquet")
    df2 = gpd.read_parquet("df_grid_2.parquet")

    df_grid = pd.concat(
        [df1, df2],
        ignore_index=True
    )

    df_grid = gpd.GeoDataFrame(
        df_grid,
        geometry="geometry",
        crs=df1.crs
    )

    gdf_city = gpd.read_parquet(
        "gdf_city.parquet"
    )

    gdf_dong = gpd.read_parquet(
        "gdf_dong_clean.parquet"
    )

    return df_grid, gdf_city, gdf_dong
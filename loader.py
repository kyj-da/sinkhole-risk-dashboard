import pandas as pd
import geopandas as gpd
import streamlit as st


@st.cache_data
def load_data():

    # -----------------------------------------------------
    # 1. 경량화된 격자 데이터
    # -----------------------------------------------------

    df1 = pd.read_parquet(
        "df_grid_1.parquet"
    )

    df2 = pd.read_parquet(
        "df_grid_2.parquet"
    )

    df_grid = pd.concat(
        [df1, df2],
        ignore_index=True,
    )


    # -----------------------------------------------------
    # 2. 지도 경계 데이터
    # -----------------------------------------------------

    gdf_city = gpd.read_parquet(
        "gdf_city.parquet"
    )

    gdf_dong = gpd.read_parquet(
        "gdf_dong_clean.parquet"
    )


    # -----------------------------------------------------
    # 3. 반환
    # -----------------------------------------------------

    return (
        df_grid,
        gdf_city,
        gdf_dong,
    )
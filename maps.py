import pydeck as pdk
import pandas as pd
import numpy as np

def get_color_for_score(normalized_score, is_grid=False):
    """0~1로 변환된 점수를 색상 리스트로 반환"""
    if pd.isna(normalized_score): return [100, 100, 100, 50]
    alpha = 200 if is_grid else 150
    if normalized_score < 0.2: return [0, 255, 0, alpha]
    if normalized_score < 0.4: return [150, 255, 0, alpha]
    if normalized_score < 0.6: return [255, 255, 0, alpha]
    if normalized_score < 0.8: return [255, 128, 0, alpha]
    return [255, 0, 0, alpha]

def draw_choropleth_map(gdf, value_col="Avg_Risk", title_col="지역명", min_v=None, max_v=None, zoom=9):
    """시군구/읍면동 배경 지도"""
    gdf = gdf.copy()
    gdf['display_val'] = gdf[value_col].round(2)
    
    if min_v is None: min_v = gdf[value_col].min()
    if max_v is None: max_v = gdf[value_col].max()
    
    gdf['norm_score'] = (gdf[value_col] - min_v) / (max_v - min_v) if max_v > min_v else 0
    gdf['fill_color'] = gdf['norm_score'].apply(lambda x: get_color_for_score(x, is_grid=False))
    
    # 클릭 시 좌표 전달을 위한 lat, lon 생성
    gdf['lat'] = gdf.geometry.centroid.y
    gdf['lon'] = gdf.geometry.centroid.x
    
    view_state = pdk.ViewState(
        latitude=gdf['lat'].mean(), 
        longitude=gdf['lon'].mean(), 
        zoom=zoom
    )

    geo_layer = pdk.Layer(
        "GeoJsonLayer", gdf, id="geojson",
        pickable=True, stroked=True, filled=True,
        get_fill_color='fill_color', get_line_color=[255, 255, 255],
        get_line_width=20, auto_highlight=True
    )

    return pdk.Deck(
        layers=[geo_layer],
        initial_view_state=view_state,
        tooltip={"html": f"<b>{{emd_nm}}</b><br/>{title_col}: {{display_val}}"},
        map_style=pdk.map_styles.ROAD
    )

def draw_cylinder_map(df, boundary, value_col="Risk_Score", title_col="위험도", min_v=None, max_v=None):
    """상세 그리드 지도 (네모 기둥)"""
    df = df.copy()
    df['display_val'] = df[value_col].round(2)

    if min_v is None: min_v = df[value_col].min()
    if max_v is None: max_v = df[value_col].max()
    
    df['norm_score'] = (df[value_col] - min_v) / (max_v - min_v) if max_v > min_v else 0
    df['color'] = df['norm_score'].apply(lambda x: get_color_for_score(x, is_grid=True))
    
    view_state = pdk.ViewState(
        latitude=df['lat'].mean(), 
        longitude=df['lon'].mean(), 
        zoom=13, pitch=60
    )

    boundary_layer = pdk.Layer(
        "GeoJsonLayer", boundary, id="boundary", 
        stroked=True, filled=False, 
        get_line_color=[255, 255, 0], get_line_width=80
    )

    grid_layer = pdk.Layer(
        "GridCellLayer", df, id="grid",
        get_position='[lon, lat]', get_elevation='norm_score',
        elevation_scale=100, cellSize=230, extruded=True,
        get_fill_color='color', pickable=True, auto_highlight=True
    )

    return pdk.Deck(
        layers=[boundary_layer, grid_layer],
        initial_view_state=view_state,
        tooltip={"html": f"{title_col}: {{display_val}}"},
        map_style=pdk.map_styles.ROAD
    )
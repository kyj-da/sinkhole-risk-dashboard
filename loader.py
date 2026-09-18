import pandas as pd
import geopandas as gpd
import streamlit as st

# 1. [1단계 변신] 숫자 코드 -> 상세 지역명
SIG_CODE_MAP = {
    "41111": "수원시 장안구", "41113": "수원시 권선구", "41115": "수원시 팔달구", "41117": "수원시 영통구",
    "41131": "성남시 수정구", "41133": "성남시 중원구", "41135": "성남시 분당구",
    "41150": "의정부시", "41171": "안양시 만안구", "41173": "안양시 동안구",
    "41190": "부천시", "41192": "부천시 원미구", "41194": "부천시 소사구", "41196": "부천시 오정구",
    "41210": "광명시", "41220": "평택시", "41250": "동두천시",
    "41271": "안산시 상록구", "41273": "안산시 단원구",
    "41281": "고양시 덕양구", "41285": "고양시 일산동구", "41287": "고양시 일산서구",
    "41290": "과천시", "41310": "구리시", "41360": "남양주시", "41370": "오산시",
    "41390": "시흥시", "41410": "군포시", "41430": "의왕시", "41450": "하남시",
    "41461": "용인시 처인구", "41463": "용인시 기흥구", "41465": "용인시 수지구",
    "41480": "파주시", "41500": "이천시", "41550": "안성시", "41570": "김포시",
    "41590": "화성시", "41610": "광주시", "41630": "양주시", "41650": "포천시",
    "41670": "여주시", "41800": "연천군", "41820": "가평군", "41830": "양평군"
}

# 2. [2단계 변신] 퉁치기 (구 -> 시)
CITY_MERGE_MAP = {
    "수원시 장안구": "수원시", "수원시 권선구": "수원시", "수원시 팔달구": "수원시", "수원시 영통구": "수원시",
    "성남시 수정구": "성남시", "성남시 중원구": "성남시", "성남시 분당구": "성남시",
    "안양시 만안구": "안양시", "안양시 동안구": "안양시",
    "안산시 상록구": "안산시", "안산시 단원구": "안산시",
    "고양시 덕양구": "고양시", "고양시 일산동구": "고양시", "고양시 일산서구": "고양시",
    "용인시 처인구": "용인시", "용인시 기흥구": "용인시", "용인시 수지구": "용인시",
    "부천시 원미구": "부천시", "부천시 소사구": "부천시", "부천시 오정구": "부천시",
    "천안시 동남구": "천안시", "천안시 서북구": "천안시",
    "청주시 상당구": "청주시", "청주시 서원구": "청주시", "청주시 흥덕구": "청주시", "청주시 청원구": "청주시",
    "포항시 남구": "포항시", "포항시 북구": "포항시",
    "창원시 의창구": "창원시", "창원시 성산구": "창원시", "창원시 마산합포구": "창원시", "창원시 마산회원구": "창원시", "창원시 진해구": "창원시",
    "전주시 완산구": "전주시", "전주시 덕진구": "전주시"
}

@st.cache_data
def load_data():
    try:
        df1 = gpd.read_parquet("final_dashboard_data_1.parquet")
        df2 = gpd.read_parquet("final_dashboard_data_2.parquet")

        df = pd.concat([df1, df2], ignore_index=True)
        df = gpd.GeoDataFrame(df, geometry="geometry", crs=df1.crs)

        gdf_dong = pd.read_pickle("dong_boundary.pkl")
    except FileNotFoundError:
        st.error("❌ 데이터 파일이 없습니다!")
        st.stop()

    # 1. 지도 데이터 컬럼 정리
    sig_candidates = ['sig_cd', 'SIG_CD', 'SIG_KOR_NM', 'SGG_NM', 'SIG_NM', 'sig_kor_nm', 'sgg_nm', 'sig_nm']
    found_sig_col = next((col for col in sig_candidates if col in gdf_dong.columns), None)

    emd_candidates = ['emd_nm', 'EMD_NM', 'EMD_KOR_NM', 'DONG', 'emd_kor_nm', 'dong']
    found_emd_col = next((col for col in emd_candidates if col in gdf_dong.columns), None)

    rename_dict = {}
    if found_sig_col:
        rename_dict[found_sig_col] = 'sjoin_sig'
    else:
        st.error("❌ 시군구 컬럼을 못 찾았습니다."); st.stop()

    if found_emd_col:
        rename_dict[found_emd_col] = 'sjoin_emd'
    else:
        st.error("❌ 읍면동 컬럼을 못 찾았습니다."); st.stop()

    gdf_clean = gdf_dong.rename(columns=rename_dict).copy()

    # 1단계 변신: 숫자 -> 이름
    gdf_clean['sjoin_sig'] = gdf_clean['sjoin_sig'].astype(str).map(SIG_CODE_MAP).fillna(gdf_clean['sjoin_sig'])

    # 2. 좌표계 통일
    if gdf_clean.crs != "EPSG:4326":
        gdf_clean = gdf_clean.to_crs("EPSG:4326")

    if not isinstance(df, gpd.GeoDataFrame):
        if 'geometry' in df.columns:
            df = gpd.GeoDataFrame(df, geometry='geometry')
            if df.crs is None: df.set_crs(epsg=5179, inplace=True)
        else:
            st.error("위치 정보가 없습니다."); st.stop()

    if df.crs != "EPSG:4326":
        df = df.to_crs("EPSG:4326")

    # 3. 공간 결합
    gdf_for_join = gdf_clean[['geometry', 'sjoin_sig', 'sjoin_emd']]
    df_joined = gpd.sjoin(df, gdf_for_join, how="inner", predicate="within")

    df_joined['sig_cd'] = df_joined['sjoin_sig']
    df_joined['emd_nm'] = df_joined['sjoin_emd']
    df_joined['lon'] = df_joined.geometry.centroid.x
    df_joined['lat'] = df_joined.geometry.centroid.y

    # 4. [퉁치기] 2단계 변신 (구 -> 시)
    df_joined['sig_cd'] = df_joined['sig_cd'].replace(CITY_MERGE_MAP)
    gdf_clean['sig_cd'] = gdf_clean['sjoin_sig'].replace(CITY_MERGE_MAP)
    gdf_clean['emd_nm'] = gdf_clean['sjoin_emd']

    # 5. 통계 및 병합
    city_stats = df_joined.groupby('sig_cd')['Risk_Score'].mean().reset_index()
    city_stats.columns = ['sig_cd', 'Avg_Risk']

    # 🚨 들여쓰기 교정 완료
    if 'sig_cd' in gdf_clean.columns:
        gdf_city = gdf_clean.dissolve(by='sig_cd').reset_index()
        # [복구] 시군구 이름을 emd_nm 자리에 넣어줌
        gdf_city['emd_nm'] = gdf_city['sig_cd'] 
        gdf_city = gdf_city.merge(city_stats, on='sig_cd', how='left')
        gdf_city['Avg_Risk'] = gdf_city['Avg_Risk'].fillna(0)
    else:
        gdf_city = gdf_clean

    return df_joined, gdf_city, gdf_clean
import streamlit as st
import loader
import maps
import altair as alt
import pandas as pd
import numpy as np

# 1. 페이지 설정
st.set_page_config(layout="wide", page_title="싱크홀 위험 지도 Final")

# 2. CSS 스타일
st.markdown("""
    <style>
    .metric-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .stButton>button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로딩
with st.spinner("데이터 로딩 중..."):
    df_grid, gdf_city, gdf_dong = loader.load_data()

# ---------------------------------------------------------
# 🎛️ 사이드바
# ---------------------------------------------------------
st.sidebar.image("inx.gif", use_container_width=True)
st.sidebar.title("🎛️ 분석 설정")
sig_list = sorted(df_grid['sig_cd'].unique())
selected_sig = st.sidebar.selectbox("시/군/구", ["경기도 전체"] + sig_list)

if selected_sig != "경기도 전체":
    emd_list = sorted(df_grid[df_grid['sig_cd'] == selected_sig]['emd_nm'].unique())
    selected_emd = st.sidebar.selectbox("읍면동", ["전체"] + emd_list)
else:
    selected_emd = "전체"

LAYER_MAPPING = {
    "Risk_Score": "🚨 종합 위험도",
    "sw_rep_rt": "🔧 하수관 보수율",
    "rd_dens": "🚗 도로 밀도",
    "avg_age": "🏚️ 건물 노후도",
    "population": "👥 인구 수",
    "rain_sum": "☔ 누적 강수량"
}

available_layers = {k: v for k, v in LAYER_MAPPING.items() if k in df_grid.columns}
selected_layer_col = st.sidebar.radio("🗺️ 주제", options=list(available_layers.keys()), format_func=lambda x: available_layers[x])
layer_kor_name = available_layers[selected_layer_col]

# ✅ [요청 1] 주제와 필터 사이에 가로줄 추가
st.sidebar.markdown("---")

# 기준값 설정
if selected_layer_col == "Risk_Score":
    MIN_GLOBAL, MAX_GLOBAL = 0.0, 1.0
elif selected_layer_col in ["population", "sw_rep_rt"]:
    MIN_GLOBAL = float(df_grid[selected_layer_col].min())
    MAX_GLOBAL = float(df_grid[selected_layer_col].quantile(0.95))
else:
    MIN_GLOBAL = float(df_grid[selected_layer_col].min())
    MAX_GLOBAL = float(df_grid[selected_layer_col].quantile(0.85))

min_risk = st.sidebar.slider(f"🔍 필터 기준", 0.0, float(df_grid[selected_layer_col].max()), 0.0)

# ---------------------------------------------------------
# 메인 화면 구성
# ---------------------------------------------------------
st.title(f"📍 {selected_sig} {selected_emd if selected_emd != '전체' else ''} [{layer_kor_name}]")
col1, col2 = st.columns([3, 1])

# 차트 색상 함수
def get_hex_color_dynamic(val, min_v, max_v):
    if pd.isna(val): return "#d3d3d3"
    norm = (val - min_v) / (max_v - min_v) if max_v > min_v else 0
    colors = ["#4caf50", "#8bc34a", "#ffeb3b", "#ff9800", "#f44336"]
    return colors[min(int(norm * 5), 4)]

with col1:
    deck, current_data, view_level = None, None, "top"
    
    if selected_sig == "경기도 전체":
        view_level = "top"
        plot_data = gdf_city.copy()
        stats = df_grid.groupby('sig_cd')[selected_layer_col].mean().reset_index()
        plot_data = plot_data.drop(columns=[selected_layer_col], errors='ignore').merge(stats, on='sig_cd', how='left').fillna(0)
        deck = maps.draw_choropleth_map(plot_data, selected_layer_col, layer_kor_name, MIN_GLOBAL, MAX_GLOBAL, zoom=8.5)
        current_data = plot_data[['emd_nm', selected_layer_col]].sort_values(selected_layer_col, ascending=False).rename(columns={'emd_nm': '지역명', selected_layer_col: '값'})

    elif selected_emd == "전체":
        view_level = "city"
        plot_data = gdf_dong[gdf_dong['sig_cd'] == selected_sig].copy()
        stats = df_grid[df_grid['sig_cd'] == selected_sig].groupby('emd_nm')[selected_layer_col].mean().reset_index()
        plot_data = plot_data.merge(stats, on='emd_nm', how='left').fillna(0)
        deck = maps.draw_choropleth_map(plot_data, selected_layer_col, layer_kor_name, MIN_GLOBAL, MAX_GLOBAL, zoom=10.5)
        current_data = plot_data[['emd_nm', selected_layer_col]].sort_values(selected_layer_col, ascending=False).rename(columns={'emd_nm': '지역명', selected_layer_col: '값'})
    
    else:
        view_level = "grid"
        filtered_df = df_grid[(df_grid['sig_cd'] == selected_sig) & (df_grid['emd_nm'] == selected_emd) & (df_grid[selected_layer_col] >= min_risk)].copy()
        if not filtered_df.empty:
            deck = maps.draw_cylinder_map(filtered_df, gdf_dong[gdf_dong['emd_nm'] == selected_emd], selected_layer_col, layer_kor_name, MIN_GLOBAL, MAX_GLOBAL)
            current_data = filtered_df[[selected_layer_col, 'lat', 'lon']].copy().rename(columns={selected_layer_col: '값'})
            current_data['지역명'] = filtered_df.index

    # 1. 지도 출력
    selection = st.pydeck_chart(deck, use_container_width=True, height=600, on_select="rerun") if deck else None

    # 2. 상세 데이터 (맵 밑)
    st.markdown("---")
    # ✅ [요청 3] 그리드 단계 포함 무조건 닫힘 설정 (expanded=False)
    with st.expander("📋 상세 순위 데이터", expanded=False):
        if view_level == "grid" and 'filtered_df' in locals():
            st.dataframe(filtered_df.drop(columns=['geometry'], errors='ignore'), use_container_width=True)
        elif current_data is not None:
            st.dataframe(current_data, use_container_width=True)

with col2:
    if current_data is not None and not current_data.empty:
        st.markdown(f"""<div class="metric-card"><h4>📊 통계</h4><p>평균: <strong>{current_data['값'].mean():.2f}</strong></p><p>최고: <strong>{current_data.iloc[0]['지역명']}</strong></p></div>""", unsafe_allow_html=True)

        if view_level == "grid":
            # ✅ 파이차트 영역: 버디가 준 Baseline 코드를 100% 그대로 사용
            st.markdown(f"#### 🥧 {layer_kor_name} 분포 (%)")
            step = (MAX_GLOBAL - MIN_GLOBAL) / 5
            bins = [MIN_GLOBAL + step*i for i in range(6)]
            current_data['구간'] = pd.cut(current_data['값'], bins=bins, labels=["1단계", "2단계", "3단계", "4단계", "5단계"], include_lowest=True)
            pie_df = current_data['구간'].value_counts(sort=False).reset_index()
            pie_df.columns = ['구간', '개수']
            total = pie_df['개수'].sum()
            pie_df['퍼센트'] = pie_df['개수'].apply(lambda x: f'{(x/total)*100:.1f}%' if x > 0 else '')
            base = alt.Chart(pie_df).encode(theta=alt.Theta("개수:Q", stack=True), color=alt.Color("구간:N", scale=alt.Scale(domain=["1단계", "2단계", "3단계", "4단계", "5단계"], range=["#4caf50", "#8bc34a", "#ffeb3b", "#ff9800", "#f44336"])))
            st.altair_chart(base.mark_arc(outerRadius=100) + base.mark_text(radius=125, fontWeight="bold").encode(text="퍼센트:N"), use_container_width=True)
        else:
            st.markdown(f"#### 🏆 Top 10 순위")
            current_data['Color'] = current_data['값'].apply(lambda x: get_hex_color_dynamic(x, MIN_GLOBAL, MAX_GLOBAL))
            
            # ✅ [요청 4] [지역명], [값] 축 라벨 제거 (title=None)
            chart = alt.Chart(current_data.head(10)).mark_bar().encode(
                x=alt.X('값', title=None), 
                y=alt.Y('지역명:N', sort=None, title=None), 
                color=alt.Color('Color:N', scale=None),
                tooltip=['지역명', '값']
            ).properties(height=350)
            st.altair_chart(chart, use_container_width=True)

        st.markdown("---")
        st.subheader("🛣️ 현장 로드뷰")
        
        # ✅ [요청 2] 그리드 뎊스에서 격자 선택 시에만 버튼 활성화
        has_selection = False
        if view_level == "grid":
            if selection and "selection" in selection and selection["selection"]["objects"]:
                obj_list = list(selection["selection"]["objects"].values())
                if obj_list and len(obj_list[0]) > 0:
                    selected_obj = obj_list[0][0]
                    lat, lon = selected_obj.get("lat"), selected_obj.get("lon")
                    if lat and lon:
                        has_selection = True
                        st.success(f"📍 선택: {lat:.4f}, {lon:.4f}")
                        st.link_button("🏙️ 카카오 로드뷰 열기", f"https://map.kakao.com/link/roadview/{lat},{lon}", type="primary")
        
        if not has_selection:
            if view_level == "grid":
                st.info("지도의 격자를 클릭하면 로드뷰 버튼이 나타납니다.")
            else:
                st.warning("로드뷰는 그리드(읍면동 상세) 지도에서만 가능합니다.")
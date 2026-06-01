import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

# 페이지 레이아웃 설정
st.set_page_config(page_title="연교차 분석 대시보드", layout="wide")

st.title("🌡️ 1980년대 전후 연교차 변화 추이 분석")
st.markdown("""
1980년대 이전과 이후의 기후 변화로 인해 **연교차(Annual Temperature Range)**에 유의미한 차이가 발생했는지 대화형 그래프로 분석합니다.
""")

# 데이터 로드 및 전처리 함수
@st.cache_data
def load_and_process_data(file_path):
    df = pd.read_csv(file_path)
    
    # 컬럼명 공백 제거 및 날짜 정제
    df.columns = df.columns.str.strip()
    df['날짜'] = df['날짜'].astype(str).str.replace(r'\s+', '', regex=True)
    df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
    
    # 결측치 제거 후 연도 추출
    df = df.dropna(subset=['날짜', '최고기온(℃)', '최저기온(℃)'])
    df['연도'] = df['날짜'].dt.year
    
    # 연도별 최고기온의 맥스, 최저기온의 미니멈 계산
    yearly = df.groupby('연도').agg(
        max_temp=('최고기온(℃)', 'max'),
        min_temp=('최저기온(℃)', 'min')
    ).reset_index()
    
    # 연교차 계산
    yearly['temp_range'] = yearly['max_temp'] - yearly['min_temp']
    
    # 1980년 기준 그룹 분리 (클라우드 한글 깨짐 방지를 위해 영문 명명)
    yearly['Group'] = yearly['연도'].apply(lambda x: 'Before 1980' if x < 1980 else 'After 1980')
    
    return yearly

# 데이터 실행
try:
    data_path = "ta_20260601093156.csv"
    yearly_df = load_and_process_data(data_path)
    
    # ------------------ 대시보드 화면 구성 ------------------
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.subheader("📊 그룹별 연교차 요약 통계")
        summary = yearly_df.groupby('Group')['temp_range'].describe().round(2)
        # 보기 좋게 컬럼명 한글화하여 출력
        summary.index.name = '그룹'
        summary.columns = ['데이터 개수', '평균 연교차', '표준편차', '최소값', '25%', '50%(중앙값)', '75%', '최대값']
        st.dataframe(summary, use_container_width=True)
        
        # 통계적 가설 검정 (t-test)
        before_series = yearly_df[yearly_df['Group'] == 'Before 1980']['temp_range']
        after_series = yearly_df[yearly_df['Group'] == 'After 1980']['temp_range']
        t_stat, p_value = stats.ttest_ind(before_series, after_series, equal_var=False)
        
        st.markdown("### 🔬 독립표본 t-검정 결과")
        st.metric(label="t-통계량 (t-statistic)", value=f"{t_stat:.4f}")
        st.metric(label="p-값 (p-value)", value=f"{p_value:.4f}")
        
        if p_value < 0.05:
            st.success("🎉 **가설 지지:** p-value가 0.05보다 작으므로, 1980년대 이전과 이후의 연교차는 **통계적으로 유의미한 차이가 있습니다.**")
        else:
            st.warning("⚠️ **가설 미지지:** p-value가 0.05보다 크므로, 1980년대 전후의 연교차 차이는 **통계적으로 유의미하다고 보기 어렵습니다.**")

    with col2:
        st.subheader("📉 연도별 연교차 시계열 추이 분석 (Interactive)")
        
        # 시계열 라인 차트 생성
        fig_line = px.line(
            yearly_df, x='연도', y='temp_range', 
            markers=True, title="Annual Temperature Range Trend Over Years",
            labels={'연도': 'Year', 'temp_range': 'Temperature Range (°C)'},
            color_discrete_sequence=['#7f7f7f']
        )
        
        # 1980년 세로 기준선 추가
        fig_line.add_vline(x=1980, line_width=2, line_dash="dash", line_color="red", annotation_text="1980")
        
        # 그룹별 평균선 계산 및 추가
        mean_before = before_series.mean()
        mean_after = after_series.mean()
        
        fig_line.add_shape(type="line", x0=yearly_df['연도'].min(), y0=mean_before, x1=1979, y1=mean_before,
                           line=dict(color="Blue", width=3), name="Before 1980 Mean")
        fig_line.add_shape(type="line", x0=1980, y0=mean_after, x1=yearly_df['연도'].max(), y1=mean_after,
                           line=dict(color="Orange", width=3), name="After 1980 Mean")
        
        fig_line.update_layout(hovermode="x unified", template="plotly_white")
        st.plotly_chart(fig_line, use_container_width=True)

    st.write("---")
    
    # 하단 데이터 분포 비교 (Boxplot)
    st.subheader("📦 데이터 분포 및 편차 비교 (Boxplot)")
    
    fig_box = px.box(
        yearly_df, x='Group', y='temp_range', color='Group',
        points="all", title="Comparison of Temperature Range Distribution",
        labels={'Group': 'Period', 'temp_range': 'Temperature Range (°C)'},
        color_discrete_map={'Before 1980': '#1f77b4', 'After 1980': '#ff7f0e'}
    )
    fig_box.update_layout(template="plotly_white")
    st.plotly_chart(fig_box, use_container_width=True)

except FileNotFoundError:
    st.error("❌ 데이터 파일(`ta_20260601093156.csv`)을 찾을 수 없습니다. 파일 이름을 확인하거나 같은 경로에 올려주세요.")

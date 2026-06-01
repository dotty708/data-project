import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# 페이지 설정
st.set_page_config(page_title="연교차 변화 분석 앱", layout="wide")

st.title("🌡️ 1980년대 전후 연교차 변화 비교 분석")
st.markdown("""
1980년대 이전과 이후의 기후 변화로 인해 **연교차(Annual Temperature Range)**에 유의미한 차이가 발생했는지 분석합니다.
업로드하신 서울 기상 데이터(`ta_20260601093156.csv`)를 기반으로 구동됩니다.
""")

# 데이터 로드 함수
@st.cache_data
def load_data(file_path):
    # CSV 파일 읽기
    df = pd.read_csv(file_path)
    
    # 컬럼명 공백 제거 및 날짜 데이터 정제 ('\t1907-10-01' 형식 대응)
    df.columns = df.columns.str.strip()
    df['날짜'] = df['날짜'].astype(str).str.replace(r'\s+', '', regex=True)
    df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
    
    # 결측치 제거
    df = df.dropna(subset=['날짜', '최고기온(℃)', '최저기온(℃)'])
    
    # 연도 컬럼 추가
    df['연도'] = df['날짜'].dt.year
    
    # 연도별 최고기온의 최댓값, 최저기온의 최솟값 구하기
    yearly_data = df.groupby('연도
    ').agg(
        최고기온_max=('최고기온(℃)', 'max'),
        최저기온_min=('최저기온(℃)', 'min')
    ).reset_index()
    
    # 연교차 계산 (그 해 가장 더웠던 날 - 가장 추웠던 날)
    yearly_data['연교차'] = yearly_data['최고기온_max'] - yearly_data['최저기온_min']
    
    # 1980년 기준으로 그룹 분리 (1980년 포함 여부에 따라 설정 가능, 여기선 1980년 미만 / 이상)
    yearly_data['그룹'] = yearly_data['연도'].apply(lambda x: '1980년 이전' if x < 1980 else '1980년 이후')
    
    return yearly_data

# 로컬에 있는 파일 혹은 스트림릿에 내장할 파일 경로 (같은 디렉토리에 있다고 가정)
try:
    data_path = "ta_20260601093156.csv"
    yearly_df = load_data(data_path)
    
    # ------------------ 대시보드 레이아웃 ------------------
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 그룹별 연교차 기초통계량")
        summary = yearly_df.groupby('그룹')['연교차'].describe().round(2)
        st.dataframe(summary, use_container_width=True)
        
        # 가설 검정 (독립표본 t-검정)
        group_before = yearly_df[yearly_df['그룹'] == '1980년 이전']['연교차']
        group_after = yearly_df[yearly_df['그룹'] == '1980년 이후']['연교차']
        
        t_stat, p_value = stats.ttest_ind(group_before, group_after, equal_var=False)
        
        st.markdown("### 🔬 통계적 가설 검정 (t-test)")
        st.write(f"- **t-통계량(t-statistic):** {t_stat:.4f}")
        st.write(f"- **p-값(p-value):** {p_value:.4f}")
        
        if p_value < 0.05:
            st.success("🎉 **결론:** p-value가 0.05보다 작으므로, 1980년 이전과 이후의 연교차는 **통계적으로 유의미한 차이가 있습니다.**")
        else:
            st.warning("⚠️ **결론:** p-value가 0.05보다 크므로, 1980년 이전과 이후의 연교차 차이는 **통계적으로 유의미하지 않습니다.**")

    with col2:
        st.subheader("📉 연도별 연교차 추세 (시계열)")
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # 한글 폰트 깨짐 방지 설정 (스트림릿 클라우드 배포 시 기본 폰트 사용을 위해 무난한 스타일 지정)
        sns.set_theme(style="whitegrid")
        plt.rcParams['font.family'] = 'sans-serif' 
        
        sns.lineplot(data=yearly_df, x='연도', y='연교차', marker='o', color='gray', alpha=0.5, ax=ax)
        # 1980년 기준선
        ax.axvline(x=1980, color='red', linestyle='--', linewidth=2, label='1980년 기준선')
        
        # 그룹별 평균선 그리기
        mean_before = group_before.mean()
        mean_after = group_after.mean()
        ax.hlines(y=mean_before, xmin=yearly_df['연도'].min(), xmax=1979, color='blue', linestyle='-', linewidth=3, label=f'이전 평균 ({mean_before:.1f}℃)')
        ax.hlines(y=mean_after, xmin=1980, xmax=yearly_df['연도'].max(), color='orange', linestyle='-', linewidth=3, label=f'이후 평균 ({mean_after:.1f}℃)')
        
        ax.set_title("Annual Temperature Range Trend", fontsize=14)
        ax.set_xlabel("Year")
        ax.set_ylabel("Temperature Difference (°C)")
        ax.legend()
        st.pyplot(fig)

    st.write("---")
    
    # 하단 박스플롯 및 분포 시각화
    st.subheader("📦 분포 비교 (Boxplot & Violinplot)")
    fig2, ax2 = plt.subplots(1, 2, figsize=(12, 5))
    
    sns.boxplot(data=yearly_df, x='그룹', y='연교차', palette='Set2', ax=ax2[0])
    ax2[0].set_title("Boxplot of Temperature Range")
    ax2[0].set_ylabel("°C")
    
    sns.violinplot(data=yearly_df, x='그룹', y='연교차', palette='Pastel1', ax=ax2[1])
    ax2[1].set_title("Violinplot of Temperature Range")
    ax2[1].set_ylabel("°C")
    
    st.pyplot(fig2)
    
    # 데이터 테이블 보여주기
    if st.checkbox("전체 정제 데이터 보기"):
        st.dataframe(yearly_df, use_container_width=True)

except FileNotFoundError:
    st.error("❌ `ta_20260601093156.csv` 파일을 찾을 수 없습니다. 대시보드 앱과 같은 폴더에 파일을 배치해주세요.")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

# ตั้งค่า page config
st.set_page_config(
    page_title="Student Assessment Report",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ฟังก์ชันเตรียมข้อมูล (นำมาจากโค้ดเดิม)
def prepare_data_for_analysis(df):
    """
    เตรียมข้อมูลสำหรับการทำกราฟ clustering
    """
    
    # สร้างคอลัมน์เพื่อแยกนักเรียนจำลองกับนักเรียนจริง
    df['IS_SIMULATED'] = df['ALIAS'].str.startswith('Sim')
    df['STUDENT_CATEGORY'] = df['IS_SIMULATED'].map({True: 'Simulated', False: 'Real'})
    
    # คำนวณคะแนนเฉลี่ยในกลุ่มต่างๆ
    df['STEM_AVG'] = (df['MATH'] + df['SCIENCE']) / 2
    df['LANGUAGE_AVG'] = (df['ENGLISH'] + df['THAI']) / 2
    df['OVERALL_AVG'] = (df['MATH'] + df['SCIENCE'] + df['ENGLISH'] + df['THAI']) / 4
    
    return df

def create_interactive_scatter_plot(df, student_alias):
    """สร้าง interactive scatter plot ด้วย Plotly (แสดงเฉพาะ target + simulated students)"""
    comparison_df = prepare_data_for_analysis(df)
    
    classroom_types = ['stem_focused', 'language_focused', 'balanced_mixed', 'general']
    classroom_names = ['STEM-Focused', 'Language-Focused', 'Balanced Mixed', 'General']

    tier_colors = {
        'Diamond': "#EF28B0",
        'Platinum': "#001c9a",
        'Gold': '#F1C40F',
        'Sliver': "#51daf9",
        'Bronze': '#E74C3C'
    }

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=classroom_names,
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )

    for idx, (classroom_type, name) in enumerate(zip(classroom_types, classroom_names)):
        row = idx // 2 + 1
        col = idx % 2 + 1
        
        classroom_data = comparison_df[comparison_df['CLASSROOM_TYPE'] == classroom_type]
        target_student = classroom_data[classroom_data['ALIAS'] == student_alias]

        # ✅ แสดงนักเรียนจำลอง (Simulated) ทุกคน
        simulated_data = classroom_data[classroom_data['STUDENT_CATEGORY'] == 'Simulated']
        for tier in simulated_data['TIER'].unique():
            tier_data = simulated_data[simulated_data['TIER'] == tier]
            if len(tier_data) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=tier_data['STEM_AVG'],
                        y=tier_data['LANGUAGE_AVG'],
                        mode='markers',
                        marker=dict(
                            color=tier_colors.get(tier, '#888888'),
                            size=8,
                            symbol='circle',
                            opacity=0.6
                        ),
                        name=f'Simulated - {tier}',
                        showlegend=True if idx == 0 else False,
                        hovertemplate='<b>%{text}</b><br>STEM: %{x:.1f}<br>Language: %{y:.1f}<extra></extra>',
                        text=tier_data['ALIAS']
                    ),
                    row=row, col=col
                )

        # ✅ แสดงเฉพาะนักเรียนที่เลือก
        if len(target_student) > 0:
            fig.add_trace(
                go.Scatter(
                    x=target_student['STEM_AVG'],
                    y=target_student['LANGUAGE_AVG'],
                    mode='markers',
                    marker=dict(
                        color='red',
                        size=20,
                        symbol='diamond',
                        line=dict(width=2, color='white')
                    ),
                    name=f'{student_alias} (Target)',
                    hovertemplate='<b>%{text}</b><br>STEM: %{x:.1f}<br>Language: %{y:.1f}<extra></extra>',
                    text=target_student['ALIAS'],
                    showlegend=True if idx == 0 else False
                ),
                row=row, col=col
            )
        
        # เส้นอ้างอิง
        fig.add_hline(y=50, line_dash="dash", line_color="red", opacity=0.5, row=row, col=col)
        fig.add_vline(x=50, line_dash="dash", line_color="red", opacity=0.5, row=row, col=col)
        fig.add_trace(
            go.Scatter(
                x=[0, 100], y=[0, 100],
                mode='lines',
                line=dict(dash='dot', color='gray', width=1),
                showlegend=False,
                hoverinfo='skip'
            ),
            row=row, col=col
        )

    fig.update_layout(
        height=800,
        title_text=f"Student Performance Analysis - {student_alias}",
        title_x=0.5,
        showlegend=True
    )
    
    fig.update_xaxes(title_text="STEM Average (Math + Science)", range=[0, 100])
    fig.update_yaxes(title_text="Language Average (English + Thai)", range=[0, 100])
    
    return fig

# ฟังก์ชันสร้างกราฟเปรียบเทียบคะแนนในแต่ละวิชา
def create_subject_comparison(df, student_alias, selected_month):
    """สร้างกราฟเปรียบเทียบคะแนนในแต่ละวิชา"""
    student_data = df[(df['ALIAS'] == student_alias) & (df['MONTH'] == selected_month)]
    
    if len(student_data) == 0:
        return None

    subjects = ['MATH', 'SCIENCE', 'ENGLISH', 'THAI']
    subject_names = ['คณิตศาสตร์', 'วิทยาศาสตร์', 'ภาษาอังกฤษ', 'ภาษาไทย']
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['STEM-Focused', 'Language-Focused', 'Balanced Mixed', 'General'],
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )

    classroom_types = ['stem_focused', 'language_focused', 'balanced_mixed', 'general']
    
    for idx, classroom_type in enumerate(classroom_types):
        row = idx // 2 + 1
        col = idx % 2 + 1

        classroom_student = student_data[student_data['CLASSROOM_TYPE'] == classroom_type]

        if len(classroom_student) > 0:
            scores = [classroom_student[subject].iloc[0] for subject in subjects]

            # กำหนดสีรายแท่งตาม logic ที่คุณต้องการ
            bar_colors = []
            for i, subject in enumerate(subjects):
                score = scores[i]
                
                # เงื่อนไขการให้สีตามคะแนน
                if score < 50:
                    color = "#E74C3C"  # แดง
                elif 50 <= score < 80:
                    color = "#F1C40F"  # เหลือง
                else:
                    color = "#2ECC71"  # เขียว

                # เงื่อนไขการลบสี (ทำให้ bar โปร่ง) สำหรับบางวิชา
                if classroom_type == 'stem_focused' and subject not in ['MATH', 'SCIENCE']:
                    color = "lightgray"
                elif classroom_type == 'language_focused' and subject not in ['ENGLISH', 'THAI']:
                    color = "lightgray"

                bar_colors.append(color)

            fig.add_trace(
                go.Bar(
                    x=subject_names,
                    y=scores,
                    name=f'{classroom_type.replace("_", " ").title()}',
                    marker_color=bar_colors,
                    showlegend=False,
                    text=[f'{score:.1f}' for score in scores],
                    textposition='auto',
                ),
                row=row, col=col
            )

    fig.update_layout(
        height=600,
        title_text=f"Subject Scores Comparison - {student_alias} (Month {selected_month})",
        title_x=0.5
    )
    
    fig.update_yaxes(title_text="Score", range=[0, 100])
    
    return fig

def create_summary_table(df, student_alias, selected_month):
    """สร้างตารางสรุปผลการประเมิน"""
    student_data = df[(df['ALIAS'] == student_alias) & (df['MONTH'] == selected_month)]
    
    if len(student_data) == 0:
        return None
    
    prepared_data = prepare_data_for_analysis(student_data)
    
    summary_data = []
    for _, row in prepared_data.iterrows():
        summary_data.append({
            'Classroom Type': row['CLASSROOM_TYPE'].replace('_', ' ').title(),
            'Math': f"{row['MATH']:.1f}",
            'Science': f"{row['SCIENCE']:.1f}",
            'English': f"{row['ENGLISH']:.1f}",
            'Thai': f"{row['THAI']:.1f}",
            'STEM Avg': f"{row['STEM_AVG']:.1f}",
            'Language Avg': f"{row['LANGUAGE_AVG']:.1f}",
            'Overall Avg': f"{row['OVERALL_AVG']:.1f}",
            'Tier': row['TIER'],
            'Rank': row['RANK']
        })
    
    return pd.DataFrame(summary_data)

def create_summarize_from_summary_table(summary_df):
    """สร้างข้อความ markdown สำหรับสรุปผล"""
    if summary_df is None or len(summary_df) == 0:
        return "⚠️ ไม่พบข้อมูลนักเรียน"

    # คำอธิบายแต่ละระดับ TIER
    tier_descriptions = {
        'Diamond': "อยู่ใกล้นักเรียนอัจฉริยะ คาดว่า นักเรียนมีความสามารถเหมาะสมในห้องเรียนนี้",
        'Platinum': "อยู่ใกล้นักเรียนเก่ง คาดว่า นักเรียนสามารถเรียนในห้องเรียนนี้ได้และจะพัฒนาได้ดีในห้องเรียนนี้",
        'Gold': "อยู่ใกล้นักเรียนดี คาดว่า  นักเรียนสามารถเรียนในห้องเรียนนี้ได้",
        'Silver': "อยู่ใกล้นักเรียนพอใช้ คาดว่า นักเรียนสามารถเรียนในห้องเรียนนี้ได้ แต่ต้องพัฒนาตัวเองอย่างสม่ำเสมอ",
        'Bronze': "อยู่ใกล้นักเรียนที่ต้องพัฒนา คาดว่า นักเรียนต้องพัฒนาตัวเองให้มากกว่าเดิม"
    }

    # กรองเฉพาะห้องเรียนจำลอง (ไม่รวม 'General')
    simulated_df = summary_df[summary_df['Classroom Type'] != 'General']
    
    # หา Overall Avg สูงสุดในห้องเรียนจำลอง
    best_row = simulated_df.loc[simulated_df['Overall Avg'].astype(float).idxmax()]
    best_classroom = best_row['Classroom Type']
    best_score = best_row['Overall Avg']
    best_tier = best_row['Tier']
    detail_best_tier = tier_descriptions.get(best_tier, "ไม่มีคำอธิบาย")

    # หาค่าจากห้องเรียนทั่วไป
    general_row = summary_df[summary_df['Classroom Type'] == 'General'].iloc[0]
    general_score = general_row['Overall Avg']
    general_tier = general_row['Tier']
    detail_general_tier = tier_descriptions.get(general_tier, "ไม่มีคำอธิบาย")

    markdown_text = f"""
        ### 🧠 สรุปผลการจำลองศักยภาพนักเรียน

        1. หากวัดจากในห้องเรียนจำลองทั้งหมด:  
        นักเรียนมีผลการเรียนที่ดีที่สุดในห้องเรียน **{best_classroom}**  
        อยู่ในระดับใกล้เคียงกับ **{best_tier}** → _{detail_best_tier}_

        2. หากวัดจากห้องเรียนทั่วไปตามมาตรฐาน:  
        นักเรียนจะมีคะแนนเฉลี่ย **{general_score}**  
        อยู่ในระดับใกล้เคียงกับ **{general_tier}** → _{detail_general_tier}_
        """
    return markdown_text


def plot_classroom_cluster(df):
    """Interactive Scatter Plot (Plotly) แสดง STEM vs Language พร้อมแบ่ง Zoning ทั้ง 9 โซน"""
    
    cluster_df = prepare_data_for_analysis(df)  # สมมติว่าเตรียม df แล้วมี 'STEM_AVG', 'LANGUAGE_AVG', 'CLUSTER'

    cluster_colors = {
        'Very High': "#00ff2f",
        'High': "#8e44ad",
        'Medium': "#f1c40f",
        'Low': "#5dade2",
        'Very Low': "#c0392b"
    }

    zones = [
        (0, 50, 0, 50, "Warning Zone", "#f9ebea"),
        (0, 50, 50, 80, "STEM Support", "#fef9e7"),
        (0, 50, 80, 100, "Language Expert", "#eafaf1"),
        (50, 80, 0, 50, "Language Support", "#fef5e7"),
        (50, 80, 50, 80, "Development Zone", "#e8f8f5"),
        (80, 100, 0, 50, "STEM Expert", "#f4ecf7"),
        (80, 100, 50, 80, "STEM Strong", "#e8daef"),
        (50, 80, 80, 100, "Language Strong", "#eaf2f8"),
        (80, 100, 80, 100, "Perfect Zone", "#d4efdf")
    ]

    fig = go.Figure()

    # วาด zoning พื้นหลัง
    for xmin, xmax, ymin, ymax, label, color in zones:
        fig.add_shape(
            type="rect",
            x0=xmin, x1=xmax,
            y0=ymin, y1=ymax,
            fillcolor=color,
            opacity=0.3,
            line_width=0
        )
        fig.add_annotation(
            x=(xmin + xmax)/2,
            y=(ymin + ymax)/2,
            text=label,
            showarrow=False,
            font=dict(size=10, color="black")
        )

    # วาด scatter plot
    for cluster, group in cluster_df.groupby('CLUSTER'):
        fig.add_trace(go.Scatter(
            x=group['STEM_AVG'],
            y=group['LANGUAGE_AVG'],
            mode='markers',
            name=cluster,
            marker=dict(
                color='red',
                size=20,
                symbol='diamond',
                line=dict(width=1, color='white')
            ),
            text=group.get('STUDENT_NAME', None),  # ถ้ามีชื่อ
            hoverinfo='text+x+y'
        ))

    # เส้นแบ่ง
    fig.add_shape(type="line", x0=50, x1=50, y0=0, y1=100,
                  line=dict(color="red", dash="dash", width=1))
    fig.add_shape(type="line", x0=80, x1=80, y0=0, y1=100,
                  line=dict(color="gray", dash="dot", width=1))
    fig.add_shape(type="line", x0=0, x1=100, y0=50, y1=50,
                  line=dict(color="red", dash="dash", width=1))
    fig.add_shape(type="line", x0=0, x1=100, y0=80, y1=80,
                  line=dict(color="gray", dash="dot", width=1))
    fig.add_shape(type="line", x0=0, x1=100, y0=0, y1=100,
                  line=dict(color="gray", dash="dot", width=1))

    fig.update_layout(
        title='Student Performance by Zone and Cluster',
        xaxis=dict(title='STEM Average (Math + Science)', range=[0, 100]),
        yaxis=dict(title='Language Average (English + Thai)', range=[0, 100]),
        plot_bgcolor='white',
        legend_title='Cluster',
        height=700
    )

    return fig

# Main Streamlit App
def main():
    # Header
    st.image("bd-logo.png", width=2000)  # ใส่ชื่อไฟล์และกำหนดขนาด
    st.title("Bewdar Academy Lamphun: Student Assessment Report")
    
    # โหลดข้อมูลจากทุกระดับชั้น
    @st.cache_data
    def load_data_by_level(levels, sheet_name):
        try:
            # หาตำแหน่งไฟล์ที่แน่นอน
            current_dir = Path(__file__).parent
            file_path = current_dir / "data" / f"export_all_outputs_{levels}.xlsx"
            
            # Debug: แสดงข้อมูล path
            st.write(f"Current directory: {current_dir}")
            st.write(f"Looking for file at: {file_path}")
            st.write(f"File exists: {file_path.exists()}")
            
            if not file_path.exists():
                st.error(f"❌ ไม่พบไฟล์: {file_path}")
                return pd.DataFrame()
                
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            df["LEVEL"] = sheet_name
            return df
            
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            st.error(f"❌ ระดับชั้น {levels} ยังไม่พร้อมสำหรับการประเมินผล")
            return pd.DataFrame()

    # รายการระดับชั้นที่มี
    levels = ["Primary1", "Primary2", "Primary3", "Primary4", "Primary5", "Primary6"]

    # Sidebar Input
    with st.sidebar:
        st.header("🔍 Student Information")
        st.markdown("กรุณาเลือกระดับชั้นและชื่อนักเรียน")

        selected_level = st.selectbox("🏫 ระดับชั้น", options=[""] + levels)

        if selected_level:
            load_analysis_sheet_name = "Analysis_" + selected_level
            load_analysis_our_students_name = "OurStudent_" + selected_level

            df = load_data_by_level(selected_level, load_analysis_sheet_name)
            df_our_students = load_data_by_level(selected_level, load_analysis_our_students_name)


            if df.empty:
                st.warning("⚠️ ไม่พบข้อมูลในระดับนี้")
            else:
                available_aliases = df['ALIAS'].unique()
                real_students = [alias for alias in available_aliases if not alias.startswith('Sim')]

                student_alias = st.selectbox(
                    "🎓 Student Name (ALIAS)",
                    options=[""] + list(real_students),
                    help="เลือกชื่อนักเรียน (ALIAS) ของลูกคุณ"
                )

                if student_alias:
                    available_months = sorted(df[df['ALIAS'] == student_alias]['MONTH'].unique())
                    selected_month = st.selectbox(
                        "📅 Assessment Month",
                        options=available_months,
                        help="เลือกเดือนที่ต้องการดูผลการประเมิน"
                    )

                    if selected_month:
                        student_info = df[(df['ALIAS'] == student_alias) & (df['MONTH'] == selected_month)]
                        if not student_info.empty:
                            st.success(f"✅ พบข้อมูลของ {student_alias} ในเดือน {selected_month}")
                            st.info(f"📚 ระดับชั้น: {selected_level}")
                        else:
                            st.warning("⚠️ ไม่พบข้อมูลสำหรับเดือนที่เลือก")
                else:
                    st.info("👆 กรุณาเลือกชื่อนักเรียน")
        else:
            st.info("👈 กรุณาเลือกระดับชั้นก่อน")
        
    
    # Main content
    if 'student_alias' in locals() and student_alias and 'selected_month' in locals() and selected_month:
        student_data = df[(df['ALIAS'] == student_alias) & (df['MONTH'] == selected_month)]
        student_data_in_class = df_our_students[(df_our_students['ALIAS'] == student_alias) & (df_our_students['MONTH'] == selected_month)]
        
        if len(student_data) == 0:
            st.error("❌ ไม่พบข้อมูลสำหรับนักเรียนและเดือนที่เลือก")
            return
        
        # Section 1: Overview
        st.markdown("---")
        st.header("📊 สรุปผลคะแนนและเวลาเรียนทั้งหมด")
        
        col1, col2, col3 = st.columns(3)
        
        prepared_data = prepare_data_for_analysis(student_data)
        avg_overall = prepared_data['OVERALL_AVG'].mean()
        avg_stem = prepared_data['STEM_AVG'].mean()
        avg_language = prepared_data['LANGUAGE_AVG'].mean()

        math_learning_period = student_data['MATH_TIME_HR'].unique()[0] * 60
        science_learning_period = student_data['SCIENCE_TIME_HR'].unique()[0] * 60
        english_learning_period = student_data['ENGLISH_TIME_HR'].unique()[0] * 60
        thai_learning_period = student_data['THAI_TIME_HR'].unique()[0] * 60 

        math_learning_topic = student_data['MATH_TOPICS'].unique()[0]
        science_learning_topic = student_data['SCIENCE_TOPICS'].unique()[0]
        english_learning_topic = student_data['ENGLISH_TOPICS'].unique()[0]
        thai_learning_topic = student_data['THAI_TOPICS'].unique()[0]
        
        with col1:
            st.metric("คะแนนเฉลี่ยรวม", f"{avg_overall:.1f}", help="คะแนนเฉลี่ยทุกวิชาในทุกสภาพแวดล้อมห้องเรียน")
        with col2:
            st.metric("คะแนนเฉลี่ย STEM", f"{avg_stem:.1f}", help="คะแนนเฉลี่ยวิชาคณิตศาสตร์และวิทยาศาสตร์")
        with col3:
            st.metric("คะแนนเฉลี่ยภาษา", f"{avg_language:.1f}", help="คะแนนเฉลี่ยวิชาภาษาอังกฤษและภาษาไทย")
        
        st.markdown("---")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write(f"ทดสอบเรื่อง {math_learning_topic}")
            st.metric("เวลาเรียน ", f"{math_learning_period:.1f} นาที", help="เวลาเรียนวิชาคณิตศาสตร์(นาที)")
        with col2:
            st.write(f"ทดสอบเรื่อง {science_learning_topic}")
            st.metric("เวลาเรียน ", f"{science_learning_period:.1f} นาที", help="เวลาเรียนวิทยาศาสตร์(นาที)")
        with col3:
            st.write(f"ทดสอบเรื่อง {english_learning_topic}")
            st.metric("เวลาเรียน ", f"{english_learning_period:.1f} นาที", help="เวลาเรียนภาษาอังกฤษ(นาที)")
        with col4:
            st.write(f"ทดสอบเรื่อง {thai_learning_topic}")
            st.metric("เวลาเรียน ", f"{thai_learning_period:.1f} นาที", help="เวลาเรียนภาษาไทย(นาที)")
        
        st.markdown("---")

        # Section 2: Classroom Analysis
        st.header("🧩 ผลการวิเคราะห์จุดแข็งและจุดอ่อน รวมถึงแนวทางการพัฒนา")
        
        # แสดงกราฟ
        st.markdown("""**การวิเคราะห์นี้แสดงให้เห็นว่า นักเรียนมีจุดแข็งและจุดอ่อนอย่างไร และเราจะพัฒนานักเรียนอย่างไร**
                    
                โดยพิื้นที่จะแบ่งออกเป็น 9 พื้นที่ ได้แก่:
                1. Warning Zone (พื้นที่เตือนภัย)
                    - สถานการณ์ปัจจุบัน: นักเรียนยังไม่เข้าใจพื้นฐาน ต้องได้รับการสนับสนุนจากโรงเรียนและผู้ปกครอง
                    - แผนพัฒนาขั้นต่อไป: ปรับหลักสูตรใหม่ให้เหมาะสม, ร่วมมือกับผู้ปกครองอย่างใกล้ชิด และจัดการเรียนแบบกลุ่มเล็กแยกออกมา
                    - เป้าหมายต่อไป: เพื่อให้นักเรียนเข้าออกจากพื้นนี้ไปเข้าสู่ พื้นที่พัฒนาการ (Development Zone)

                2. STEM Support (พื้นที่สนับสนุน)
                    - สถานการณ์ปัจจุบัน: นักเรียนมีพื้นฐานด้านภาษา แต่ต้องเสริมด้านวิทยาศาสตร์-คณิต
                    - แผนพัฒนาขั้นต่อไป: ให้คุณครูสาย STEM ดูแลอย่างใกล้ชิด, เพิ่มกิจกรรมการทดลองเข้ามาเพื่อทำให้เข้าใจง่าย และจัดการเรียนแบบกลุ่มเล็กแยกออกมา
                    - เป้าหมายต่อไป: เพื่อให้นักเรียนเข้าออกจากพื้นนี้ไปเข้าสู่ พื้นที่พัฒนาการ (Development Zone)

                3. Language Support (พื้นที่สนับสนุน)
                    - สถานการณ์ปัจจุบัน: นักเรียนมีพื้นฐานด้านคณิต-วิทย์ แต่ต้องเสริมด้านภาษา
                    - แผนพัฒนาขั้นต่อไป: ให้คุณครูสายภาษาดูแลอย่างใกล้ชิด, เพิ่มแบบฝึกหัดให้ทำอย่างสม่ำเสมอ และจัดการเรียนแบบกลุ่มเล็กแยกออกมา
                    - เป้าหมายต่อไป: เพื่อให้นักเรียนเข้าออกจากพื้นนี้ไปเข้าสู่ พื้นที่พัฒนาการ (Development Zone)

                4. Development Zone (พื้นที่พัฒนาการ)
                    - สถานการณ์ปัจจุบัน: นักเรียนมีพื้นฐานดีทุกวิชาแล้ว แต่ยังไม่มีจุดเด่นที่ชัดเจน
                    - แผนพัฒนาขั้นต่อไป: จัดกลุ่มการเรียนแบบผสมผสานให้เรียนกับเพื่อนที่เก่งหลายๆ แบบ และทดสอบนักเรียนภายใต้ทักษะหลายๆ อย่าง
                    - เป้าหมายต่อไป: เพื่อให้นักเรียนเข้าออกจากพื้นนี้ไปเข้าสู่ พื้นที่โดดเด่น(Strong Zone) หรือ พื้นที่สมสมบูรณ์แบบ(Perfect Zone)
                
                5. Language Expert (พื้นที่พัฒนาการ)
                    - สถานการณ์ปัจจุบัน: นักเรียนมีพื้นฐานภาษาดีมาก ต้องเสริมการคิดวิเคราะห์
                    - แผนพัฒนาขั้นต่อไป: จัดกลุ่มการเรียนให้เรียนกับเพื่อนที่เก่งด้านการวิเคราะห์และวิทยาศาสตร์ และทดสอบด้านการวิเคราะห์และแก้ปัญหาอย่างสม่ำเสมอ
                    - เป้าหมายต่อไป: เพื่อให้นักเรียนเข้าออกจากพื้นนี้ไปเข้าสู่ พื้นที่โดดเด่น(Strong Zone) หรือ พื้นที่สมสมบูรณ์แบบ(Perfect Zone)
                     
                6. STEM Expert (พื้นที่พัฒนาการ)
                    - สถานการณ์ปัจจุบัน: นักเรียนมีพื้นฐานด้านการวิเคราะห์และคณิตศาสตร์ดีมาก ต้องเสริมด้านภาษา
                    - แผนพัฒนาขั้นต่อไป: จัดกลุ่มการเรียนให้เรียนกับเพื่อนที่เก่งด้านภาษา และทดสอบด้านภาษาอย่างสม่ำเสมอ
                    - เป้าหมายต่อไป: เพื่อให้นักเรียนเข้าออกจากพื้นนี้ไปเข้าสู่ พื้นที่โดดเด่น(Strong Zone) หรือ พื้นที่สมสมบูรณ์แบบ(Perfect Zone)
                     
                7. STEM Strong (พื้นที่โดดเด่น) 
                    - สถานการณ์ปัจจุบัน: นักเรียนเชี่ยวชาญด้านการวิเคราะห์และวิทยาศาสตร์ และมีพื้นฐานภาษาที่ดีในเวลาเดียวกัน
                    - แผนพัฒนาขั้นต่อไป: จัดกลุ่มการเรียนให้เรียนกับเพื่อนที่เก่งด้านภาษา และพยายามประคับประคองให้รักษามาตรฐานต่อไป
                    - เป้าหมายต่อไป: เพื่อให้นักเรียนเข้าออกจากพื้นนี้ไปเข้าสู่ พื้นที่สมสมบูรณ์แบบ(Perfect Zone)

                8. Language Strong (พื้นที่โดดเด่น) 
                    - สถานการณ์ปัจจุบัน: นักเรียนเชี่ยวชาญด้านภาษา และมีพื้นฐานการวิเคราะห์และวิทยาศาสตร์ที่ดีในเวลาเดียวกัน
                    - แผนพัฒนาขั้นต่อไป: จัดกลุ่มการเรียนให้เรียนกับเพื่อนที่เก่งด้านการวิเคราะห์และวิทยาศาสตร์ และพยายามประคับประคองให้รักษามาตรฐานต่อไป
                    - เป้าหมายต่อไป: เพื่อให้นักเรียนเข้าออกจากพื้นนี้ไปเข้าสู่ พื้นที่สมสมบูรณ์แบบ(Perfect Zone)

                9. Perfect Zone (สมบูรณ์แบบ) 
                    - สถานการณ์ปัจจุบัน: นักเรียนมีความเชี่ยวชาญทั้งด้านการวิเคราะห์และด้านภาษา
                    - แผนพัฒนาขั้นต่อไป: พยายามประคับประคองให้รักษามาตรฐาน และจับตาดูอย่างใกล้ชิดถ้าหากน้องออกจากพื้นที่นี้ในอนาคต
                    - เป้าหมายต่อไป: เพิ่มเติมให้นักเรียนมีความสามารถด้านอื่นนอกจากด้านวิชาการ รวมถึงยกระดับด้านจิตใจให้อดทน ขยัน และมี winning mindset อยู่ตลอด""")
        
        fig = plot_classroom_cluster(student_data_in_class)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        
        # Section 3: Simulation Analysis
        st.header("🎯 การวิเคราะห์ศักยภาพเมื่ออยู่ในสภาพแวดล้อมที่แตกต่างกัน")
        st.markdown("""**การวิเคราะห์นี้แสดงให้เห็นว่า นักเรียนมีผลการเรียนเป็นอย่างไรในสภาพแวดล้อมห้องเรียนที่แตกต่างกัน เมื่อเปรียบเทียบกับนักเรียนจำลองทั้งหมด 100 คน**
                    
                โดยจะแสดงผลการเรียนใน 4 ประเภทห้องเรียน ได้แก่:
                1. STEM-Focused: ห้องเรียนที่พัฒนาด้านการคิดวิเคราะห์และแก้ปัญหาจากการทดลอง
                2. Language-Focused: ห้องเรียนที่พัฒนาด้านภาษาและการใช้เหตุผล
                3. Balanced Mixed: ห้องเรียนที่เน้นการบูรณาการความรู้จากหลายวิชา
                4. General: ห้องเรียนตามมาตรฐาน (มีนักเรียนเรียนเก่ง, เรียนปานกลาง และ เรียนพอใช้ ปนกันไป)""")
        
        subject_fig = create_subject_comparison(df, student_alias, selected_month)
        if subject_fig:
            st.plotly_chart(subject_fig, use_container_width=True)
        
        
        st.markdown("---")
        st.markdown("""**เพชร (♦️) แทนตำแหน่งของนักเรียน ถ้านักเรียนใกล้กับนักเรียนจำลองระดับไหน มีแนวโน้มว่านักเรียนคล้ายกับนักเรียนจำลองระดับนั้น**
                    
        ระดับของนักเรียนจำลองจะถูกแบ่งออกเป็น 5 ระดับ ได้แก่:
        - เพชรสีชมพู (Diamond): อัจฉริยะ ถ้าอยู่ใกล้ระดับนี้คาดว่า นักเรียนมีความสามารถเหมาะสมในห้องเรียนนี้
        - เพชรสีฟ้า (Platinum): นักเรียนเก่ง ถ้าอยู่ใกล้ระดับนี้คาดว่า นักเรียนสามารถเรียนในห้องเรียนนี้ได้และจะพัฒนาได้ดีในห้องเรียนนี้
        - เพชรสีทอง (Gold): นักเรียนดี ถ้าอยู่ใกล้ระดับนี้คาดว่า นักเรียนสามารถเรียนในห้องเรียนนี้ได้
        - เพชรสีเงิน (Silver): นักเรียนพอใช้ ถ้าอยู่ใกล้ระดับนี้คาดว่า นักเรียนสามารถเรียนในห้องเรียนนี้ได้ แต่ต้องพัฒนาตัวเองอย่างสม่ำเสมอ
        - เพชรสีน้ำตาล (Bronze): นักเรียนที่ต้องพัฒนา ถ้าอยู่ใกล้ระดับนี้คาดว่า นักเรียนต้องพัฒนาตัวเองให้มากกว่าเดิม""")


        scatter_fig = create_interactive_scatter_plot(df, student_alias)
        st.plotly_chart(scatter_fig, use_container_width=True)
        
        summary_df = create_summary_table(df, student_alias, selected_month)
        if summary_df is not None:
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True
            )

        # สรุปผล simulation
        summary_text = create_summarize_from_summary_table(summary_df)
        st.markdown(summary_text)
        
        st.markdown("---")
        
        # Section 4: Teacher's Assessment
        st.header("👨‍🏫 การประเมินจากครูผู้สอน")
        st.markdown("""**ผลประเมินจากคุณครูเป็นการวิเคราะห์มุมมองที่มาจากมนุษย์ ซึ่งจะแตกต่างจากมุมมองของระบบประดิษฐ์ (AI)**
                    
        ขอแตกต่างมุมมองคุณครูกับมุมมองของระบบประดิษฐ์ (AI) ที่ได้แสดงไปแล้วในส่วนก่อนหน้านี้:
        - มุมมองของคุณครูจะเป็นการประเมินจากการสอนจริงในห้องเรียน
        - มุมองของคุณครูจะเป็นการประเมินที่อาจจะมีความรู้สึกเข้ามาเกี่ยวข้อง
        """)
        
        teacher_data = student_data.iloc[0]  # เอาแค่ row แรก
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ จุดแข็ง")
            if pd.notna(teacher_data['GOOD_AT']):
                st.success(teacher_data['GOOD_AT'])
            else:
                st.write("ไม่มีข้อมูลการประเมินเฉพาะ")
        
        with col2:
            st.subheader("📈 ด้านที่ควรพัฒนา")
            if pd.notna(teacher_data['IMPROVE_ON']):
                st.warning(teacher_data['IMPROVE_ON'])
            else:
                st.write("ไม่มีข้อมูลการประเมินเฉพาะ")

        st.markdown("---")

    
    else:
        # แสดงหน้าต้อนรับเมื่อยังไม่ได้เลือกข้อมูล
        st.markdown("""
                
                ### ระบบการวิเคราะห์ที่ช่วยให้ผู้ปกครองเข้าใจ **ผลการเรียนของลูก** อย่างลึกซึ้ง ไม่ใช่ดูแค่คะแนนสอบ:
                    
                #### 1. 🎨 ภาพรวมผลการเรียน
                : จากคะแนนที่ได้ นักเรียนมีจุดแข็งหรือจุดอ่อนที่ตรงไหนและขั้นตอนต่อไปเราควรจะพัฒนาอย่างไร
                    
                #### 2. 🔮 โมเดลการคาดการณ์ศักยภาพ
                : จากคะแนนที่ได้ ระบบปัญญาประดิษฐ์(AI) จะจำลองสภาพแวดล้อมของห้องเรียนว่า นักเรียนจะพัฒนาได้ดีในห้องเรียนแบบไหน
                
                #### 3. 👩‍🏫 ความเห็นจากครูผู้สอน
                : จากคะแนนที่ได้ คุณครูผู้สอนมีความคิดเห็นอย่างไรเกี่ยวกับการเรียนของลูก
                
                ---
                
                #### 🔒 ความปลอดภัยของข้อมูล
                - ข้อมูลทั้งหมดเป็นความลับ เฉพาะผู้ปกครองที่ลงทะเบียนแล้วเท่านั้น
                - ชื่อของนักเรียนจะถูกเข้ารหัสเพื่อปกป้องความเป็นส่วนตัว
                - ไม่มีการแชร์ข้อมูลไปยังบุคคลภายนอก
                - ระบบการวิเคราะห์เป็นทรัพย์สินทางปัญญาของสถาบัน
                
                #### 🚀 เริ่มต้นใช้งาน
                กรุณาเลือกเมนูด้านซ้ายเพื่อเริ่มดูรายงานการประเมินของลูก
                
                ---
                *💡 หากมีข้อสงสัย กรุณาติดต่อ Bewdar Academy Lamphun*
                """)

if __name__ == "__main__":
    main()
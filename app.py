import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Set page config
st.set_page_config(
    page_title="Interview Analysis Dashboard",
    page_icon="📊",
    layout="wide"
)

# Load and process data
@st.cache_data
def load_data():
    with open('mongo_interview_analysis_grouped_10_5.json', 'r') as f:
        data = json.load(f)
    
    def safe_get(d, *keys):
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k, None)
            else:
                return None
        return d
    
    records = []
    for candidate in data:
        for video in candidate['videos']:
            analysis = video['analysis']
            record = {
                'firstName': candidate.get('firstName'),
                'lastName': candidate.get('lastName'),
                'email': candidate.get('email'),
                'question': video.get('question'),
                'fileName': video.get('fileName'),
                # Visual scores
                'attire_score': safe_get(analysis, 'visual', 'attire', 'score'),
                'background_score': safe_get(analysis, 'visual', 'background', 'score'),
                'video_quality_score': safe_get(analysis, 'visual', 'videoQuality', 'score'),
                'appearance_score': safe_get(analysis, 'visual', 'appearance', 'score'),
                'eye_contact_score': safe_get(analysis, 'visual', 'eyeContact', 'score'),
                # Audio scores
                'delivery_score': safe_get(analysis, 'audio', 'delivery', 'score'),
                'pronunciation_score': safe_get(analysis, 'audio', 'pronunciation', 'score'),
                'accent_score': safe_get(analysis, 'audio', 'accent', 'score'),
                # Content scores
                'irrelevant_responses_score': safe_get(analysis, 'content', 'irrelevantResponses', 'score'),
                'filler_words_score': safe_get(analysis, 'content', 'fillerWords', 'score'),
                'pauses_score': safe_get(analysis, 'content', 'pauses', 'score'),
                'grammar_score': safe_get(analysis, 'content', 'grammar', 'score'),
                'structure_score': safe_get(analysis, 'content', 'structure', 'score'),
                # Irregularities scores
                'language_score': safe_get(analysis, 'irregularities', 'language', 'score'),
                'video_irregularities_score': safe_get(analysis, 'irregularities', 'videoIrregularities', 'score'),
                'ai_cheating_score': safe_get(analysis, 'irregularities', 'aiCheating', 'score')
            }
            records.append(record)
    
    return pd.DataFrame(records)

# Load the data
df = load_data()

df['fullName'] = df['firstName'].fillna('') + ' ' + df['lastName'].fillna('')
candidate_names = ["All"] + sorted(df['fullName'].unique().tolist())

# Title and description
st.title("📊 Interview Analysis Dashboard")
st.markdown("""
This dashboard provides an analysis of video interview performances, including visual, audio, content, and irregularity metrics.
Use the filters on the sidebar to explore the data.
""")

# Sidebar filters
st.sidebar.header("Filters")

# Filter by candidate
selected_candidate = st.sidebar.selectbox(
    "Select Candidate",
    candidate_names
)

# Filter by question
selected_question = st.sidebar.selectbox(
    "Select Question",
    ["All"] + sorted(df['question'].unique().tolist())
)

# Apply filters
if selected_candidate != "All":
    df_filtered = df[df['fullName'] == selected_candidate]
else:
    df_filtered = df

if selected_question != "All":
    df_filtered = df_filtered[df_filtered['question'] == selected_question]

# Display candidate info if filtered
if selected_candidate != "All":
    st.header(f"Candidate: {selected_candidate}")
    if not df_filtered.empty:
        candidate_email = df_filtered['email'].iloc[0]
        st.subheader(f"Email: {candidate_email}")
    else:
        st.warning("No data found for this candidate and question selection.")

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📈 Overall Scores", "🔍 Detailed Analysis", "📋 Raw Data", "🎥 Video"])

with tab1:
    # Calculate average scores by category
    categories = {
        'Visual': ['attire_score', 'background_score', 'video_quality_score', 'appearance_score', 'eye_contact_score'],
        'Audio': ['delivery_score', 'pronunciation_score', 'accent_score'],
        'Content': ['irrelevant_responses_score', 'filler_words_score', 'pauses_score', 'grammar_score', 'structure_score'],
        'Irregularities': ['language_score', 'video_irregularities_score', 'ai_cheating_score']
    }
    
    # Create radar chart for average scores
    avg_scores = {}
    for category, metrics in categories.items():
        avg_scores[category] = df_filtered[metrics].mean().mean()
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(avg_scores.values()),
        theta=list(avg_scores.keys()),
        fill='toself',
        name='Average Score'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=False,
        title="Average Scores by Category"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display score distributions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Score Distributions")
        selected_category = st.selectbox("Select Category", list(categories.keys()))
        
        fig = px.box(df_filtered, y=categories[selected_category],
                    title=f"{selected_category} Scores Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Score Heatmap")
        fig = px.imshow(df_filtered[categories[selected_category]].corr(),
                       title=f"{selected_category} Scores Correlation",
                       color_continuous_scale='RdBu')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    # Detailed analysis by aspect
    st.header("Detailed Analysis by Aspect")
    
    aspect = st.selectbox(
        "Select Aspect to Analyze",
        ["Visual", "Audio", "Content", "Irregularities"]
    )
    
    metrics = categories[aspect]
    
    # Create detailed score breakdown
    fig = px.bar(df_filtered[metrics].mean().reset_index(),
                 x='index',
                 y=0,
                 title=f"Average {aspect} Scores by Metric",
                 labels={'index': 'Metric', 0: 'Score'})
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Show individual scores
    st.subheader("Individual Scores")
    st.dataframe(df_filtered[metrics].style.background_gradient(cmap='RdYlGn', vmin=0, vmax=10))

with tab3:
    # Raw data view
    st.header("Raw Data")
    st.dataframe(df_filtered)

with tab4:
    if selected_candidate != "All" and selected_question != "All":
        # Get the video file name for the selected candidate and question
        video_info = df_filtered[df_filtered['question'] == selected_question]
        if not video_info.empty:
            video_file_name = video_info['fileName'].iloc[0]
            
            # Try to find the video in both possible locations
            video_paths = [
                f"baker_mckenzie_video/{video_file_name}",
            ]
            
            video_found = False
            for video_path in video_paths:
                try:
                    st.video(video_path)
                    video_found = True
                    break
                except:
                    continue
            
            if not video_found:
                st.warning(f"Video file not found for {selected_candidate}'s response to: {selected_question}")
                st.info("Available video file name: " + video_file_name)
    else:
        st.info("Please select both a candidate and a question to view the video.")

# Add footer
st.markdown("---")
st.markdown("Dashboard created with Streamlit | Data from Interview Analysis") 
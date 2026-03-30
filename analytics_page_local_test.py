"""
Analytics Page for Avisia UTM Builder - LOCAL TEST VERSION
Uses local JSON files instead of Cloud Storage
"""

import streamlit as st
import json
from datetime import datetime
import pandas as pd
import os
from pathlib import Path

# Local test mode - read from local files
LOCAL_TEST_MODE = True
LOCAL_REPORTS_DIR = Path(__file__).parent / "mock_analytics_reports"

def list_available_reports():
    """List all available analytics reports from local directory"""
    try:
        if not LOCAL_REPORTS_DIR.exists():
            return []

        reports = []
        for file_path in LOCAL_REPORTS_DIR.glob("*.json"):
            # Extract date from filename
            parts = file_path.stem.replace('report_', '')
            reports.append({
                'file_path': str(file_path),
                'display_name': parts,
                'updated': datetime.fromtimestamp(file_path.stat().st_mtime)
            })

        # Sort by date (most recent first)
        reports.sort(key=lambda x: x['updated'], reverse=True)
        return reports

    except Exception as e:
        st.error(f"❌ Error listing reports: {str(e)}")
        return []

def load_report_from_storage(file_path):
    """Load a specific analytics report from local file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data

    except Exception as e:
        st.error(f"❌ Error loading report: {str(e)}")
        return None

def display_summary_metrics(data):
    """Display executive summary metrics in columns"""
    st.subheader("📊 Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Sessions",
            value=f"{data.get('total_sessions', 0):,}"
        )

    with col2:
        st.metric(
            label="Total Conversions",
            value=f"{data.get('total_conversions', 0):,}"
        )

    with col3:
        st.metric(
            label="Total Revenue",
            value=f"${data.get('total_revenue', 0):,.2f}"
        )

    with col4:
        # Calculate average engagement rate
        channels = data.get('channels', [])
        if channels:
            avg_engagement = sum(ch.get('engagement_rate', 0) for ch in channels) / len(channels)
            st.metric(
                label="Avg Engagement Rate",
                value=f"{avg_engagement:.2%}"
            )
        else:
            st.metric(label="Avg Engagement Rate", value="N/A")

def display_channel_focus(data, channel_type, title, color, icon):
    """Display focus section for Email or Social channel"""
    focus_data = data.get(f"{channel_type}_focus")

    if focus_data and focus_data.get('sessions', 0) > 0:
        st.markdown(f"### {icon} {title}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Sessions", f"{focus_data.get('sessions', 0):,}")
        with col2:
            st.metric("Conversions", f"{focus_data.get('conversions', 0):,}")
        with col3:
            st.metric("Revenue", f"${focus_data.get('revenue', 0):,.2f}")
        with col4:
            st.metric("Engagement Rate", f"{focus_data.get('engagement_rate', 0):.2%}")

def display_channels_table(data):
    """Display all channels data in a table"""
    st.subheader("📈 All Acquisition Channels")

    channels = data.get('channels', [])

    if not channels:
        st.info("ℹ️ No channel data available")
        return

    # Convert to DataFrame
    df = pd.DataFrame(channels)

    # Format numeric columns
    if 'sessions' in df.columns:
        df['sessions'] = df['sessions'].apply(lambda x: f"{x:,}")
    if 'conversions' in df.columns:
        df['conversions'] = df['conversions'].apply(lambda x: f"{x:,}")
    if 'revenue' in df.columns:
        df['revenue'] = df['revenue'].apply(lambda x: f"${x:,.2f}")
    if 'engagement_rate' in df.columns:
        df['engagement_rate'] = df['engagement_rate'].apply(lambda x: f"{x:.2%}")
    if 'avg_session_duration' in df.columns:
        df['avg_session_duration'] = df['avg_session_duration'].apply(lambda x: f"{x:.2f}s")

    # Rename columns for display
    df.columns = df.columns.str.replace('_', ' ').str.title()

    # Display table
    st.dataframe(df, use_container_width=True, hide_index=True)

def display_ai_insights(data):
    """Display AI-generated insights"""
    insights = data.get('ai_insights')

    if insights:
        st.subheader("🧠 AI-Generated Insights")
        st.markdown(f"""
        <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; border-left: 4px solid #ff9800;">
        {insights}
        </div>
        """, unsafe_allow_html=True)

def analytics_page():
    """Main analytics page function - LOCAL TEST VERSION"""

    st.title("📊 GA4 Weekly Analytics Reports")

    if LOCAL_TEST_MODE:
        st.info("🧪 **LOCAL TEST MODE** - Reading from mock_analytics_reports directory")

    st.markdown("""
    View your weekly Google Analytics 4 reports with insights on acquisition channels,
    email performance, and social media metrics.
    """)

    # List available reports
    reports = list_available_reports()

    if not reports:
        st.warning(f"""
        ⚠️ **No analytics reports found in {LOCAL_REPORTS_DIR}**

        Run this command to create mock data:
        ```
        python test_streamlit_analytics.py
        ```
        """)
        return

    # Report selector
    st.markdown("---")
    st.subheader("📅 Select Report Period")

    report_options = {report['display_name']: report['file_path'] for report in reports}

    selected_display = st.selectbox(
        "Choose a report:",
        options=list(report_options.keys()),
        format_func=lambda x: f"Week: {x}"
    )

    selected_file = report_options[selected_display]

    # Load and display selected report
    with st.spinner("Loading report..."):
        data = load_report_from_storage(selected_file)

    if not data:
        st.error("❌ Failed to load report data")
        return

    # Display report metadata
    st.markdown(f"""
    **Report Period:** {data.get('week_start', 'N/A')} to {data.get('week_end', 'N/A')}
    **Generated:** {data.get('generated_at', 'N/A')}
    **Property ID:** {data.get('property_id', 'N/A')}
    """)

    st.markdown("---")

    # Display metrics
    display_summary_metrics(data)

    st.markdown("---")

    # Email Channel Focus
    display_channel_focus(data, 'email', 'Email Channel Focus', '#1976d2', '📧')

    st.markdown("---")

    # Social Media Focus
    display_channel_focus(data, 'social', 'Social Media Focus', '#c2185b', '📱')

    st.markdown("---")

    # All Channels Table
    display_channels_table(data)

    st.markdown("---")

    # AI Insights
    display_ai_insights(data)

    # Download option
    st.markdown("---")
    st.subheader("💾 Export Data")

    # Prepare JSON for download
    json_str = json.dumps(data, indent=2)
    st.download_button(
        label="📥 Download Report (JSON)",
        data=json_str,
        file_name=f"analytics_report_{selected_display}.json",
        mime="application/json",
        use_container_width=True
    )

    # Footer
    st.markdown("---")
    st.caption(f"🧪 LOCAL TEST MODE | Mock data | Last updated: {reports[0]['updated'].strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # Direct test
    st.set_page_config(page_title="Analytics Test", layout="wide")
    analytics_page()

"""
Analytics Page for Avisia UTM Builder
Displays GA4 weekly analytics reports from Cloud Storage
"""

import streamlit as st
from google.cloud import storage
import json
from datetime import datetime
import pandas as pd
import os

# Cloud Storage configuration
BUCKET_NAME = "avisia-utm-builder"
ANALYTICS_FOLDER = "analytics_reports"
GCP_PROJECT_ID = os.getenv('GCP_PROJECT', 'avisia-training')

def get_storage_client():
    """Initialize Cloud Storage client"""
    try:
        return storage.Client(project=GCP_PROJECT_ID)
    except Exception as e:
        st.error(f"❌ Error connecting to Cloud Storage: {str(e)}")
        return None

def list_available_reports():
    """List all available analytics reports from Cloud Storage"""
    try:
        client = get_storage_client()
        if not client:
            return []

        bucket = client.bucket(BUCKET_NAME)
        blobs = bucket.list_blobs(prefix=f"{ANALYTICS_FOLDER}/")

        reports = []
        for blob in blobs:
            if blob.name.endswith('.json'):
                # Extract date from filename like: analytics_reports/report_2025-11-04_to_2025-11-10.json
                parts = blob.name.split('/')[-1].replace('report_', '').replace('.json', '')
                reports.append({
                    'blob_name': blob.name,
                    'display_name': parts,
                    'updated': blob.updated
                })

        # Sort by date (most recent first)
        reports.sort(key=lambda x: x['updated'], reverse=True)
        return reports

    except Exception as e:
        st.error(f"❌ Error listing reports: {str(e)}")
        return []

def load_report_from_storage(blob_name):
    """Load a specific analytics report from Cloud Storage"""
    try:
        client = get_storage_client()
        if not client:
            return None

        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)

        if not blob.exists():
            st.warning(f"⚠️ Report not found: {blob_name}")
            return None

        # Download and parse JSON
        content = blob.download_as_text()
        data = json.loads(content)
        return data

    except Exception as e:
        st.error(f"❌ Error loading report: {str(e)}")
        return None

def calculate_evolution(current_value, previous_value):
    """Calculate percentage evolution between two values"""
    if previous_value == 0 or previous_value is None:
        return None
    return ((current_value - previous_value) / previous_value) * 100

def display_summary_metrics(data, previous_data=None):
    """Display executive summary metrics in columns with evolution rates"""
    st.subheader("📊 Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        current_sessions = data.get('total_sessions', 0)
        delta = None
        if previous_data:
            prev_sessions = previous_data.get('total_sessions', 0)
            evolution = calculate_evolution(current_sessions, prev_sessions)
            delta = f"{evolution:+.0f}%" if evolution is not None else None

        st.metric(
            label="Total Sessions",
            value=f"{current_sessions:,}",
            delta=delta
        )

    with col2:
        current_conversions = data.get('total_conversions', 0)
        delta = None
        if previous_data:
            prev_conversions = previous_data.get('total_conversions', 0)
            evolution = calculate_evolution(current_conversions, prev_conversions)
            delta = f"{evolution:+.0f}%" if evolution is not None else None

        st.metric(
            label="Total Conversions",
            value=f"{current_conversions:,}",
            delta=delta
        )

    with col3:
        current_revenue = data.get('total_revenue', 0)
        delta = None
        if previous_data:
            prev_revenue = previous_data.get('total_revenue', 0)
            evolution = calculate_evolution(current_revenue, prev_revenue)
            delta = f"{evolution:+.0f}%" if evolution is not None else None

        st.metric(
            label="Total Revenue",
            value=f"${current_revenue:,.2f}",
            delta=delta
        )

    with col4:
        # Calculate average engagement rate
        channels = data.get('channels', [])
        if channels:
            avg_engagement = sum(ch.get('engagement_rate', 0) for ch in channels) / len(channels)
            delta = None
            if previous_data:
                prev_channels = previous_data.get('channels', [])
                if prev_channels:
                    prev_avg_engagement = sum(ch.get('engagement_rate', 0) for ch in prev_channels) / len(prev_channels)
                    evolution = calculate_evolution(avg_engagement, prev_avg_engagement)
                    delta = f"{evolution:+.0f}%" if evolution is not None else None

            st.metric(
                label="Avg Engagement Rate",
                value=f"{avg_engagement:.2%}",
                delta=delta
            )
        else:
            st.metric(label="Avg Engagement Rate", value="N/A")

def display_channel_focus(data, channel_type, title, color, icon, previous_data=None):
    """Display focus section for Email or Social channel with evolution rates"""
    focus_data = data.get(f"{channel_type}_focus")

    if focus_data and focus_data.get('sessions', 0) > 0:
        st.markdown(f"### {icon} {title}")

        col1, col2, col3, col4 = st.columns(4)

        # Get previous data if available
        prev_focus = None
        if previous_data:
            prev_focus = previous_data.get(f"{channel_type}_focus")

        with col1:
            current_sessions = focus_data.get('sessions', 0)
            delta = None
            if prev_focus:
                prev_sessions = prev_focus.get('sessions', 0)
                evolution = calculate_evolution(current_sessions, prev_sessions)
                delta = f"{evolution:+.0f}%" if evolution is not None else None
            st.metric("Sessions", f"{current_sessions:,}", delta=delta)

        with col2:
            current_conversions = focus_data.get('conversions', 0)
            delta = None
            if prev_focus:
                prev_conversions = prev_focus.get('conversions', 0)
                evolution = calculate_evolution(current_conversions, prev_conversions)
                delta = f"{evolution:+.0f}%" if evolution is not None else None
            st.metric("Conversions", f"{current_conversions:,}", delta=delta)

        with col3:
            current_revenue = focus_data.get('revenue', 0)
            delta = None
            if prev_focus:
                prev_revenue = prev_focus.get('revenue', 0)
                evolution = calculate_evolution(current_revenue, prev_revenue)
                delta = f"{evolution:+.0f}%" if evolution is not None else None
            st.metric("Revenue", f"${current_revenue:,.2f}", delta=delta)

        with col4:
            current_engagement = focus_data.get('engagement_rate', 0)
            delta = None
            if prev_focus:
                prev_engagement = prev_focus.get('engagement_rate', 0)
                evolution = calculate_evolution(current_engagement, prev_engagement)
                delta = f"{evolution:+.0f}%" if evolution is not None else None
            st.metric("Engagement Rate", f"{current_engagement:.2%}", delta=delta)

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
    """Main analytics page function"""

    st.title("📊 GA4 Weekly Analytics Reports")

    st.markdown("""
    View your weekly Google Analytics 4 reports with insights on acquisition channels,
    email performance, and social media metrics.
    """)

    # List available reports
    reports = list_available_reports()

    if not reports:
        st.info("""
        ℹ️ **No analytics reports available yet.**

        Reports are automatically generated every Monday at 7 AM and will appear here.

        You can also trigger a manual report by running the analytics agent.
        """)
        return

    # Report selector
    st.markdown("---")
    st.subheader("📅 Select Report Period")

    report_options = {report['display_name']: report['blob_name'] for report in reports}

    selected_display = st.selectbox(
        "Choose a report:",
        options=list(report_options.keys()),
        format_func=lambda x: f"Week: {x}"
    )

    selected_blob = report_options[selected_display]

    # Load and display selected report
    with st.spinner("Loading report..."):
        data = load_report_from_storage(selected_blob)

    if not data:
        st.error("❌ Failed to load report data")
        return

    # Load previous report for comparison
    previous_data = None
    current_index = list(report_options.keys()).index(selected_display)
    if current_index < len(report_options) - 1:  # If there's a previous report
        previous_display = list(report_options.keys())[current_index + 1]
        previous_blob = report_options[previous_display]
        with st.spinner("Loading previous week for comparison..."):
            previous_data = load_report_from_storage(previous_blob)

    # Display report metadata
    comparison_text = ""
    if previous_data:
        comparison_text = f" | Compared to: {previous_data.get('week_start', 'N/A')} to {previous_data.get('week_end', 'N/A')}"

    st.markdown(f"""
    **Report Period:** {data.get('week_start', 'N/A')} to {data.get('week_end', 'N/A')}{comparison_text}
    **Generated:** {data.get('generated_at', 'N/A')}
    **Property ID:** {data.get('property_id', 'N/A')}
    """)

    st.markdown("---")

    # Display metrics with evolution rates
    display_summary_metrics(data, previous_data)

    st.markdown("---")

    # Email Channel Focus
    display_channel_focus(data, 'email', 'Email Channel Focus', '#1976d2', '📧', previous_data)

    st.markdown("---")

    # Social Media Focus
    display_channel_focus(data, 'social', 'Social Media Focus', '#c2185b', '📱', previous_data)

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
    st.caption(f"🤖 Automated analytics powered by GA4 MCP Server | Last updated: {reports[0]['updated'].strftime('%Y-%m-%d %H:%M:%S')}")

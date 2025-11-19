"""
Test script for Analytics Page in Streamlit App
Creates mock Cloud Storage data for local testing
"""

import json
import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Mock analytics data
mock_data = {
    "property_id": "255756835",
    "week_start": "2025-10-27",
    "week_end": "2025-11-02",
    "generated_at": "2025-11-06T12:15:11.622253",
    "total_sessions": 46590,
    "total_conversions": 2778,
    "total_revenue": 144902.0,
    "channels": [
        {
            "channel": "Organic Search",
            "sessions": 15420,
            "conversions": 892,
            "revenue": 45230.5,
            "engagement_rate": 0.058,
            "avg_session_duration": 320.0
        },
        {
            "channel": "Direct",
            "sessions": 8760,
            "conversions": 523,
            "revenue": 28460.0,
            "engagement_rate": 0.060,
            "avg_session_duration": 240.0
        },
        {
            "channel": "Paid Search",
            "sessions": 6540,
            "conversions": 412,
            "revenue": 22340.5,
            "engagement_rate": 0.063,
            "avg_session_duration": 290.0
        },
        {
            "channel": "Social",
            "sessions": 4120,
            "conversions": 156,
            "revenue": 8920.25,
            "engagement_rate": 0.038,
            "avg_session_duration": 240.0
        },
        {
            "channel": "Email",
            "sessions": 3250,
            "conversions": 245,
            "revenue": 12450.75,
            "engagement_rate": 0.075,
            "avg_session_duration": 230.0
        }
    ],
    "email_focus": {
        "channel": "Email",
        "sessions": 3250,
        "conversions": 245,
        "revenue": 12450.75,
        "engagement_rate": 0.075,
        "avg_session_duration": 230.0
    },
    "social_focus": {
        "channel": "Social",
        "sessions": 4120,
        "conversions": 156,
        "revenue": 8920.25,
        "engagement_rate": 0.038,
        "avg_session_duration": 240.0
    },
    "ai_insights": """
**Key Performance Highlights:**
- Strong organic search performance with 15.4K sessions
- Email campaigns showing solid 7.5% conversion rate
- Social media engagement improving week-over-week

**Email Channel Performance:**
The email channel delivered 3,250 sessions with 245 conversions, representing a healthy conversion rate of 7.5%. Revenue from email campaigns reached $12,450.75. The engagement rate suggests recipients are highly qualified leads.

**Social Media Channel Performance:**
Social media traffic generated 4,120 sessions with 156 conversions. While the volume is good, the conversion rate of 3.8% indicates opportunity for better targeting or landing page optimization. Revenue of $8,920.25 shows room for growth.

**3 Actionable Recommendations:**

1. **Scale Email Campaigns**: Given the strong 7.5% conversion rate, consider increasing email campaign frequency and list size. The ROI appears very positive.

2. **Optimize Social Media Funnels**: Social traffic is strong but conversions lag. Review landing pages and ensure they're mobile-optimized. Consider retargeting campaigns for social visitors.

3. **Leverage Organic Success**: With organic search performing well, invest in SEO content that targets converting keywords. Expand on topics that are already driving qualified traffic.
"""
}

# Create mock analytics reports directory
mock_dir = Path("mock_analytics_reports")
mock_dir.mkdir(exist_ok=True)

# Save mock data
mock_file = mock_dir / "report_2025-10-27_to_2025-11-02.json"
with open(mock_file, 'w', encoding='utf-8') as f:
    json.dump(mock_data, f, indent=2)

print("✅ Mock analytics data created!")
print(f"   Location: {mock_file.absolute()}")
print()
print("📝 To test the Streamlit app with mock data:")
print()
print("1. Modify analytics_page.py to use local mock data:")
print("   Replace: BUCKET_NAME = 'avisia-utm-builder'")
print("   With: BUCKET_NAME = 'mock' # or add LOCAL_TEST flag")
print()
print("2. Or run Streamlit with Cloud Storage credentials:")
print("   streamlit run app.py")
print()
print("💡 Mock data has been created for testing purposes.")

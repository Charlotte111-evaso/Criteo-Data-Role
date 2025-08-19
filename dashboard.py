import pandas as pd
import streamlit as st
import plotly.express as px

# Load datasets
users = pd.read_csv("data/users.csv")
exposures = pd.read_csv("data/ad_exposures.csv")
engagement = pd.read_csv("data/engagement.csv")
conversions = pd.read_csv("data/conversion_events.csv")

# Add engagement score
engagement["engagement_score"] = (
    0.4 * engagement["dwell_time"] +
    0.4 * engagement["pageviews"] +
    0.2 * engagement["clicked"]
)

# Sidebar filters
st.sidebar.title("🔍 Filters")
selected_region = st.sidebar.selectbox("Region", ["All"] + users["region"].unique().tolist())
selected_device = st.sidebar.selectbox("Device Type", ["All"] + users["device_type"].unique().tolist())

# Filter user data
filtered_users = users.copy()
if selected_region != "All":
    filtered_users = filtered_users[filtered_users["region"] == selected_region]
if selected_device != "All":
    filtered_users = filtered_users[filtered_users["device_type"] == selected_device]

# Filter other datasets
filtered_engagement = engagement[engagement["user_id"].isin(filtered_users["user_id"])]
filtered_exposures = exposures[exposures["user_id"].isin(filtered_users["user_id"])]
filtered_conversions = conversions[conversions["user_id"].isin(filtered_users["user_id"])]

# KPI calculations
filtered_ctr = filtered_engagement["clicked"].mean()
filtered_dwell = filtered_engagement["dwell_time"].mean()
filtered_conversion_rate = filtered_engagement["user_id"].isin(filtered_conversions["user_id"]).mean()

# Tabs layout
tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Exposure Analysis", "🧠 Engagement Analysis"])

# ----------- TAB 1: OVERVIEW ----------
with tab1:
    st.title("📈 Upper-Funnel Marketing Dashboard (Criteo-style)")
    st.markdown("Prototype dashboard to monitor performance of ad exposures and engagement.")

    # KPI Cards
    col1, col2, col3 = st.columns(3)
    col1.metric("CTR", f"{filtered_ctr:.2%}")
    col2.metric("Avg Dwell Time", f"{filtered_dwell:.2f} sec")
    col3.metric("Conversion Rate", f"{filtered_conversion_rate:.2%}")

    # Engagement score distribution
    st.subheader("Engagement Score Distribution")
    fig1 = px.histogram(filtered_engagement, x="engagement_score", nbins=40)
    st.plotly_chart(fig1, use_container_width=True, key="fig1")

    # New: Engagement by Device Type
    st.subheader("Engagement Score by Device Type")
    merged_device = filtered_engagement.merge(users[["user_id", "device_type"]], on="user_id", how="left")
    score_by_device = (
        merged_device
        .groupby("device_type")["engagement_score"]
        .mean()
        .reset_index()
        .sort_values(by="engagement_score", ascending=False)
    )
    fig2 = px.bar(score_by_device, x="device_type", y="engagement_score", title="Avg Engagement Score by Device")
    st.plotly_chart(fig2, use_container_width=True, key="fig2")

# ----------- TAB 2: EXPOSURE ANALYSIS ----------
with tab2:
    st.subheader("📊 Conversion Rate by Exposure Frequency")

    exposure_freq = exposures.groupby("user_id")["exposure_count"].sum().reset_index(name="total_exposures")
    exposure_vs_conversion = exposure_freq.merge(conversions[["user_id"]], on="user_id", how="left")
    exposure_vs_conversion["converted"] = exposure_vs_conversion["user_id"].isin(conversions["user_id"])

    bins = [0, 2, 5, 10, 20, 50, 100]
    labels = ["1–2", "3–5", "6–10", "11–20", "21–50", "50+"]
    exposure_vs_conversion["exposure_bin"] = pd.cut(exposure_vs_conversion["total_exposures"], bins=bins, labels=labels)

    conversion_by_exposure = exposure_vs_conversion.groupby("exposure_bin")["converted"].mean().reset_index()
    conversion_by_exposure["exposure_bin"] = conversion_by_exposure["exposure_bin"].astype(str)

    fig3 = px.bar(conversion_by_exposure, x="exposure_bin", y="converted", labels={"converted": "Conversion Rate"})
    st.plotly_chart(fig3, use_container_width=True, key="fig3")

# ----------- TAB 3: ENGAGEMENT ANALYSIS ----------
# ----------- TAB 3: ENGAGEMENT ANALYSIS ----------
with tab3:
    st.subheader("📈 Conversion Rate by Engagement Level")

    # Merge engagement + conversion
    engagement_vs_conversion = engagement.merge(
        conversions[["user_id"]], on="user_id", how="left"
    )
    engagement_vs_conversion["converted"] = engagement_vs_conversion["user_id"].isin(
        conversions["user_id"]
    )

    # Bin engagement scores into Low, Medium, High
    engagement_vs_conversion["engagement_level"] = pd.cut(
        engagement_vs_conversion["engagement_score"],
        bins=[-float("inf"), 20, 50, float("inf")],
        labels=["Low", "Medium", "High"]
    )

    # Group and calculate
    conversion_by_engagement = (
        engagement_vs_conversion.groupby("engagement_level")
        .agg(
            conversion_rate=("converted", "mean"),
            user_count=("user_id", "count")
        )
        .reset_index()
    )

    # Plot
    fig4 = px.bar(
        conversion_by_engagement,
        x="engagement_level",
        y="conversion_rate",
        text=conversion_by_engagement["conversion_rate"].apply(lambda x: f"{x:.2%}"),
        labels={"conversion_rate": "Conversion Rate", "engagement_level": "Engagement Level"},
        title="Conversion Rate Increases With Engagement Level"
    )
    fig4.update_traces(marker_color='steelblue', textposition='outside')
    fig4.update_layout(yaxis_tickformat=".0%", xaxis_title="Engagement Level", yaxis_title="Conversion Rate")

    st.plotly_chart(fig4, use_container_width=True, key="fig4")

    st.markdown("""
    - **Low** engagement: Users who barely interacted (low dwell time/pageviews).
    - **Medium** engagement: Average users.
    - **High** engagement: Long sessions, more pageviews, higher interaction.

    📌 *As engagement increases, users are more likely to convert.*
    """)
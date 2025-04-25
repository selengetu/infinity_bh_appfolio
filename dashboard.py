import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS

st.set_page_config(page_title="Infinity BH Dashboards", layout="wide")

def show_dashboard():
    
    BASE_DIR = os.path.join(os.getcwd(), "data")  # Use relative path
    IMG_DIR = "plotly_pdf_images"
    st.title("📊 Infinity BH Dashboards")
    # Define file prefixes
    file_prefixes = {
        "Tenant Data": "tenant_data_cleaned",
        "Work Orders": "work_order_cleaned",
        "Prospect": "prospect_cleaned",
        "Rent Roll": "rentroll_cleaned",
        "Leasing": "leasing_cleaned",
        "Purchase Order": "purchase_order_cleaned",
        "Bill": "bill_cleaned",
        "Rent Roll 12 Months": "rentroll_12_months_combined",
    }

    # Initialize a dictionary to store the latest file for each category
    latest_files = {}

    # List all files in the BASE_DIR
    files_in_directory = os.listdir(BASE_DIR)

    # Function to extract date from the filename
    def extract_timestamp_from_filename(filename):
        """
        Extracts datetime object from filenames like 'tenant_data_cleaned_20250321_115751.csv'
        """
        try:
            # Extract the last two underscore-separated parts before .csv
            parts = filename.rsplit("_", 2)  # ['tenant_data_cleaned', '20250321', '115751.csv']
            if len(parts) < 3:
                raise ValueError("Invalid filename format")
            
            date_str, time_str = parts[-2], parts[-1].split(".")[0]  # Get YYYYMMDD and HHMMSS

            # Convert to datetime object
            return datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
        except ValueError as e:
            print(f"Error parsing date from {filename}: {e}")
            return datetime.min  # Return a minimal datetime to avoid crashing

    # Iterate through each category and find the latest file
    for category, prefix in file_prefixes.items():
        # Filter files based on the prefix
        relevant_files = [f for f in files_in_directory if f.startswith(prefix) and f.endswith(".csv")]
        
        if relevant_files:
            # Sort the files by timestamp extracted from their filenames in descending order (latest first)
            latest_file = max(relevant_files, key=extract_timestamp_from_filename)
            latest_files[category] = os.path.join(BASE_DIR, latest_file)

    # Print the latest files for each category
    for category, file_path in latest_files.items():
        print(f"Latest {category}: {file_path}")

    # Store latest files in a dictionary
    FILES = {
        "Tenant Data": latest_files.get("Tenant Data"),
        "Work Orders": latest_files.get("Work Orders"),
        "Prospect": latest_files.get("Prospect"),
        "Leasing": latest_files.get("Leasing"),
        "Rent Roll": latest_files.get("Rent Roll"),
        "Purchase Order": latest_files.get("Purchase Order"),
        "Bill": latest_files.get("Bill"),
        "Rent Roll 12 Months": latest_files.get("Rent Roll 12 Months")
    }
    # 🔹 2. Load DataFrames
    dfs = {}
    for name, path in FILES.items():
        if os.path.exists(path):  # Check if file exists
            dfs[name] = pd.read_csv(path)
        else:
            st.warning(f"⚠️ File not found: {path}")
    # Create folder for images
    IMG_DIR = "plotly_images"
    os.makedirs(IMG_DIR, exist_ok=True)

    # 🔹 Generate and Save Plotly Charts as Images
    image_paths = []
    # 🔹 3. Display DataFrames in Tabs
    if dfs:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🏠 Property Performance", 
            "💰 Rent", 
            "📝 Leasing", 
            "🔧 Maintenance", 
            "🏢 Tenants", 
            "📄 Billings"
        ])

    with tab1:
         # Get unique filter values
        properties = dfs["Rent Roll"]["Property Name"].dropna().unique().tolist()
        statuses = dfs["Rent Roll"]["Status"].dropna().unique().tolist()

        col_prop = st.columns(3)[0]

        with col_prop:
            selected_property = st.selectbox("Filter by Property", ["All"] + properties)

       # Filter data
        rent_roll = dfs["Rent Roll"].copy()
        rent_roll1 = dfs["Rent Roll"].copy()
        trailing_12months = dfs["Rent Roll 12 Months"].copy()  
        tenant_data = dfs["Tenant Data"].copy()

        if selected_property != "All":
            rent_roll = rent_roll[rent_roll["Property Name"] == selected_property]
            rent_roll1 = rent_roll1[rent_roll1["Property Name"] == selected_property]
            trailing_12months = trailing_12months[trailing_12months["Property Name"] == selected_property]
            tenant_data = tenant_data[tenant_data["Property Name"] == selected_property]

        # Metric calculations using filtered data
        col1, col2, col3, col4 = st.columns(4)

        all_units = rent_roll.shape[0]
        current_resident = rent_roll[rent_roll["Status"] == "Current"].shape[0]
        notice = rent_roll[rent_roll["Status"] == "Notice-Unrented"].shape[0]
        notice_re = rent_roll[rent_roll["Status"] == "Notice-Rented"].shape[0]
        evict = rent_roll[rent_roll["Status"] == "Evict"].shape[0]
        occupied = ((current_resident + evict + notice + notice_re) / all_units) * 100 if all_units > 0 else 0

        # Convert rent columns
        rent_roll["Rent"] = rent_roll["Rent"].replace("[\$,]", "", regex=True)
        rent_roll["Rent"] = pd.to_numeric(rent_roll["Rent"], errors="coerce")
        total_rent = rent_roll["Rent"].sum()

        total_move_out = rent_roll["Move-out"].notnull().sum()

        # Display metrics
        col1.metric(label="🏠 Total Units", value=f"{all_units}")
        col2.metric(label="📊 Occupancy Rate", value=f"{occupied:.2f}%")
        col3.metric(label="💵 Total Rent", value=f"${total_rent:,.0f}")
        col4.metric(label="🚪 Total Move-outs (Next 60 days)", value=f"{total_move_out}")

        col5, col6 = st.columns(2)
        
        with col5:
            
            trailing_12months['date_str'] = pd.to_datetime(trailing_12months['date_str'], format='%m-%d-%Y')
            trailing_12months = trailing_12months.sort_values(by='date_str')
            summary = []
            for date, group in trailing_12months.groupby('date_str'):
                total = len(group)
                current = group[group['Status'] == 'Current'].shape[0]
                notice = group[group['Status'] == 'Notice-Rented'].shape[0]
                evict = group[group['Status'] == 'Evict'].shape[0]
                notice_un = group[group['Status'] == 'Notice-Unrented'].shape[0]
                occupied = current +evict+ notice_un+notice
                occupancy_rate = round((occupied / total) * 100, 2) if total > 0 else 0

                summary.append({
                    "Month": date.strftime("%b %Y"),
                    "Occupancy %": occupancy_rate,
                    "Total Units": total
                })

            df_occ = pd.DataFrame(summary)

            fig = go.Figure()
            # Line chart for Occupancy %
            fig.add_trace(
                go.Scatter(
                    x=df_occ["Month"],
                    y=df_occ["Occupancy %"],
                    mode="lines+markers",
                    name="Occupancy %",
                    line=dict(color="green"),
                    marker=dict(size=8),
                    text=df_occ["Occupancy %"],
                    textposition="top center"
                )
            )

            # Layout
            fig.update_layout(
                title="📊 Monthly Occupancy % and Total Units",
                xaxis=dict(title="Month", title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title="Occupancy %", title_font=dict(size=14), tickfont=dict(size=12), gridcolor="lightgray"),
                yaxis2=dict(
                    title="Total Units",
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    title_font=dict(size=14),
                    tickfont=dict(size=12),
                ),
                legend=dict(title="Metrics", font=dict(size=12)),
                width=1000, height=600,
                margin=dict(l=50, r=50, t=50, b=50)
            )

            st.plotly_chart(fig, use_container_width=True)
        
        with col6:
            
            trailing_12months['date_str'] = pd.to_datetime(trailing_12months['date_str'], format='%m-%d-%Y')
            trailing_12months = trailing_12months.sort_values(by='date_str')
            summary = []
            for date, group in trailing_12months.groupby('date_str'):
                total = len(group)
                vacant_rented = group[group['Status'] == 'Vacant-Rented'].shape[0]
                vacant_unrented = group[group['Status'] == 'Vacant-Unrented'].shape[0]

                summary.append({
                    "Month": date.strftime("%b %Y"),
                    "Vacant-Rented": vacant_rented,
                    "Vacant-Unrented": vacant_unrented,
                    "Total Units": total
                })

            df_occ = pd.DataFrame(summary)

            fig = go.Figure()

            # Bar: Vacant-Rented
            fig.add_trace(
                go.Bar(
                    x=df_occ["Month"],
                    y=df_occ["Vacant-Rented"],
                    name="Vacant-Rented",
                    marker=dict(color="lightblue")
                )
            )

            # Bar: Vacant-Unrented (stacked on top)
            fig.add_trace(
                go.Bar(
                    x=df_occ["Month"],
                    y=df_occ["Vacant-Unrented"],
                    name="Vacant-Unrented",
                    marker=dict(color="steelblue")
                )
            )

            # Layout
            fig.update_layout(
                barmode='stack',
                title="📊 Monthly Breakdown: Vacant-Rented vs Vacant-Unrented",
                xaxis=dict(title="Month", title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title="Unit Count", title_font=dict(size=14), tickfont=dict(size=12), gridcolor="lightgray"),
                legend=dict(title="Vacancy Type", font=dict(size=12)),
                width=1000, height=600,
                margin=dict(l=50, r=50, t=50, b=50)
            )

            st.plotly_chart(fig, use_container_width=True)
            
        col7, col8 = st.columns(2)

        # Use col2 and col5 for two separate charts
        with col7:

            statuses = [
            "Current",
            "Notice-Rented",
            "Notice-Unrented",
            "Evict",
            "Vacant-Rented",
            "Vacant-Unrented"
            ]

            # Filter only relevant statuses
            filtered = rent_roll[rent_roll["Status"].isin(statuses)]

            # Group by Unit Type and Status
            grouped = (
                filtered
                .groupby(["BD/BA", "Status"])
                .size()
                .reset_index(name="Count")
            )

            color_map = {
                "Current": "lightgrey",
                "Vacant-Unrented": "steelblue",
                "Vacant-Rented": "lightblue",
                "Evict": "red",
                "Notice-Unrented": "mediumseagreen",
                "Notice-Rented": "orange"
            }
            pivot_df = grouped.pivot_table(
                index="BD/BA",
                columns="Status",
                values="Count",
                fill_value=0
            ).reset_index()

            fig = px.bar(
                grouped,
                x="BD/BA",
                y="Count",
                color="Status",
                barmode="stack",
                color_discrete_map=color_map,
                title="📊 Unit Type Breakdown by Status"
            )

            fig.update_layout(
                xaxis_title="BD/BA",
                yaxis_title="Number of Units",
                legend_title="Status",
                width=1000,
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

          

        with col8:
            # Ensure "Status" column exists
            if "Status" in rent_roll.columns:
                status_counts = rent_roll["Status"].value_counts().reset_index()
                status_counts.columns = ["Status", "Count"]

                # Normalize to match color map keys
                status_counts["Status"] = status_counts["Status"].str.strip().str.title().str.replace(" ", "-")

                color_map = {
                    "Current": "lightgrey",
                    "Vacant-Unrented": "steelblue",
                    "Vacant-Rented": "lightblue",
                    "Evict": "red",
                    "Notice-Unrented": "mediumseagreen",
                    "Notice-Rented": "orange"
                }

                fig4 = px.pie(
                    status_counts,
                    values="Count",
                    names="Status",
                    title="🏠 Tenant Status Distribution",
                    hole=0.4,
                    color_discrete_map=color_map
                )

                fig4.update_layout(
                    width=800, height=600,
                    legend=dict(font=dict(size=14), x=1, y=0.9, xanchor="right")
                )

                fig4.update_traces(
                    textinfo="percent+label",
                    pull=[0.1 if i == 0 else 0 for i in range(len(status_counts))]
                )

                st.plotly_chart(fig4, use_container_width=True)
                img_path4 = os.path.join(IMG_DIR, "status.png")
                fig4.write_image(img_path4)
            else:
                st.warning("⚠️ 'Status' column not found in dataset.")

        col9, col10 = st.columns(2)

        with col9:
            today = datetime.today()
            
            tenant_data['Move-in'] = pd.to_datetime(tenant_data['Move-in'], errors='coerce')
            tenant_data1 = tenant_data[tenant_data['Move-in'] >= today]
            # Extract Month-Year
            tenant_data1['Move-in Month'] = tenant_data1['Move-in'].dt.to_period("M").astype(str)
            movein_counts = (
                tenant_data1.groupby('Move-in Month').size().reset_index(name='Count')
                .rename(columns={'Move-in Month': 'Month'})
            )
            movein_counts['Type'] = 'Move-in'

            tenant_data2 = tenant_data.copy()

            tenant_data2['Lease To'] = pd.to_datetime(tenant_data2['Lease To'], errors='coerce')
            tenant_data2 = tenant_data2[tenant_data2['Lease To'] >= today]
            
            tenant_data2['Lease To Month'] = tenant_data2['Lease To'].dt.to_period("M").astype(str)

            # Count Move-ins
           
            # Count Move-outs
            moveout_counts = (
                tenant_data2.groupby('Lease To Month').size().reset_index(name='Count')
                .rename(columns={'Lease To Month': 'Month'})
            )
            moveout_counts['Type'] = 'Lease To'

            # Combine and convert Month to datetime
            combined = pd.concat([movein_counts, moveout_counts])
            combined['Month'] = pd.to_datetime(combined['Month'], format='%Y-%m')
            combined = combined.sort_values('Month')
            combined['Month'] = combined['Month'].dt.strftime('%b %Y')

            fig = px.line(
                combined,
                x='Month',
                y='Count',
                color='Type',
                markers=True,
                title="📈 Monthly Move-ins vs Lease To",
                color_discrete_map={
                    "Move-in": "green",
                    "Lease To": "red"
                }
            )

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Number of Units",
                yaxis=dict(range=[0, 200]),  # 👈 Adjust max value here
                legend_title="Event Type",
                width=1000,
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)
        

        with col10:

            tenant_data['Lease To'] = pd.to_datetime(tenant_data['Lease To'], errors='coerce')

            today = datetime.today()

            def categorize_moveout_days(row):
                if pd.isna(row['Lease To']):
                    return None
                delta = (row['Lease To'] - today).days
                if delta < 0:
                    return None  # Already moved out
                elif delta <= 30:
                    return '0-30 Days'
                elif delta <= 60:
                    return '31-60 Days'
                elif delta <= 90:
                    return '61-90 Days'
                elif delta <= 365:
                    return '91-365 Days'
                else:
                    return None

            tenant_data['Move Out Bucket'] = tenant_data.apply(lambda row: categorize_moveout_days(row), axis=1)

            # Group only by Move Out Bucket
            grouped = (
                tenant_data[tenant_data['Move Out Bucket'].notna()]
                .groupby(['Move Out Bucket'])
                .size()
                .reset_index(name='Count')
            )

            # Bar chart without Property Name
            fig = px.bar(
                grouped,
                x="Move Out Bucket",
                y="Count",
                title="📦 Upcoming Move-Outs",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            fig.update_layout(
                xaxis_title="Move Out Timeframe",
                yaxis_title="Number of Units",
                width=1000,
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

        col11, col12 = st.columns(2)

        with col11:
            trailing_12months['date_str'] = pd.to_datetime(trailing_12months['date_str'], format='%m-%d-%Y')
            trailing_12months = trailing_12months.sort_values(by='date_str')
            summary = []
            for date, group in trailing_12months.groupby('date_str'):
                total = len(group)
                evict = group[group['Status'] == 'Evict'].shape[0]
                summary.append({
                    "Month": date.strftime("%b %Y"),
                    "Evict": evict
                })

            df_occ = pd.DataFrame(summary)

            fig = go.Figure()

            # Line chart for Occupancy %
            fig.add_trace(
                go.Scatter(
                    x=df_occ["Month"],
                    y=df_occ["Evict"],
                    mode="lines+markers",
                    name="Evict",
                    line=dict(color="orange"),
                    marker=dict(size=8),
                    text=df_occ["Evict"],
                    textposition="top center"
                )
            )

            # Layout
            fig.update_layout(
                title="📊 Monthly Occupancy % and Total Units",
                xaxis=dict(title="Month", title_font=dict(size=14), tickfont=dict(size=12)),
                yaxis=dict(title="Evict", title_font=dict(size=14), tickfont=dict(size=12), gridcolor="lightgray"),
               
                legend=dict(title="Metrics", font=dict(size=12)),
                width=1000, height=600,
                margin=dict(l=50, r=50, t=50, b=50)
            )

            st.plotly_chart(fig, use_container_width=True)

        with col12:

            # Clean the 'Past Due' column: remove $ and commas, convert to float
            rent_roll['Past Due'] = (
                rent_roll['Past Due']
                .astype(str)  # Convert to string in case of mixed types
                .str.replace(r'[$,]', '', regex=True)  # Remove $ and commas
            )

            # Convert to numeric, coercing any invalid entries to NaN, then fill NaN with 0
            rent_roll['Past Due'] = pd.to_numeric(rent_roll['Past Due'], errors='coerce').fillna(0)

            # Filter for tenants who have any amount past due
            df_delinquent = rent_roll[rent_roll['Past Due'] > 0]

            summary = df_delinquent.groupby('BD/BA').agg(
                Delinquent_Units=('Unit', 'count'),
                Delinquent_Amount=('Past Due', 'sum')
            ).reset_index()

            summary = summary.sort_values(by='Delinquent_Units', ascending=False)

            fig = go.Figure()

            # Bar chart for $ amount (use y2 - right side)
            fig.add_trace(go.Bar(
                x=summary['BD/BA'],
                y=summary['Delinquent_Amount'],
                name='Delinquent $',
                yaxis='y2',
                marker_color='blue',
                opacity=0.4
            ))

            # Line chart for unit count (use y - left side)
            fig.add_trace(go.Scatter(
                x=summary['BD/BA'],
                y=summary['Delinquent_Units'],
                mode='lines+markers+text',
                text=summary['Delinquent_Units'],
                textposition='top center',
                name='Delinquent Units',
                line=dict(color='green'),
                marker=dict(size=10)
            ))

            fig.update_layout(
                title="💰 Delinquency by Unit Type (BD/BA)",
                xaxis=dict(title="BD/BA"),
                
                yaxis=dict(  # LEFT: Delinquent Units
                    title=dict(text="Delinquent Units"),
                    tickformat=","
                ),
                
                yaxis2=dict(  # RIGHT: Delinquent Amount $
                    title=dict(text="Delinquent Amount ($)"),
                    tickformat="$.2s",
                    overlaying="y",
                    side="right",
                    showgrid=False
                ),

                legend=dict(title="Metric"),
                width=1000,
                height=600,
                margin=dict(t=60, b=60, l=50, r=50)
            )

            st.plotly_chart(fig, use_container_width=True)


    with tab2:
        # Filters
        properties1 = dfs["Rent Roll"]["Property Name"].dropna().unique().tolist()

        col_prop1 = st.columns(3)[0]

        with col_prop1:
            selected_property1 = st.selectbox("Filter by Property", ["All"] + properties1, key="property_tab2")

        # Filter data
        rent_roll = dfs["Rent Roll"].copy()

        if selected_property1 != "All":
            rent_roll = rent_roll[rent_roll["Property Name"] == selected_property1]

        col26, col27 = st.columns(2)

        with col26:
            # Clean Rent and Market Rent columns
            rent_roll["Rent"] = pd.to_numeric(rent_roll["Rent"].replace("[\$,]", "", regex=True), errors="coerce")
            rent_roll["Market Rent"] = pd.to_numeric(rent_roll["Market Rent"].replace("[\$,]", "", regex=True), errors="coerce")

            # Drop rows with missing rent data
            filtered_df = rent_roll.dropna(subset=["Rent", "Market Rent"])

            # Group and aggregate
            avg_rent_df = filtered_df.groupby("BD/BA")[["Rent", "Market Rent"]].mean().round(0).reset_index()
            unit_count_df = filtered_df.groupby("BD/BA").size().reset_index(name="Unit Count")

            # Merge
            final_df = avg_rent_df.merge(unit_count_df, on="BD/BA")

            # Plot
            fig3 = go.Figure()

            fig3.add_trace(go.Bar(
                x=final_df["BD/BA"], 
                y=final_df["Rent"], 
                name="Avg Rent",
                marker_color="lightblue",
                text=final_df["Rent"], 
                textposition="auto"
            ))

            fig3.add_trace(go.Bar(
                x=final_df["BD/BA"], 
                y=final_df["Market Rent"], 
                name="Avg Market Rent",
                marker_color="lightgreen",
                text=final_df["Market Rent"], 
                textposition="auto"
            ))

            fig3.add_trace(go.Scatter(
                x=final_df["BD/BA"], 
                y=final_df["Unit Count"], 
                name="Unit Count",
                mode="lines+markers",
                yaxis="y2",
                line=dict(color="red", width=2),
                marker=dict(size=8),
            ))

            fig3.update_layout(
                title="📊 Avg Rent vs. Market Rent with Unit Count by BD/BA",
                xaxis=dict(title="Bedroom/Bathroom", tickangle=-45, tickfont=dict(size=12)),
                yaxis=dict(title="Amount ($)", gridcolor="lightgray"),
                yaxis2=dict(title="Unit Count", overlaying="y", side="right", showgrid=False),
                legend=dict(title="Legend"),
                width=1000,
                height=600,
                bargap=0.15,
                barmode="group"
            )

            st.plotly_chart(fig3, use_container_width=True)

        with col27:
            pass  # You can add another visualization or summary here

    with tab3:
      
        col36, col37 = st.columns(2)

        with col36:
           
            df_leasing = dfs["Leasing"].copy()

            # Sum values across all properties
            funnel_counts = {
                "Move-Ins": df_leasing["Move-Ins"].sum(),
                "Approved": df_leasing["Approved"].sum(),
                "Rental Applications": df_leasing["Rental Apps"].sum(),
                "Completed Shows": df_leasing["Completed Showings"].sum(),
                "Inquiries": df_leasing["Inquiries"].sum(),
            }

            # Convert to DataFrame
            funnel_df = pd.DataFrame({
                "Stage": list(funnel_counts.keys()),
                "Count": list(funnel_counts.values())
            })

            # Create funnel chart
            fig = px.funnel(
                funnel_df,
                x="Count",
                y="Stage",
                title="🔻 Leasing Funnel Overview",
                color="Stage",
                color_discrete_sequence=px.colors.sequential.Blues
            )

            # Improve layout
            fig.update_layout(
                yaxis_title="Leasing Stage",
                xaxis_title="Number of Leads",
                showlegend=False,
                width=700,
                height=500,
                margin=dict(t=50, b=50, l=50, r=50)
            )

            # Show in Streamlit
            st.plotly_chart(fig, use_container_width=True)

        with col37:
        
            df_prospect = dfs["Prospect"].copy()

            # Clean data
            df_prospect['Source'] = df_prospect['Source'].fillna("Unknown")

            # Group by Source
            summary = df_prospect.groupby("Source").agg(
                Guest_Cards=('Guest Card Inquiries', 'sum'),
                Converted_Tenants=('Converted Tenants', 'sum')
            ).reset_index()

            # Sort by most Guest Cards
            summary = summary.sort_values(by="Converted_Tenants", ascending=False).head(10)

            # Create bar chart
            fig = go.Figure()

            # Bar 1: Guest Card Inquiries
            fig.add_trace(go.Bar(
                x=summary["Source"],
                y=summary["Guest_Cards"],
                name="Guest Card Inquiries",
                marker_color="skyblue"
            ))

            # Bar 2: Converted Tenants
            fig.add_trace(go.Bar(
                x=summary["Source"],
                y=summary["Converted_Tenants"],
                name="Converted Tenants",
                marker_color="seagreen"
            ))

            # Layout
            fig.update_layout(
                title="📈 Guest Card Inquiries vs Converted Tenants by Source",
                xaxis=dict(title="Lead Source", tickangle=-45),
                yaxis=dict(title="Count"),
                barmode='group',
                legend_title="Metric",
                width=1000,
                height=600
            )

            # Show in Streamlit
            st.plotly_chart(fig, use_container_width=True)


    with tab4:
        
         # Filters
        properties4 = dfs["Rent Roll"]["Property Name"].dropna().unique().tolist()

        col_prop4 = st.columns(3)[0]

        with col_prop4:
            selected_property4 = st.selectbox("Filter by Property", ["All"] + properties4, key="property_tab4")

        # Filter data
        df_work = dfs["Work Orders"].copy()
        df_work1 = dfs["Work Orders"].copy()

        if selected_property4 != "All":
            df_work = df_work[df_work["Property Name"] == selected_property4]
            df_work1 = df_work1[df_work1["Property Name"] == selected_property4]

        col45, col46 = st.columns(2)

        with col45:
            
            st.subheader("🛠️ Most Common Terms in Work Order Descriptions")

            if "Job Description" in df_work.columns:
                # Combine all job descriptions into one big string
                text = " ".join(str(desc) for desc in df_work['Job Description'].dropna())

                if text.strip():  # ✅ Only proceed if there's non-empty text
                    custom_stopwords = set(STOPWORDS)
                    custom_stopwords.update([
                        "unit", "please", "de", "la", "y", "need", "working", "lo", "needs", "por", "come", "fix", "que", "se", "en", "el",
                        "agua", "funciona", "cocina"
                    ])

                    # Generate the Word Cloud
                    wordcloud = WordCloud(
                        width=800,
                        height=400,
                        background_color='white',
                        colormap='tab10',
                        max_words=100,
                        contour_width=0.5,
                        contour_color='steelblue',
                        stopwords=custom_stopwords,
                    ).generate(text)

                    # Display it with Matplotlib in Streamlit
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.imshow(wordcloud, interpolation='bilinear')
                    ax.axis('off')
                    st.pyplot(fig)

                else:
                    st.warning("⚠️ No job descriptions available to generate a word cloud.")
            else:
                st.warning("⚠️ 'Job Description' column not found in the data.")

        with col46:

            # Ensure date column is datetime
            df_work["Created At"] = pd.to_datetime(df_work["Created At"], errors="coerce")

            # Drop rows without valid dates or statuses
            df_work = df_work.dropna(subset=["Created At", "Status"])

            # Create a "Month" column (e.g., '2025-04')
            df_work["Month"] = df_work["Created At"].dt.to_period("M").astype(str)

            # Group by Month and Status
            grouped = (
                df_work.groupby(["Month", "Status"])
                .size()
                .reset_index(name="Count")
            )

            fig = px.bar(
                grouped,
                x="Month",
                y="Count",
                color="Status",
                barmode="stack",
                title="📅 Monthly Work Orders by Status",
                color_discrete_sequence=[ "orange", "steelblue", "mediumseagreen", "lightgrey",
        "indianred", "goldenrod", "cadetblue", "mediumslateblue", "teal", "darkkhaki"]
           
            )

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Number of Work Orders",
                legend_title="Work Order Status",
                width=1000,
                height=600
            )

            # Show in Streamlit
            st.plotly_chart(fig, use_container_width=True)

    with tab5:

         # Get unique filter values
        properties5 = dfs["Rent Roll"]["Property Name"].dropna().unique().tolist()

        col_prop5 = st.columns(3)[0]

        with col_prop5:
            selected_property5 = st.selectbox("Filter by Property", ["All"] + properties5, key="property_tab5")

       # Filter data
        rent_roll = dfs["Rent Roll"].copy()
        tenant_data = dfs["Tenant Data"].copy()
        tenant_data1 = dfs["Tenant Data"].copy()

        if selected_property5 != "All":
            rent_roll = rent_roll[rent_roll["Property Name"] == selected_property5]
            tenant_data = tenant_data[tenant_data["Property Name"] == selected_property5]
            tenant_data = tenant_data[tenant_data["Property Name"] == selected_property5]

        col51, col52, col53, col54 = st.columns(4)

        total_residents = rent_roll[rent_roll['Status'] == 'Current'].shape[0] # or df.shape[0] if 1 row per resident
        eviction_filings = rent_roll[rent_roll['Status'] == 'Evict'].shape[0]
        notice = rent_roll[rent_roll['Status'] == 'Notice'].shape[0]
        future = rent_roll[rent_roll['Status'] == 'Future'].shape[0]
        evictions_per_resident = round(eviction_filings / total_residents, 3)

        # Display the metric card
        col51.metric(label="🏠Current Residents", value=f"{total_residents}")
        col52.metric(label="📊Notice Residents",  value=f"{notice}")
        col53.metric(label="🚪Future tenants (Next 60 days)", value=f"{future}")
        col54.metric(label="⚖️ Eviction Filings per Residentt", value=f"{evictions_per_resident}")
        
        col55, col56 = st.columns(2)

        with col55:

            # Clean columns
            rent_roll['Past Due'] = pd.to_numeric(rent_roll['Past Due'], errors='coerce').fillna(0)
            rent_roll['Late Count'] = pd.to_numeric(rent_roll['Late Count'], errors='coerce').fillna(0)

            # Filter for tenants with Late Count > 0
            df_late = rent_roll[rent_roll['Late Count'] > 0]

           
            # Group by Tenant (or Unit if better)
            summary = df_late.groupby("Tenant").agg(
                Past_Due=('Past Due', 'sum'),
                Late_Count=('Late Count', 'sum')
            ).reset_index()

            # Sort by most Past Due
            summary = summary.sort_values(by="Past_Due", ascending=False).head(30)  # top 30 tenants
           
            # Plotly dual-axis chart
            fig = go.Figure()

            # Bar: Past Due $
            fig.add_trace(go.Bar(
                x=summary['Tenant'],
                y=summary['Past_Due'],
                name='Past Due ($)',
                yaxis='y2',
                marker_color='indianred',
                opacity=0.6
            ))

            # Line: Late Count
            fig.add_trace(go.Scatter(
                x=summary['Tenant'],
                y=summary['Late_Count'],
                name='Late Count',
                yaxis='y1',
                mode='lines+markers',
                line=dict(color='green'),
                marker=dict(size=8)
            ))

            # Layout
            fig.update_layout(
                title="📉 Late Tenants: Past Due vs Late Count",
                xaxis=dict(title="Tenant", tickangle=-45),
                yaxis=dict(
                    title="Late Count",
                    tickfont=dict(color="green"),
                ),
                yaxis2=dict(
                    title="Past Due ($)",
                    overlaying="y",
                    side="right",
                    tickformat="$.2s",
                    tickfont=dict(color="indianred"),
                    showgrid=False
                ),
                legend=dict(title="Metrics"),
                height=600,
                width=1100,
                margin=dict(t=60, b=80, l=50, r=50)
            )

            st.plotly_chart(fig, use_container_width=True)

        with col56:
                        # Group by Property
            summary = (
                rent_roll.groupby("Property Name")
                .agg(
                    Total_Residents=('Tenant', 'nunique'),
                    Eviction_Filings=('Status', lambda x: (x == 'Evict').sum())
                )
                .reset_index()
            )

            # Calculate ratio
            summary['Evictions per Resident'] = summary['Eviction_Filings'] / summary['Total_Residents']


            fig = px.bar(
                summary,
                x="Property Name",
                y="Evictions per Resident",
                title="📉 Eviction Filings per Resident by Property",
                color="Evictions per Resident",
                color_continuous_scale="OrRd"
            )

            fig.update_layout(
                xaxis_title="Property",
                yaxis_title="Evictions per Resident",
                width=1000,
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

    with tab6:
          # Filters
        properties6 = dfs["Bill"]["Property Name"].dropna().unique().tolist()

        col_prop6 = st.columns(3)[0]

        with col_prop6:
            selected_property6 = st.selectbox("Filter by Property", ["All"] + properties6, key="property_tab6")

        # Filter data
        bill = dfs["Bill"].copy()
        bill1 = dfs["Bill"].copy()

        if selected_property6 != "All":
            bill = bill[bill["Property Name"] == selected_property6]
            bill1 = bill1[bill1["Property Name"] == selected_property6]

        col65, col66 = st.columns(2)

        with col65:

            # Parse datetime and extract month
            bill['Bill Date'] = pd.to_datetime(bill['Bill Date'], errors='coerce')
            bill['Month'] = bill['Bill Date'].dt.to_period("M").astype(str)

            # Convert amounts to numeric
            bill['Paid'] = pd.to_numeric(bill['Paid'], errors='coerce').fillna(0)
            bill['Unpaid'] = pd.to_numeric(bill['Unpaid'], errors='coerce').fillna(0)

            # Group by Month
            monthly_summary = bill.groupby('Month').agg({
                'Paid': 'sum',
                'Unpaid': 'sum',
                'Reference': 'nunique'  # Count of unique bill references
            }).reset_index().sort_values('Month')

            # Stacked bar chart: Paid and Unpaid
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=monthly_summary['Month'],
                y=monthly_summary['Paid'],
                name='Paid',
                marker_color='mediumseagreen',
                text=monthly_summary['Paid'].map('${:,.0f}'.format),
                textposition='auto'
            ))

            fig.add_trace(go.Bar(
                x=monthly_summary['Month'],
                y=monthly_summary['Unpaid'],
                name='Unpaid',
                marker_color='indianred',
                text=monthly_summary['Unpaid'].map('${:,.0f}'.format),
                textposition='auto'
            ))
            # Reference Line Chart
            fig.add_trace(go.Scatter(
                x=monthly_summary['Month'],
                y=monthly_summary['Reference'],
                name='Reference Count',
                yaxis='y2',
                mode='lines+markers',
                line=dict(color='orange', width=3),
                marker=dict(size=7),
                text=monthly_summary['Reference'],
                textposition='top center'
            ))
            fig.update_layout(
                barmode='stack',
                title='💸 Paid vs Unpaid Amounts by Month',
                xaxis=dict(title='Month'),
                yaxis=dict(title='Amount ($)', tickformat="$.2s"),
                yaxis2=dict(
                    title='Number of References',
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                legend=dict(title='Payment Status'),
                height=600,
                width=1000
            )
            # Show chart in Streamlit
            st.plotly_chart(fig, use_container_width=True)

        with col66:

            # Ensure columns are in correct type
            bill['Bill Date'] = pd.to_datetime(bill['Bill Date'], errors='coerce')
            bill['Paid'] = pd.to_numeric(bill['Paid'], errors='coerce')

            # Drop nulls in critical fields
            bill_cleaned = bill.dropna(subset=['Payee Name', 'Bill Date', 'Paid'])

            # Extract Month-Year
            bill_cleaned['Month'] = bill_cleaned['Bill Date'].dt.to_period("M").astype(str)

            top_payees = (
                bill_cleaned.groupby('Payee Name')['Paid'].sum()
                .sort_values(ascending=False)
                .head(10)
                .index
            )

            df_top = bill_cleaned[bill_cleaned['Payee Name'].isin(top_payees)]
            # Group by Month and Payee
            monthly_spend = (
                df_top.groupby(['Month', 'Payee Name'])['Paid'].sum()
                .reset_index()
                .sort_values('Month')
            )

            # Plot with Plotly
            fig = px.line(
                monthly_spend,
                x='Month',
                y='Paid',
                color='Payee Name',
                markers=True,
                title="💸 Monthly Spend by Top 10 Vendor",
                labels={'Paid': 'Amount ($)', 'Month': 'Month'},
            )

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Total $ Spent",
                width=1000,
                height=600,
                legend_title="Vendor",
                xaxis=dict(tickangle=-45),
                hovermode="x unified"
            )

            st.plotly_chart(fig, use_container_width=True)

        with tab1:
            st.subheader("🏠 Property Performance")
            st.write(rent_roll1)

        with tab2:
            st.subheader("💰 Rent")
            st.write(rent_roll1)

        with tab3:
            st.subheader("📝 Leasing")
            st.write(dfs["Leasing"])
         
        with tab4:
            st.subheader("🔧 Maintenance")
            st.write(df_work1)
        
        with tab5:
            st.subheader("🏢 Tenants")
            st.write(tenant_data1)

        with tab6:
            st.subheader("📄 Billings")
            st.write(bill1)
       

if __name__ == "__main__":
    show_dashboard()
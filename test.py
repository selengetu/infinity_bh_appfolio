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

# st.set_page_config(page_title="Infinity BH Dashboards", layout="wide")

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
        "Bill": "bill_cleaned",
        "Guest": "guest_cleaned",
        "General Ledger": "general_ledger_cleaned",
        "Rent Roll 12 Months": "rentroll_12_months_combined",
    }
    today = datetime.today()
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
        "Bill": latest_files.get("Bill"),
        "Guest": latest_files.get("Guest"),
        "General Ledger": latest_files.get("General Ledger"),
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

    region_df = pd.read_csv("region_list.csv")

    # 🔹 Generate and Save Plotly Charts as Images
    image_paths = []
    # 🔹 3. Display DataFrames in Tabs
    if dfs:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🏠 Property Performance", 
            "💰 Financials", 
            "📝 Leasing", 
            "🔧 Maintenance", 
            "🏢 Tenants", 
            "📄 Billings"
        ])

    with tab1:

       # Filter data
        rent_roll = dfs["Rent Roll"].copy()
        rent_roll1 = dfs["Rent Roll"].copy()
        trailing_12months = dfs["Rent Roll 12 Months"].copy()  
        tenant_data = dfs["Tenant Data"].copy()

        rent_roll = rent_roll.merge(region_df, on="Property Name", how="left")
        rent_roll1 = rent_roll1.merge(region_df, on="Property Name", how="left")
        trailing_12months = trailing_12months.merge(region_df, on="Property Name", how="left")
        tenant_data = tenant_data.merge(region_df, on="Property Name", how="left")

        properties =  sorted(rent_roll["Property Name"].dropna().unique().tolist() , key=str.lower)
        regions=  sorted(rent_roll["Region"].dropna().unique().tolist(), key=str.lower)


        col_prop,col_region, col_s= st.columns(3)

        with col_prop:
            selected_property = st.multiselect(
                "Filter by Property",
                options=properties,
                default=[],
                key="property_tab"
            )

        with col_region:
            selected_region = st.multiselect(
                "Filter by Region",
                options=regions,
                default=[],
                key="region_tab"
            )   
        

        if selected_property:
            rent_roll = rent_roll[rent_roll["Property Name"].isin(selected_property)]
            rent_roll1 = rent_roll1[rent_roll1["Property Name"].isin(selected_property)]
            trailing_12months = trailing_12months[trailing_12months["Property Name"].isin(selected_property)]
            tenant_data = tenant_data[tenant_data["Property Name"].isin(selected_property)]

        if selected_region:
            rent_roll = rent_roll[rent_roll["Region"].isin(selected_region)]
            rent_roll1 = rent_roll1[rent_roll1["Region"].isin(selected_region)]
            trailing_12months = trailing_12months[trailing_12months["Region"].isin(selected_region)]
            tenant_data = tenant_data[tenant_data["Region"].isin(selected_region)]

        # Metric calculations using filtered data
        col1,col01,col02,col2,col3, col4 = st.columns(6)
        tenant_data['Lease To'] = pd.to_datetime(tenant_data['Lease To'], errors='coerce')
        all_units = rent_roll.shape[0]
        current_resident = rent_roll[rent_roll["Status"] == "Current"].shape[0]
        notice = rent_roll[rent_roll["Status"] == "Notice-Unrented"].shape[0]
        notice_re = rent_roll[rent_roll["Status"] == "Notice-Rented"].shape[0]
        evict = rent_roll[rent_roll["Status"] == "Evict"].shape[0]
        vacant_rented = rent_roll[rent_roll["Status"] == "Vacant-Rented"].shape[0]
        vacant_unrented = rent_roll[rent_roll["Status"] == "Vacant-Unrented"].shape[0]
        future = tenant_data[tenant_data["Status"] == "Future"].shape[0]
        current_nonrenew = tenant_data[
            (tenant_data["Status"] == "Current") &
            (tenant_data["Lease To"] >= today) &
            (tenant_data["Tenant Tags"].str.contains(r'non[\s-]?renew|not[\s-]?renew', case=False, na=False))
        ].shape[0]
        
        total_vacant = vacant_rented+vacant_unrented
        occupied = current_resident + evict + notice + notice_re
        future_rate = ((current_resident + evict + notice + notice_re + future- current_nonrenew)/ all_units) * 100 if all_units > 0 else 0
        occupied_rate = ((current_resident + evict + notice + notice_re) / all_units) * 100 if all_units > 0 else 0

        # Convert rent columns
        rent_roll["Rent"] = rent_roll["Rent"].replace("[\$,]", "", regex=True)
        rent_roll["Rent"] = pd.to_numeric(rent_roll["Rent"], errors="coerce")

        total_residents = rent_roll[rent_roll['Status'] == 'Current'].shape[0]
        
        
        tenant_data['Move-out'] = pd.to_datetime(tenant_data['Move-out'], errors='coerce')
        ninety_days_before = today - timedelta(days=90)

        # Filter rows where Move-out is after ninety_days_before
        filtered_move_outs = tenant_data[tenant_data['Move-out'] >= today]

        distinct_units = filtered_move_outs[['Property Name', 'Unit']].drop_duplicates()

        # Count unique apartments moving out
        total_move_out = len(distinct_units)
    
        tenant_data['Move-in'] = pd.to_datetime(tenant_data['Move-in'], errors='coerce')
        ninety_days_before = today - timedelta(days=90)

        # Filter rows where Move-out is after ninety_days_before
        filtered_move_ins = tenant_data[tenant_data['Move-in'] >= today]
        
        distinct_units_move_in = filtered_move_ins[['Property Name', 'Unit']].drop_duplicates()

        # Count how many tenants moved out
        total_move_ins = len(distinct_units_move_in)

        # Display metrics
        col1.metric(label="🏘️ Total Units", value=f"{all_units:,.0f}")
        col01.metric(label="✅ Total Occupied", value=f"{occupied}")
        col02.metric(label="🌀 Total Vacant", value=f"{total_vacant}")
        col2.metric(label="📈 Future Occupancy Rate", value=f"{future_rate:,.2f}%")
        col3.metric(label="📥 Move-ins (Next 90 days)", value=f"{total_move_ins}")
        col4.metric(label="📤 Move-outs (Next 90 days)", value=f"{total_move_out}")

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
                    mode="lines+markers+text",
                    name="Occupancy %",
                    line=dict(color="green"),
                    marker=dict(size=8),
                    text=df_occ["Occupancy %"].map(lambda x: f"{x:.1f}%"),
                    textposition="top center",
                    textfont=dict(size=12),
                    hovertemplate="Occupancy: %{y}%<extra></extra>"
                )
            )

            # Layout
            fig.update_layout(
                title="📊 Monthly Occupancy Trend",
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
            df_occ["Total Vacant"] = df_occ["Vacant-Rented"] + df_occ["Vacant-Unrented"]

            fig = go.Figure()

            # Bar: Vacant-Rented
            fig.add_trace(
                go.Bar(
                    x=df_occ["Month"],
                    y=df_occ["Vacant-Rented"],
                    name="Vacant-Rented",
                    marker=dict(color="lightblue"),
                    text=df_occ["Vacant-Rented"], 
                    textposition='auto'   
                )
            )

            # Bar: Vacant-Unrented (stacked on top)
            fig.add_trace(
                go.Bar(
                    x=df_occ["Month"],
                    y=df_occ["Vacant-Unrented"],
                    name="Vacant-Unrented",
                    marker=dict(color="steelblue"),
                    text=df_occ["Vacant-Unrented"],           
                    textposition='auto'   
                )
            )
            # Add total vacant labels on top
            fig.add_trace(
                go.Scatter(
                    x=df_occ["Month"],
                    y=df_occ["Vacant-Rented"] + df_occ["Vacant-Unrented"],
                    mode='text+markers',
                    text=df_occ["Total Vacant"].map('{:,}'.format),
                    textposition="top center",
                    marker=dict(opacity=0),  # Hide the markers
                    hoverinfo='skip',
                    showlegend=False,
                    textfont=dict(size=12, color="steelblue",family="Arial Black" ),
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

            totals = grouped.groupby("BD/BA")["Count"].sum().reset_index(name="Total")

            color_map = {
                "Current": "lightgrey",
                "Vacant-Unrented": "steelblue",
                "Vacant-Rented": "lightblue",
                "Evict": "red",
                "Notice-Unrented": "mediumseagreen",
                "Notice-Rented": "orange"
            }

            fig = px.bar(
                grouped,
                x="BD/BA",
                y="Count",
                color="Status",
                barmode="stack",
                color_discrete_map=color_map,
                title="📊 Unit Type Breakdown by Status",
                text="Count"
            )

            # Apply auto text position ONLY to bar traces
            for trace in fig.data:
                if trace.type == "bar":
                    trace.texttemplate = "%{text:,}"
                    trace.textposition = "inside"

            # Add total labels as overlay
            fig.add_trace(
                go.Scatter(
                    x=totals["BD/BA"],
                    y=totals["Total"],
                    mode="text",
                    text=totals["Total"].map('{:,}'.format),
                    textposition="top center",  
                    textfont=dict(size=12, color="steelblue",family="Arial Black" ),
                    showlegend=False
                )
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

                color_map1 = {
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
                    color="Status",
                    color_discrete_map=color_map1
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

        col9, col11 = st.columns(2)

        with col9:
            
            tenant_data['Move-in'] = pd.to_datetime(tenant_data['Move-in'], errors='coerce')
            tenant_data1 = tenant_data[tenant_data['Status'] == 'Future']
            tenant_data1 = tenant_data1.drop_duplicates(subset=['Property Name', 'Unit'])
            # Extract Month-Year
            tenant_data1['Move-in Month'] = tenant_data1['Move-in'].dt.to_period("M").astype(str)
            movein_counts = (
                tenant_data1.groupby('Move-in Month').size().reset_index(name='Count')
                .rename(columns={'Move-in Month': 'Month'})
            )
            movein_counts['Type'] = 'Move-in'

            tenant_data2 = tenant_data.copy()

            tenant_data2['Move-out'] = pd.to_datetime(tenant_data2['Move-out'], errors='coerce')
            ninety_days_before = today - timedelta(days=90)
            ninety_days_later = today + timedelta(days=90)
            tenant_data2 = tenant_data2[(tenant_data2['Move-out'] >= ninety_days_before)]
            tenant_data2 = tenant_data2.drop_duplicates(subset=['Property Name', 'Unit'])
            
            tenant_data2['Move-out Month'] = tenant_data2['Move-out'].dt.to_period("M").astype(str)

            # Count Move-outs
            moveout_counts = (
                tenant_data2.groupby('Move-out Month').size().reset_index(name='Count')
                .rename(columns={'Move-out Month': 'Month'})
            )
            moveout_counts['Type'] = 'Move-out'

            # Combine and convert Month to datetime
            combined = pd.concat([movein_counts, moveout_counts])
            combined['Month'] = pd.to_datetime(combined['Month'], format='%Y-%m')
            combined = combined.sort_values('Month')
            combined['Month'] = combined['Month'].dt.strftime('%b %Y')

            fig = px.bar(
                combined,
                x='Month',
                y='Count',
                color='Type',
                barmode='group',
                text='Count',  # Add data labels
                title="📊 Monthly Move-ins vs Move-outs",
                color_discrete_map={
                    "Move-in": "green",
                    "Move-out": "red"
                }
            )

            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Number of Units",
                yaxis=dict(range=[0, 200]),  # Optional: adjust y-axis range
                legend_title="Event Type",
                width=1000,
                height=600
            )

            fig.update_traces(
                texttemplate='%{text:,}',  # Thousand separator in labels
                textposition='outside'
            )

            st.plotly_chart(fig, use_container_width=True)
        

        # with col10:

        #     tenant_data['Move-out'] = pd.to_datetime(tenant_data['Move-out'], errors='coerce')
        #     tenant_data_filtered = tenant_data.dropna(subset=["Property Name", "Unit"])

        #     def categorize_moveout_days(row):
        #         if pd.isna(row['Move-out']):
        #             return None
        #         delta = (row['Move-out'] - today).days
        #         if delta < 0:
        #             return None  # Already moved out
        #         elif delta <= 30:
        #             return '0-30 Days'
        #         elif delta <= 60:
        #             return '31-60 Days'
        #         elif delta <= 90:
        #             return '61-90 Days'

        #         else:
        #             return None
            
        #     tenant_data_filtered['Move Out Bucket'] = tenant_data.apply(lambda row: categorize_moveout_days(row), axis=1)
            

        #     # Group only by Move Out Bucket
        #     grouped = (
        #         tenant_data_filtered[tenant_data_filtered['Move Out Bucket'].notna()]
        #         .groupby(['Move Out Bucket'])
        #         .size()
        #         .reset_index(name='Count')
        #     )

        #     # Bar chart without Property Name
        #     fig = px.bar(
        #         grouped,
        #         x="Move Out Bucket",
        #         y="Count",
        #         title="📦 Upcoming Move-Outs",
        #         color_discrete_sequence=px.colors.qualitative.Pastel,
        #         text="Count"  
        #     )

        #     fig.update_layout(
        #         xaxis_title="Move Out Timeframe",
        #         yaxis_title="Number of Units",
        #         width=1000,
        #         height=600
        #     )

        #     st.plotly_chart(fig, use_container_width=True)

        

        # with col11:
        #     trailing_12months['date_str'] = pd.to_datetime(trailing_12months['date_str'], format='%m-%d-%Y')
        #     trailing_12months = trailing_12months.sort_values(by='date_str')
        #     summary = []
        #     for date, group in trailing_12months.groupby('date_str'):
        #         total = len(group)
        #         evict = group[group['Status'] == 'Evict'].shape[0]
        #         summary.append({
        #             "Month": date.strftime("%b %Y"),
        #             "Evict": evict
        #         })

        #     df_occ = pd.DataFrame(summary)

        #     fig = go.Figure()

        #     # Line chart for Occupancy %
        #     fig.add_trace(
        #         go.Scatter(
        #             x=df_occ["Month"],
        #             y=df_occ["Evict"],
        #             mode="lines+markers+text",
        #             name="Evict",
        #             line=dict(color="orange"),
        #             marker=dict(size=8),
        #             text=df_occ["Evict"],
        #             textposition="top center"
        #         )
        #     )

        #     # Layout
        #     fig.update_layout(
        #         title="📊 Evictions by month",
        #         xaxis=dict(title="Month", title_font=dict(size=14), tickfont=dict(size=12)),
        #         yaxis=dict(title="Evict", title_font=dict(size=14), tickfont=dict(size=12), gridcolor="lightgray"),
               
        #         legend=dict(title="Metrics", font=dict(size=12)),
        #         width=1000, height=600,
        #         margin=dict(l=50, r=50, t=50, b=50)
        #     )

        #     st.plotly_chart(fig, use_container_width=True)
        
     
        with col11:

            # Clean the 'Past Due' column: remove $ and commas, convert to float
            rent_roll['Past Due'] = (
                rent_roll['Past Due']
                .astype(str)  # Convert to string in case of mixed types
                .str.replace(r'[$,]', '', regex=True)  # Remove $ and commas
            )

            # Convert to numeric, coercing any invalid entries to NaN, then fill NaN with 0
            rent_roll['Past Due'] = pd.to_numeric(rent_roll['Past Due'], errors='coerce').fillna(0)

            # Filter for tenants who have any amount past due
            df_delinquent = rent_roll[rent_roll['Past Due'] > 500]

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
                opacity=0.4,
                text=summary['Delinquent_Amount'].map('${:,.0f}'.format),  # <- Add this
                textposition='auto'
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
         # Filter data
        rent_roll = dfs["Rent Roll"].copy()
        rent_roll2 = dfs["Rent Roll"].copy()

        rent_roll = rent_roll.merge(region_df, on="Property Name", how="left")
        rent_roll2 = rent_roll2.merge(region_df, on="Property Name", how="left")

        properties1 =  sorted(rent_roll["Property Name"].dropna().unique().tolist() , key=str.lower)
        regions1=  sorted(rent_roll["Region"].dropna().unique().tolist(), key=str.lower)

        col_prop1, col_region1,col_s1 = st.columns(3)

        with col_prop1:
            selected_property1 = st.multiselect(
                "Filter by Property",
                options=properties1,
                default=[],
                key="property_tab2"
            )

        with col_region1:
            selected_region1 = st.multiselect(
                "Filter by Region",
                options=regions1,
                default=[],
                key="region_tab2"
            )   

        if selected_property1:
            rent_roll = rent_roll[rent_roll["Property Name"].isin(selected_property1)]
            rent_roll2 = rent_roll2[rent_roll2["Property Name"].isin(selected_property1)]

        if selected_region1:
            rent_roll = rent_roll[rent_roll["Region"].isin(selected_region1)]
            rent_roll2 = rent_roll2[rent_roll2["Region"].isin(selected_region1)]

         # Metric calculations using filtered data
        col21, col22, col23, col24, col25 = st.columns(5)

        
        # Convert rent columns
        rent_roll["Rent"] = rent_roll["Rent"].replace("[\$,]", "", regex=True)
        rent_roll["Rent"] = pd.to_numeric(rent_roll["Rent"], errors="coerce")
        total_rent = rent_roll["Rent"].sum()

        col21.metric(label="💵 Total Rent", value=f"${total_rent:,.0f}")

        col26, col27= st.columns(2)

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
                mode="lines+markers+text",
                yaxis="y2",
                line=dict(color="red", width=2),
                text=final_df["Unit Count"],  # 👈 Use col11 as label
                textposition="top center",
                marker=dict(size=8),
            ))

            fig3.update_layout(
                title="📊 Average In Place rent vs Current Asking Rent",
                xaxis=dict(title="Bedroom/Bathroom", tickangle=-45, tickfont=dict(size=12)),
                yaxis=dict(title="Amount ($)", gridcolor="lightgray"),
                yaxis2=dict(title="Unit Count", overlaying="y", side="right", showgrid=False),
                legend=dict(title="Legend"),
                width=1000,
                height=600,
                bargap=0.15,
                barmode="group"
            )

            fig3.update_traces(
                selector=dict(type="bar"),
                texttemplate="$%{text:,}",  # Format as dollar + comma separated
                textposition="auto"
            )

            st.plotly_chart(fig3, use_container_width=True)


        with col27:

            rent_roll["Rent"] = pd.to_numeric(rent_roll["Rent"].replace(r"[\$,]", "", regex=True), errors="coerce")
            rent_roll["Market Rent"] = pd.to_numeric(rent_roll["Market Rent"].replace(r"[\$,]", "", regex=True), errors="coerce")

            # Drop rows with missing critical data
            filtered_df = rent_roll.dropna(subset=["Rent", "Market Rent", "Property Name", "BD/BA"])

            # Group and aggregate
            summary = (
                filtered_df.groupby(["Property Name", "BD/BA"])
                .agg(
                    Avg_Rent=("Rent", "mean"),
                    Avg_Market_Rent=("Market Rent", "mean"),
                    Unit_Count=("BD/BA", "count")
                )
                .reset_index()
            )

            summary = summary.rename(columns={
                "Avg_Rent": "Avg Rent",
                "Avg_Market_Rent": "Avg Market Rent",
                "Unit_Count": "Unit Count"
            })
            # Calculate Variance
            summary["Variance"] =  summary["Avg Rent"] - summary["Avg Market Rent"]

            # Round values
            summary = summary.round({"Avg_Rent": 0, "Avg_Market_Rent": 0, "Variance": 0})

            # 🎨 Define style function
            def highlight_variance(val):
                if val < 0:
                    return 'background-color: #FF5C5C'  # light red
                else:
                    return ''

            styled_summary = summary.style.format({
                "Avg Rent": "${:,.0f}",
                "Avg Market Rent": "${:,.0f}",
                "Variance": "${:,.0f}",
                "Unit Count": "{:,}"
            }).applymap(highlight_variance, subset=["Variance"])

            # ✨ Header
            st.subheader("🏘️ Property Leasing Summary: Average Rent, Market Rent & Variances")

            # ✨ Table
            st.dataframe(styled_summary)


    with tab3:
        df_guest= dfs["Guest"].copy()
        df_guest1 = dfs["Guest"].copy()
        
        df_guest = df_guest.merge(region_df, left_on="Property Name", right_on="Property Name", how="left")
        df_guest1 = df_guest1.merge(region_df, left_on="Property Name", right_on="Property Name", how="left")

        properties3 =  sorted(df_guest["Property Name"].dropna().unique().tolist() , key=str.lower)
        regions3=  sorted(df_guest["Region"].dropna().unique().tolist(), key=str.lower)

        col_prop3,col_region3,col_date1, col_date2 = st.columns(4)

        with col_prop3:
            selected_property3 = st.multiselect(
                "Filter by Property",
                options=properties3,
                default=[],
                key="property_tab3"
            )

        with col_region3:
            selected_region3 = st.multiselect(
                "Filter by Region",
                options=regions3,
                default=[],
                key="region_tab3"
            ) 
        with col_date1:
            start_date = st.date_input("Start Date", value=datetime(2024, 1, 1), key="start_date3")
        with col_date2:
            end_date = st.date_input("End Date", value=datetime.now(), key="end_date3")

        if selected_region3:
            df_guest = df_guest[df_guest["Region"].isin(selected_region3)]
            df_guest1 = df_guest1[df_guest1["Region"].isin(selected_region3)]

        if selected_property3:
            df_guest = df_guest[df_guest["Property Name"].isin(selected_property3)]
            df_guest1 = df_guest1[df_guest1["Property Name"].isin(selected_property3)]

        if "Inquiry Received" in df_guest.columns:
            df_guest["Inquiry Received"] = pd.to_datetime(df_guest["Inquiry Received"], errors="coerce")
            df_guest = df_guest[(df_guest["Inquiry Received"] >= pd.to_datetime(start_date)) & (df_guest["Inquiry Received"] <= pd.to_datetime(end_date))]
            df_guest1["Inquiry Received"] = pd.to_datetime(df_guest1["Inquiry Received"], errors="coerce")
            df_guest1 = df_guest1[(df_guest1["Inquiry Received"] >= pd.to_datetime(start_date)) & (df_guest1["Inquiry Received"] <= pd.to_datetime(end_date))]
        
        col36, col37 = st.columns(2)

        with col36:

            # Sum values across all properties
            funnel_counts = {
                "Move-Ins": df_guest["Move In Preference"].count(),
                "Rental Applications": df_guest["Rental Application ID"].count(),
                "Completed Shows": df_guest["Showings"].sum(),
                "Inquiries": df_guest["Inquiry ID"].count(),
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
            fig.update_traces(
                texttemplate="%{x:,}",  
                textposition="inside"   
            )

            # Show in Streamlit
            st.plotly_chart(fig, use_container_width=True)

        with col37:
        
            df_guest = dfs["Guest"].copy()

            # Clean data
            df_guest['Source'] = df_guest['Source'].fillna("Unknown")

            # Group by Source
            summary = df_guest.groupby("Source").agg(
                Guest_Cards=('Inquiry ID', 'count'),
                Converted_Tenants=('Move In Preference', 'count')
            ).reset_index()

            # Sort by most Guest Cards
            summary = summary.sort_values(by="Guest_Cards", ascending=False).head(10)

            # Create bar chart
            fig = go.Figure()

            # Bar 1: Guest Card Inquiriess
            fig.add_trace(go.Bar(
                x=summary["Source"],
                y=summary["Guest_Cards"],
                name="Guest Card Inquiries",
                marker_color="skyblue",
                text=summary["Guest_Cards"],         # <- Add data labels
                textposition="auto"       
            ))

            # Bar 2: Converted Tenants
            fig.add_trace(go.Bar(
                x=summary["Source"],
                y=summary["Converted_Tenants"],
                name="Converted Tenants",
                marker_color="seagreen",
                text=summary["Converted_Tenants"],
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

            fig.update_traces(
                texttemplate="%{text:,}",  # Format data labels with thousand separator
                textposition="auto"        # Keep labels positioned automatically
            )

            # Show in Streamlit
            st.plotly_chart(fig, use_container_width=True)


    with tab4:
        
        df_work = dfs["Work Orders"].copy()
        df_work1 = dfs["Work Orders"].copy()

        df_work = df_work.merge(region_df, on="Property Name", how="left")
        df_work1 = df_work1.merge(region_df, on="Property Name", how="left")
        
        properties4 =  sorted(df_work["Property Name"].dropna().unique().tolist() , key=str.lower)
        region4=  sorted(df_work["Region"].dropna().unique().tolist(), key=str.lower)

        col_prop4, col_region4,col_s4 = st.columns(3)

        with col_prop4:
            selected_property4 = st.multiselect(
                "Filter by Property",
                options=properties4,
                default=[],
                key="property_tab4"
            )

        with col_region4:
            selected_region4 = st.multiselect(
                "Filter by Region",
                options=region4,
                default=[],
                key="region_tab4"
            )   

        if selected_property4:
            df_work = df_work[df_work["Property Name"].isin(selected_property4)]
            df_work1 = df_work1[df_work1["Property Name"].isin(selected_property4)]

        if selected_region4:
            df_work = df_work[df_work["Region"].isin(selected_region4)]
            df_work1 = df_work1[df_work1["Region"].isin(selected_region4)]

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

            df_work["Created At"] = pd.to_datetime(df_work["Created At"], errors="coerce")
            df_work = df_work.dropna(subset=["Created At", "Status"])

            # Create proper Month column
            df_work["Month"] = df_work["Created At"].dt.to_period("M").dt.to_timestamp()
            df_work["Month"] = df_work["Month"].dt.strftime('%b %Y')

            # Step 1: Create a full month list
            full_months = pd.period_range(
                start=df_work["Created At"].min().to_period('M'),
                end=df_work["Created At"].max().to_period('M'),
                freq='M'
            ).to_timestamp()
            full_months = full_months.strftime('%b %Y').tolist()

            # Group by Month and Status
            grouped = (
                df_work.groupby(["Month", "Status"])
                .size()
                .reset_index(name="Count")
            )

            # Step 2: Expand full grid (Month x Status)
            all_statuses = grouped["Status"].unique()

            full_index = pd.MultiIndex.from_product(
                [full_months, all_statuses],
                names=["Month", "Status"]
            )

            grouped = grouped.set_index(["Month", "Status"]).reindex(full_index, fill_value=0).reset_index()

            # Step 3: Force Month order
            grouped["Month"] = pd.Categorical(
                grouped["Month"],
                categories=full_months,
                ordered=True
            )

            monthly_totals = grouped.groupby("Month")["Count"].sum().reset_index(name="Total")

            # Plot
            fig = px.bar(
                grouped,
                x="Month",
                y="Count",
                color="Status",
                barmode="stack",
                text="Count",
                title="📅 Monthly Work Orders by Status",
                color_discrete_sequence=[
                    "orange", "steelblue", "mediumseagreen", "lightgrey",
                    "indianred", "goldenrod", "cadetblue", "mediumslateblue", "teal", "darkkhaki"
                ]
            )

            fig.add_trace(
                go.Scatter(
                    x=monthly_totals["Month"],
                    y=monthly_totals["Total"],
                    mode="text",
                    text=monthly_totals["Total"].map('{:,}'.format),
                    textposition="top center",
                    textfont=dict(size=12),
                    showlegend=False
                )
            )
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Number of Work Orders",
                legend_title="Work Order Status",
                width=1000,
                height=600
            )

            fig.update_traces(
                texttemplate="%{text:,}",
                textposition="inside",
                selector=dict(type="bar")
            )

            st.plotly_chart(fig, use_container_width=True)

    with tab5:

        rent_roll = dfs["Rent Roll"].copy()
        tenant_data = dfs["Tenant Data"].copy()
        tenant_data1 = dfs["Tenant Data"].copy()
        trailing_12months = dfs["Rent Roll 12 Months"].copy()  

        rent_roll = rent_roll.merge(region_df, on="Property Name", how="left")
        tenant_data = tenant_data.merge(region_df, on="Property Name", how="left")
        tenant_data1 = tenant_data1.merge(region_df, on="Property Name", how="left")
        trailing_12months = trailing_12months.merge(region_df, on="Property Name", how="left")
    
        properties5 =  sorted(rent_roll["Property Name"].dropna().unique().tolist() , key=str.lower)
        region5 =  sorted(rent_roll["Region"].dropna().unique().tolist(), key=str.lower)
        
        col_prop5, col_region5,col_s5 = st.columns(3)

        with col_prop5:
            selected_property5 = st.multiselect(
                "Filter by Property",
                options=properties5,
                default=[],
                key="property_tab5"
            )

        with col_region5:
            selected_region5 = st.multiselect(
                "Filter by Region",
                options=region5,
                default=[],
                key="region_tab5"
            )   


        if selected_property5:
            rent_roll = rent_roll[rent_roll["Property Name"].isin(selected_property5)]
            tenant_data = tenant_data[tenant_data["Property Name"].isin(selected_property5)]
            tenant_data1 = tenant_data1[tenant_data1["Property Name"].isin(selected_property5)]
            trailing_12months = trailing_12months[trailing_12months["Property Name"].isin(selected_property5)]

        if selected_region5:
            rent_roll = rent_roll[rent_roll["Region"].isin(selected_region5)]
            tenant_data = tenant_data[tenant_data["Region"].isin(selected_region5)]
            tenant_data1 = tenant_data1[tenant_data1["Region"].isin(selected_region5)]
            trailing_12months = trailing_12months[trailing_12months["Region"].isin(selected_region5)]

        col51, col52, col53, col54 = st.columns(4)

        total_residents = rent_roll[rent_roll['Status'] == 'Current'].shape[0] # or df.shape[0] if 1 row per resident
        eviction_filings = rent_roll[rent_roll['Status'] == 'Evict'].shape[0]
        notice = tenant_data[tenant_data['Status'] == 'Notice'].shape[0]
        future = tenant_data[tenant_data['Status'] == 'Future'].shape[0]

        # Display the metric card
        col51.metric(label="🏠Current Occupied Units", value=f"{total_residents:,.0f}")
        col52.metric(label="📊Notice Residents",  value=f"{notice}")
        col53.metric(label="🚪Future tenants", value=f"{future}")
        col54.metric(label="⚖️ Evictions", value=f"{eviction_filings}")
        
        col55= st.columns(1)[0]

        with col55:

            # Clean columns
            rent_roll['Past Due'] = (
                rent_roll['Past Due']
                .astype(str)  # ensure it is string first
                .str.replace(r'[\$,]', '', regex=True)  # remove $ and commas
            )
            rent_roll['Past Due'] = pd.to_numeric(rent_roll['Past Due'], errors='coerce').fillna(0)
            rent_roll['Late Count'] = pd.to_numeric(rent_roll['Late Count'], errors='coerce').fillna(0)
            
            df_late = rent_roll[rent_roll['Past Due'] >500]
            df_late = df_late.sort_values(by="Past Due", ascending=False).head(30)  # top 30 tenants
 
            # Plotly dual-axis chart
            fig = go.Figure()

            # Bar: Past Due $
            fig.add_trace(go.Bar(
                x=df_late['Tenant'],
                y=df_late['Past Due'],
                name='Past Due ($)',
                yaxis='y2',
                marker_color='indianred',
                opacity=0.6,
                text=df_late['Past Due'].map('${:,.0f}'.format),  # <- Add data labels
                textposition='auto' 
            ))

            # Line: Late Count
            fig.add_trace(go.Scatter(
                x=df_late['Tenant'],
                y=df_late['Late Count'],
                name='Late Count',
                yaxis='y1',
                mode='lines+markers',
                text=df_late['Late Count'],  # <- Add data labels
                textposition='top center',   # Adjust label placement
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

        col56,col57= st.columns(2)
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

            summary = summary[summary['Eviction_Filings'] > 0]
            # Sort by Evictions per Resident (descending)
            summary = summary.sort_values(by='Eviction_Filings', ascending=False)


            fig = px.bar(
                summary,
                x="Property Name",
                y="Eviction_Filings",
                title="📉 Eviction_Filings by Property",
                color="Eviction_Filings",
                color_continuous_scale="OrRd",
                text="Eviction_Filings"
            )

            fig.update_layout(
                xaxis_title="Property",
                yaxis_title="Eviction_Filings",
                width=1000,
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

        with col57:
            
                    # Convert date string to datetime
            trailing_12months['date_str'] = pd.to_datetime(trailing_12months['date_str'], format='%m-%d-%Y')

            # Clean 'Past Due' column: remove symbols, convert to float
            trailing_12months['Past Due'] = (
                trailing_12months['Past Due']
                .astype(str)
                .str.replace(r'[\$,]', '', regex=True)
            )
            trailing_12months['Past Due'] = pd.to_numeric(trailing_12months['Past Due'], errors='coerce').fillna(0)

            # Extract Year-Month from date
            trailing_12months['Month'] = trailing_12months['date_str'].dt.to_period('M').dt.to_timestamp()
            df_late = trailing_12months[trailing_12months['Past Due'] >500]

            # Group by month and sum delinquency
            df_delinquency = (
                df_late.groupby('Month')['Past Due']
                .sum()
                .reset_index()
                .sort_values('Month')
            )

            # Format month for display
            df_delinquency['Month Label'] = df_delinquency['Month'].dt.strftime('%b %Y')

            # Plot bar chart
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=df_delinquency['Month Label'],
                y=df_delinquency['Past Due'],
                name='Total Delinquency',
                marker_color='indianred',
                text=df_delinquency['Past Due'].map('${:,.0f}'.format),
                textposition='auto'
            ))

            fig.update_layout(
                title="💰 Total Delinquency by Month (Trailing 12 Months)",
                xaxis_title="Month",
                yaxis_title="Delinquent Amount ($)",
                yaxis_tickformat="$.2s",
                width=1000,
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)



    with tab6:
        
        bill = dfs["Bill"].copy()
        bill1 = dfs["Bill"].copy()
        general_ledger = dfs["General Ledger"].copy()

        bill = bill.merge(region_df, on="Property Name", how="left")
        bill1 = bill1.merge(region_df, on="Property Name", how="left")

        properties6 =  sorted(dfs["Bill"]["Property Name"].dropna().unique().tolist() , key=str.lower)
        properties06 = sorted(dfs["Bill"]["Payee Name"].dropna().unique().tolist(), key=str.lower)
        region6 =  sorted(bill["Region"].dropna().unique().tolist(), key=str.lower)
        gl_accounts6 =  sorted(bill["GL Account Name"].dropna().unique().tolist(), key=str.lower)

        col_prop6,col_region6, col_prop06,col_gl6= st.columns(4)

        with col_prop6:
            selected_property6 = st.multiselect(
                "Filter by Property",
                options=properties6,
                default=[],
                key="property_tab6"
            )

        with col_prop06:
            selected_property06 = st.multiselect(
                "Filter by Payee",
                options=properties06,
                default=[],
                key="property_tab06"
            )
    
        with col_region6:
            selected_region6 = st.multiselect(
                "Filter by Region",
                options=region6,
                default=[],
                key="region_tab6"
            )   

        with col_gl6:
            selected_gl6 = st.multiselect(
                "Filter by GL Account",
                options=gl_accounts6,
                default=[],
                key="gl_tab6"
            )

        if selected_property6:
            bill = bill[bill["Property Name"].isin(selected_property6)]
            bill1 = bill1[bill1["Property Name"].isin(selected_property6)]

        if selected_property06:
            bill = bill[bill["Payee Name"].isin(selected_property06)]
            bill1 = bill1[bill1["Payee Name"].isin(selected_property06)]

        if selected_region6:
            bill = bill[bill["Region"].isin(selected_region6)]
            bill1 = bill1[bill1["Region"].isin(selected_region6)]

        if selected_gl6:
            bill = bill[bill["GL Account Name"].isin(selected_gl6)]
            bill1 = bill1[bill1["GL Account Name"].isin(selected_gl6)]

        
        

        col65 = st.columns(1)[0]

        with col65:

            bill['Bill Date'] = pd.to_datetime(bill['Bill Date'], errors='coerce')
            bill['Month'] = bill['Bill Date'].dt.to_period("M").astype(str)

            bill['Paid'] = bill['Paid'].astype(str).str.replace(r'[$,]', '', regex=True)
            bill['Unpaid'] = bill['Unpaid'].astype(str).str.replace(r'[$,]', '', regex=True)
            bill['Paid'] = pd.to_numeric(bill['Paid'], errors='coerce').fillna(0)
            bill['Unpaid'] = pd.to_numeric(bill['Unpaid'], errors='coerce').fillna(0)

            # Normalize Approval Status
            bill['Approval Status'] = bill['Approval Status'].fillna("Unapproved")
            bill['Approval Status'] = bill['Approval Status'].str.strip().str.lower()

            # Create flags
            bill['Is_Approved'] = bill['Approval Status'].str.contains("approved", case=False, na=False)

            # Split unpaid amounts
            bill['Unpaid_Approved'] = bill.apply(lambda row: row['Unpaid'] if row['Is_Approved'] else 0, axis=1)
            bill['Unpaid_Unapproved'] = bill.apply(lambda row: row['Unpaid'] if not row['Is_Approved'] else 0, axis=1)

            # Group by month
            monthly_summary = bill.groupby('Month').agg({
                'Paid': 'sum',
                'Unpaid_Approved': 'sum',
                'Unpaid_Unapproved': 'sum',
                'Reference': 'nunique'
            }).reset_index().sort_values('Month')

            monthly_summary['Total Amount'] = (
                monthly_summary['Paid'] + monthly_summary['Unpaid_Approved'] + monthly_summary['Unpaid_Unapproved']
            )

            # Create figure
            fig = go.Figure()

            # Paid
            fig.add_trace(go.Bar(
                x=monthly_summary['Month'],
                y=monthly_summary['Paid'],
                name='Paid',
                marker_color='mediumseagreen',
                text=monthly_summary['Paid'].map('${:,.0f}'.format),
                textposition='inside'
            ))

            # Unpaid - Approved
            fig.add_trace(go.Bar(
                x=monthly_summary['Month'],
                y=monthly_summary['Unpaid_Approved'],
                name='Unpaid - Approved',
                marker_color='indianred',
                text=monthly_summary['Unpaid_Approved'].map('${:,.0f}'.format),
                textposition='inside'
            ))

            # Unpaid - Unapproved
            fig.add_trace(go.Bar(
                x=monthly_summary['Month'],
                y=monthly_summary['Unpaid_Unapproved'],
                name='Unpaid - Unapproved',
                marker_color='orange',
                text=monthly_summary['Unpaid_Unapproved'].map('${:,.0f}'.format),
                textposition='inside'
            ))

            # Reference count (secondary axis)
            fig.add_trace(go.Scatter(
                x=monthly_summary['Month'],
                y=monthly_summary['Reference'],
                name='Reference Count',
                yaxis='y2',
                mode='lines+markers+text',
                line=dict(color='gray', width=3),
                marker=dict(size=8),
            ))

            # Total label on top
            fig.add_trace(go.Scatter(
                x=monthly_summary['Month'],
                y=monthly_summary['Total Amount'] + 250,
                mode='text',
                text=monthly_summary['Total Amount'].map('${:,.0f}'.format),
                textposition='top center',
                textfont=dict(size=12, color="mediumseagreen", family="Arial Black"),
                showlegend=False
            ))

            # Layout
            fig.update_layout(
                barmode='stack',
                title='💸 Paid vs Unpaid Amounts by Month (Split by Approval)',
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

            st.plotly_chart(fig, use_container_width=True)
        
        col66 = st.columns(1)[0]
        col67 = st.columns(1)[0]
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

        with col67:
            # Clean and prepare columns
            bill['Paid'] = pd.to_numeric(bill['Paid'], errors='coerce').fillna(0)
            bill['Unpaid'] = pd.to_numeric(bill['Unpaid'], errors='coerce').fillna(0)
            bill['Approval Status'] = bill['Approval Status'].fillna("Unapproved").str.strip().str.lower()
            bill['Payee Name'] = bill['Payee Name'].fillna("Unknown")

            # Create boolean flag for approval
            bill['Is_Approved'] = bill['Approval Status'].str.contains("approved", case=False, na=False)

            # Split unpaid
            bill['Unpaid_Approved'] = bill.apply(lambda row: row['Unpaid'] if row['Is_Approved'] else 0, axis=1)
            bill['Unpaid_Unapproved'] = bill.apply(lambda row: row['Unpaid'] if not row['Is_Approved'] else 0, axis=1)

            # Group by vendor
            summary = (
                bill.groupby('Payee Name')
                .agg({
                    'Paid': 'sum',
                    'Unpaid_Approved': 'sum',
                    'Unpaid_Unapproved': 'sum',
                    'Reference': 'nunique'
                })
                .reset_index()
            )

            summary['Unpaid_Total'] = summary['Unpaid_Approved'] + summary['Unpaid_Unapproved']
            summary['Total_Activity'] = summary['Unpaid_Total'] + summary['Paid']
            top_vendors = summary.sort_values('Unpaid_Total', ascending=False).head(10)

            # Plot
            fig = go.Figure()

            # Bar: Paid
            fig.add_trace(go.Bar(
                x=top_vendors['Payee Name'],
                y=top_vendors['Paid'],
                name='Paid',
                marker_color='mediumseagreen',
                offsetgroup=0,
                text=top_vendors['Paid'].map('${:,.0f}'.format),
                textposition='auto'
            ))

            # Bar: Unpaid - Approved
            fig.add_trace(go.Bar(
                x=top_vendors['Payee Name'],
                y=top_vendors['Unpaid_Approved'],
                name='Unpaid - Approved',
                marker_color='indianred',
                offsetgroup=1,
                base=0,
                text=top_vendors['Unpaid_Approved'].map('${:,.0f}'.format),
                textposition='inside'
            ))

            # Bar: Unpaid - Unapproved (stacked on approved)
            fig.add_trace(go.Bar(
                x=top_vendors['Payee Name'],
                y=top_vendors['Unpaid_Unapproved'],
                name='Unpaid - Unapproved',
                marker_color='orange',
                offsetgroup=1,
                base=top_vendors['Unpaid_Approved'],
                text=top_vendors['Unpaid_Unapproved'].map('${:,.0f}'.format),
                textposition='inside'
            ))

            # Line: Reference Count
            fig.add_trace(go.Scatter(
                x=top_vendors['Payee Name'],
                y=top_vendors['Reference'],
                name='Reference Count',
                yaxis='y2',
                mode='lines+markers+text',
                text=top_vendors['Reference'],
                textposition='top center',
                line=dict(color='blue', width=2),
                marker=dict(size=8),
            ))

            # Layout
            fig.update_layout(
                title="💵 Paid vs Unpaid by Vendor (Stacked) + Reference Count",
                xaxis_title="Vendor",
                yaxis=dict(title="Amount ($)", tickformat="$.2s"),
                yaxis2=dict(
                    title="Reference Count",
                    overlaying='y',
                    side='right',
                    showgrid=False
                ),
                barmode='relative',
                bargap=0.35,
                legend_title="Category",
                xaxis_tickangle=-45,
                width=1100,
                height=600,
                hovermode="x unified"
            )

            st.plotly_chart(fig, use_container_width=True)




        with tab1:
            st.subheader("🏠 Property Performance")
            st.write(rent_roll1)

        with tab2:
            st.subheader("💰 Rent")
            st.write(rent_roll2)

        with tab3:
            st.subheader("📝 Leasing")
            st.write(df_guest1)
         
        with tab4:
            st.subheader("🔧 Maintenance")
            st.write(df_work1)
        
        with tab5:
            st.subheader("🏢 Tenants")
            st.write(tenant_data1)

        with tab6:
            st.subheader("📄 Billings")
            st.write(bill1)

    st.markdown(
        """
       <div style="text-align: center; font-size: 0.9rem; color: #4a4a4a;">
        Copyright © 2025 <a href="https://zuckermanautomationgroup.com" target="_blank">zuckermanautomationgroup.com</a> |
        Powered by Zuckerman Automation Group
    </div>
        """,
        unsafe_allow_html=True
    )    

# if __name__ == "__main__":
#     show_dashboard()
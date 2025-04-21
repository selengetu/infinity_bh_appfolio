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

st.set_page_config(page_title="Appfolio Dashboards", layout="wide")

def show_dashboard():
    
    BASE_DIR = os.path.join(os.getcwd(), "data")  # Use relative path
    IMG_DIR = "plotly_pdf_images"
    st.title("📊 Appfolio Dashboards")
    # Define file prefixes
    file_prefixes = {
        "Tenant Data": "tenant_data_cleaned",
        "Work Orders": "work_order_cleaned",
        "Prospect": "prospect_cleaned",
        "Rent Roll": "rentroll_cleaned",
        "Leasing": "leasing_cleaned",
        "Purchase Order": "purchase_order_cleaned",
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
        col1, col2, col3, col4 = st.columns(4)

        all_units = dfs["Rent Roll"].shape[0]
        current_resident = dfs["Rent Roll"][dfs["Rent Roll"]["Status"] == "Current"].shape[0]
        notice = dfs["Rent Roll"][dfs["Rent Roll"]["Status"] == "Notice-Unrented"].shape[0]
        notice_re = dfs["Rent Roll"][dfs["Rent Roll"]["Status"] == "Notice-Rented"].shape[0]
        evict = dfs["Rent Roll"][dfs["Rent Roll"]["Status"] == "Evict"].shape[0]
        occupied = ((current_resident+evict+notice+notice_re) / all_units) * 100
        dfs["Rent Roll"]["Rent"] = dfs["Tenant Data"]["Rent"].replace("[\$,]", "", regex=True)  # Remove $ and ,
        dfs["Rent Roll"]["Rent"] = pd.to_numeric(dfs["Tenant Data"]["Rent"], errors="coerce")  # Convert to number
        total_rent = dfs["Rent Roll"]["Rent"].sum()
        total_move_out = dfs["Rent Roll"]["Move-out"].notnull().sum()
        # Display the metric card
        col1.metric(label="🏠Total Unit", value=f"{all_units}")
        col2.metric(label="📊 Occupancy Rate",  value=f"{occupied:.2f}%")
        col3.metric(label="💵 Total Rent ",value=f"${(total_rent):,.0f}")
        col4.metric(label="🚪Total Move-outs (Next 60 days)", value=f"{total_move_out}")

        col5, col6 = st.columns(2)
        
        with col5:

            trailing_12months = dfs["Rent Roll 12 Months"]  
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

            trailing_12months = dfs["Rent Roll 12 Months"]  
            trailing_12months['date_str'] = pd.to_datetime(trailing_12months['date_str'], format='%m-%d-%Y')
            trailing_12months = trailing_12months.sort_values(by='date_str')
            summary = []
            for date, group in trailing_12months.groupby('date_str'):
                total = len(group)
                current = group[group['Status'] == 'Vacant-Rented'].shape[0]
                notice = group[group['Status'] == 'Vacant-Unrented'].shape[0]
                vacant = current +evict+ notice_un+notice

                summary.append({
                    "Month": date.strftime("%b %Y"),
                    "Occupancy %": vacant,
                    "Total Units": total
                })

            df_occ = pd.DataFrame(summary)

            fig = go.Figure()

            # Bar: Occupancy %
            fig.add_trace(
                go.Bar(
                    x=df_occ["Month"],
                    y=df_occ["Occupancy %"],
                    name="Occupancy %",
                    marker=dict(color=df_occ["Occupancy %"], colorscale="Blues"),
                    text=df_occ["Occupancy %"],
                    textposition="auto"
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
            
        col7, col8 = st.columns(2)

        # Use col2 and col5 for two separate charts
        with col7:
                # Ensure Rent and Market Rent are numeric
            dfs["Tenant Data"]["Rent"] = pd.to_numeric(dfs["Tenant Data"]["Rent"], errors="coerce")

          

        with col8:
            # Ensure "Status" column exists
            if "Status" in dfs["Tenant Data"].columns:
                status_counts = dfs["Tenant Data"]["Status"].value_counts().reset_index()
                status_counts.columns = ["Status", "Count"]

                # **Create Pie Chart**
                fig4 = px.pie(status_counts, 
                values="Count", 
                names="Status", 
                title="🏠 Tenant Status Distribution", 
                hole=0.4,  # Creates a donut-style pie chart
                color_discrete_sequence=px.colors.qualitative.Set3)  # Custom colors

                # 🔹 Improve Layout & Style
                fig4.update_layout(
                    width=800, height=600,  # Bigger chart
                )

                # 🔹 Customize Legend
                fig4.update_layout(
                    legend=dict(
                        font=dict(size=14),  # Bigger font for legend
                        x=1, y=0.9,  # Position legend to the right
                        xanchor="right"
                    )
                )

                # 🔹 Show Percentages & Labels
                fig4.update_traces(
                    textinfo="percent+label",  # Display both labels and percentages
                    pull=[0.1 if i == 0 else 0 for i in range(len(status_counts))],  # Slightly pull out the first slice

                )   

                # Display the Pie Chart
                st.plotly_chart(fig4, use_container_width=True)
                img_path4 = os.path.join(IMG_DIR, "status.png")
                fig4.write_image(img_path4)
    
            else:
                st.warning("⚠️ 'Status' column not found in dataset.")

        col9 = st.columns(1)[0] 

        # Use col2 and col5 for two separate charts
        with col9:
            pass

    with tab2:
        col21, col22, col23, col24 = st.columns(4)
        

        # Display the metric card
        col21.metric(label="🛠️ Total work order", value="")
        col22.metric(label="🆕New work orders", value="")
        col23.metric(label="⚠️Urgent work order ", value="")
        col24.metric(label="💰Total Amounts", value="")

        col26, col27 = st.columns(2)

        # Use col2 and col5 for two separate charts
            
        with col26:

            pass
        with col27:
            pass

    with tab3:
        col31, col32, col33, col34 = st.columns(4)


            # **Display Metric Cards**
        col31.metric(label="🏠 Total Vacancy", value="")
        col32.metric(label="✅ Rent Ready Units", value="")
        col33.metric(label="🆕 Upcoming Move In", value="")
        col34.metric(label="📉 Avg Days Vacant", value="")

            # **Create Another Row for More Metrics**
        col36, col37 = st.columns(2)

        with col36:
           pass

        with col37:
        
           pass

        col38, col39 = st.columns(2)

        # Use col2 and col5 for two separate charts
            
        with col38:
            pass
        
        
        with col39:
            today = pd.Timestamp.today()


        with tab1:
            st.subheader("🏠 Property Performance")
            st.write(dfs["Rent Roll"])

        with tab2:
            st.subheader("💰 Rent")
            st.write(dfs["Rent Roll"])

        with tab3:
            st.subheader("📝 Leasing")
            st.write(dfs["Leasing"])
         
        with tab4:
            st.subheader("🔧 Maintenance")
            st.write(dfs["Work Orders"])
        
        with tab5:
            st.subheader("🏢 Tenants")
            st.write(dfs["Tenant Data"])

        with tab6:
            st.subheader("📄 Billings")
            st.write(dfs["Purchase Order"])
       
# if __name__ == "__main__":
#     show_dashboard()


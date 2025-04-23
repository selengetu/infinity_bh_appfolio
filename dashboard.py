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
        dfs["Rent Roll"]["Rent"] = dfs["Rent Roll"]["Rent"].replace("[\$,]", "", regex=True)  # Remove $ and ,
        dfs["Rent Roll"]["Rent"] = pd.to_numeric(dfs["Rent Roll"]["Rent"], errors="coerce")  # Convert to number
        dfs["Rent Roll"]["Market Rent"] = dfs["Rent Roll"]["Market Rent"].replace("[\$,]", "", regex=True)  # Remove $ and ,
        dfs["Rent Roll"]["Market Rent"] = pd.to_numeric(dfs["Rent Roll"]["Market Rent"], errors="coerce")  # Convert to number
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

            rent_roll = dfs["Rent Roll"]
            # Filter only relevant statuses
            filtered = rent_roll[rent_roll["Status"].isin(statuses)]

            # Group by Unit Type and Status
            grouped = (
                filtered
                .groupby(["BD/BA", "Status"])
                .size()
                .reset_index(name="Count")
            )

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
                color_discrete_sequence=px.colors.qualitative.Set2,
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

        col9, col10 = st.columns(2)

        with col9:
            trailing_12months = dfs["Rent Roll 12 Months"]  
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

        with col10:
           

            df = dfs["Rent Roll"].copy()
            df['Move-out'] = pd.to_datetime(df['Move-out'], errors='coerce')

            today = datetime.today()

            def categorize_moveout_days(row):
                if pd.isna(row['Move-out']):
                    return None
                delta = (row['Move-out'] - today).days
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

                    # Apply the categorization
            df['Move Out Bucket'] = df.apply(lambda row: categorize_moveout_days(row), axis=1)

            # Group by Room Type and Move Out Bucket
            grouped = (
                df[df['Move Out Bucket'].notna()]
                .groupby(['BD/BA', 'Move Out Bucket'])
                .size()
                .reset_index(name='Count')
            )

            fig = px.bar(
                grouped,
                x="Move Out Bucket",
                y="Count",
                color="BD/BA",
                title="📦 Upcoming Move-Outs by Room Type",
                barmode="stack",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            fig.update_layout(
                xaxis_title="Move Out Timeframe",
                yaxis_title="Number of Units",
                legend_title="BD/BA",
                width=1000,
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)


        col11, col12 = st.columns(2)

        with col11:
            today = datetime.today()
            df = dfs["Rent Roll"].copy()
            
            df['Move-in'] = pd.to_datetime(df['Move-in'], errors='coerce')
            df['Move-out'] = pd.to_datetime(df['Move-out'], errors='coerce')

            df = df[df['Move-out'] >= today]
            # Extract Month-Year
            df['Move-in Month'] = df['Move-in'].dt.to_period("M").astype(str)
            df['Move-out Month'] = df['Move-out'].dt.to_period("M").astype(str)

            # Count Move-ins
            movein_counts = (
                df.groupby('Move-in Month').size().reset_index(name='Count')
                .rename(columns={'Move-in Month': 'Month'})
            )
            movein_counts['Type'] = 'Move-in'

            # Count Move-outs
            moveout_counts = (
                df.groupby('Move-out Month').size().reset_index(name='Count')
                .rename(columns={'Move-out Month': 'Month'})
            )
            moveout_counts['Type'] = 'Move-out'

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
                title="📈 Monthly Move-ins vs Move-outs",
                color_discrete_map={
                    "Move-in": "green",
                    "Move-out": "red"
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

        with col12:
            df = dfs["Rent Roll"].copy()
            df['Past Due'] = pd.to_numeric(df['Past Due'], errors='coerce').fillna(0)

            df_delinquent = df[df['Past Due'] > 0]

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
       
        col26, col27 = st.columns(2)

        # Use col2 and col5 for two separate charts
            
        with col26:
            dfs["Rent Roll"]["Rent"] = pd.to_numeric(dfs["Rent Roll"]["Rent"], errors="coerce")
            dfs["Rent Roll"]["Market Rent"] = pd.to_numeric(dfs["Rent Roll"]["Market Rent"], errors="coerce")

            # Drop invalid rows where Rent or Market Rent is NaN
            filtered_df = dfs["Rent Roll"].dropna(subset=["Rent", "Market Rent"])

            # Group by BD/BA and Calculate Avg Rent and Market Rent
            avg_rent_df = filtered_df.groupby("BD/BA")[["Rent", "Market Rent"]].mean().round(0).reset_index()

            # Count the number of units per BD/BA
            unit_count_df = filtered_df.groupby("BD/BA").size().reset_index(name="Unit Count")

            # Merge DataFrames to align BD/BA categories
            final_df = avg_rent_df.merge(unit_count_df, on="BD/BA")

            # Create figure with Bar Chart for Rent & Market Rent
            fig3 = go.Figure()

            # Add Rent bars
            fig3.add_trace(go.Bar(
                x=final_df["BD/BA"], 
                y=final_df["Rent"], 
                name="Avg Rent",
                marker_color="blue",
                text=final_df["Rent"], 
                textposition="auto"
            ))

            # Add Market Rent bars
            fig3.add_trace(go.Bar(
                x=final_df["BD/BA"], 
                y=final_df["Market Rent"], 
                name="Avg Market Rent",
                marker_color="green",
                text=final_df["Market Rent"], 
                textposition="auto"
            ))

            # Add Line Chart for Unit Count (Secondary Y-Axis)
            fig3.add_trace(go.Scatter(
                x=final_df["BD/BA"], 
                y=final_df["Unit Count"], 
                name="Unit Count",
                mode="lines+markers",
                yaxis="y2",
                line=dict(color="red", width=2),
                marker=dict(size=8, symbol="circle"),
            ))

            fig3.update_layout(
                title="📊 Avg Rent vs. Market Rent with Unit Count by BD/BA",
                xaxis=dict(
                    title=dict(text="Bedroom/Bathroom"), 
                    tickangle=-45, 
                    tickfont=dict(size=12)
                ),
                yaxis=dict(
                    title=dict(text="Amount ($)"), 
                    gridcolor="lightgray"
                ),
                yaxis2=dict(
                    title=dict(text="Unit Count"), 
                    overlaying="y", 
                    side="right", 
                    showgrid=False
                ),
                legend=dict(title=dict(text="Legend")),
                width=1000, height=600,
                bargap=0.15,  # Reduce gap between bars
                barmode="group"
            )
                    # Display in Streamlit
            st.plotly_chart(fig3, use_container_width=True)
        with col27:
            pass

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

        col38, col39 = st.columns(2)

        # Use col2 and col5 for two separate charts
            
        with col38:
            # Load your Work Orders table
            pass
                    
        
        with col39:
            pass

    with tab4:
      
        col45, col46 = st.columns(2)

        with col45:
            df_work = dfs["Work Orders"].copy()

            # Combine all job descriptions into one big string
            text = " ".join(str(desc) for desc in df_work['Job Description'].dropna())

            custom_stopwords = set(STOPWORDS)
            custom_stopwords.update([
                "unit", "please", "de", "la", "y", "need", "working"
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
            st.subheader("🛠️ Most Common Terms in Work Order Descriptions")

            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)

        with col46:
            df_work = dfs["Work Orders"].copy()

            # Use the correct column name for status (adjust if needed)
            status_col = "Status"  # or "Work Order Status"

            # Drop blanks and count by status
            status_counts = df_work[status_col].dropna().value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            # Create bar chart
            fig = px.bar(
                status_counts,
                x="Status",
                y="Count",
                title="🔧 Work Orders by Status",
                color="Status",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            fig.update_layout(
                xaxis_title="Work Order Status",
                yaxis_title="Number of Work Orders",
                showlegend=False,
                width=900,
                height=500
            )

            # Show in Streamlit
            st.plotly_chart(fig, use_container_width=True)



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
       
if __name__ == "__main__":
    show_dashboard()


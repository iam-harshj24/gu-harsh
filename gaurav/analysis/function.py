import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math 
import hashlib
import io




def read_sales_data(uploaded_file, sheet_name):
    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    id_cols = ['ASIN', 'Product Name']
    date_cols = [col for col in df.columns if col not in id_cols]
    melted_df = df.melt(id_vars=id_cols, value_vars=date_cols,
                        var_name='Date', value_name='Sales')
    melted_df['Date'] = pd.to_datetime(melted_df['Date'], format='%Y%m%d')
    return melted_df

def read_gross_profit(uploaded_file, sheet_name):
    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    id_cols = ['ASIN', 'Product Name']
    date_cols = [col for col in df.columns if col not in id_cols]
    melted_df = df.melt(id_vars=id_cols, value_vars=date_cols,
                        var_name='Date', value_name='Gross Profit')
    melted_df['Date'] = pd.to_datetime(melted_df['Date'], format='%Y%m%d')
    return melted_df

def merge_sales_and_profit(sales_data, profit_data):
    df = pd.merge(sales_data, profit_data, on=['ASIN', 'Date', 'Product Name'], how='inner')
    df.to_csv("merged_data.csv")
    return df

def read_inventory_data(uploaded_file, sheet_name):
    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
    base_cols = ['ASIN', 'Product Name', 'Current inventory']
    date_columns = [col for col in df.columns if col not in base_cols]
    df['Upcoming Inventory'] = df[date_columns].sum(axis=1)
    df['Total Inventory'] = df['Current inventory'] + df['Upcoming Inventory']
    df = df[base_cols + date_columns + ['Upcoming Inventory', 'Total Inventory']]
    df.to_csv('inventory_data.csv')
    return df

# def calculate_normal_drr(merged_data, use_manual_drr=False, manual_drr_value=None):
#     df = merged_data.sort_values(['ASIN', 'Date'])
    
#     if use_manual_drr and manual_drr_value is not None:
#         # Use the single manual DRR value for all ASINs
#         df['Daily_Run_Rate'] = manual_drr_value
#     else:
#         # Calculate DRR normally
#         df['Daily_Run_Rate'] = df.groupby('ASIN')['Sales'].transform(
#             lambda x: x.rolling(window=5, min_periods=1).mean()
#         )
        
#     return df.round()


def calculate_normal_drr(merged_data, use_manual_drr=False, manual_drr_value=None):
    df = merged_data.sort_values(['ASIN', 'Date'])
    
    if use_manual_drr and manual_drr_value is not None:
        # Use the single manual DRR value for all ASINs
        df['Daily_Run_Rate'] = manual_drr_value
    else:
        # Calculate DRR normally
        df['Daily_Run_Rate'] = df.groupby('ASIN')['Sales'].transform(
            lambda x: x.rolling(window=5, min_periods=1).mean()
        )


    # Create lists of products if not already defined
    top_products = [
        "B09VPLLPMB", "B071LQFHPY", "B072M2MTK1", "B09W2VSN54", "B09W9SX1W8",
        "B09TXNSQDJ", "B07GNLN5K2", "B07YWWXLJS", "B071ZQ5J4X", "B09WZYCXRQ",
        "B07J14W55P", "B07Q4TD8RS", "B07J1JZJY2", "B09VS77ZDT", "B071ZMQ3X8",
        "B072PYW2VM", "B078Z17WQ9", "B07MCKSNZQ", "B0B8HDYRZQ", "B09W28G7L3",
        "B07895B2VZ", "B07895DHYQ", "B071W92ZRG", "B07GCQDX6M", "B07MV28C29",
        "B07FSYZM6H", "B072Q32KJ2", "B07Y1LCD7T", "B07FSZ921M", "B0BY54K6C3"
    ]

    mid_section_products = [
        "B071J8GQCJ", "B07W8THF1Q", "B0788XRBJ5", "B0BB9QN29D", "B0788WTFPY",
        "B071FNLVF5", "B078Z2KPT5", "B07J1L77D3", "B072M55KZT", "B07FSV4FNK",
        "B07M9QQ8XL", "B086X1WC4N", "B0789JGL72", "B0788X172Q", "B09W2KHTWX",
        "B07M7VQ1N1", "B072Q1NW1T", "B09V1FGQ8Z", "B07J1WMHT2", "B07GCPD2DR",
        "B07M7WL2HD", "B09V7XXJ52", "B07J1DS78L", "B072Q22P7Q", "B079G5H8XP",
        "B081RJL36N", "B07BY4KRKN", "B07QZ4138D", "B07YYCLVGQ", "B07J1K4B3R",
        "B07MT9CY7B", "B07N8XR8C4", "B07MGXBWB"
    ]

    # Create a conditions list for numpy.select
    conditions = [
        df['ASIN'].isin(top_products),
        df['ASIN'].isin(mid_section_products)
    ]

    # Create corresponding multipliers
    multipliers = [1.20, 1.15]  # 20% increase for top, 10% for mid

    # Default multiplier is 1.0 (no change) for bottom products
    df['Target_DRR'] = (df['Daily_Run_Rate'] *
                       np.select(conditions, multipliers, default=1.10)).round()
    df.to_csv('drr_data.csv')
    return df.round()

def shipment_inventory_status(inventory_data, drr_data):
    df1 = inventory_data
    df2 = drr_data

    df = pd.merge(df1, df2, on=['ASIN', 'Product Name'], how='inner')
    df = df.drop(columns=['Upcoming Inventory', 'Total Inventory', 'Sales', 'Gross Profit'], errors='ignore')

    def format_column(column):
        if isinstance(column, datetime):
            return column.strftime("%d-%m-%Y")
        return str(column)

    df.columns = [format_column(col) for col in df.columns]
    shipment_columns = [col for col in df.columns if '-' in col and col != 'Date']

    if not shipment_columns:
        raise ValueError("No shipment date columns detected. Ensure headers are in 'DD-MM-YYYY' format.")

    df[shipment_columns] = df[shipment_columns].fillna(0)

    if "Current inventory" in df.columns:
        df["Current inventory"] = df["Current inventory"].fillna(0)
    else:
        raise ValueError("Missing 'Current inventory' column in the data.")

    if "Daily_Run_Rate" in df.columns:
        df["Daily_Run_Rate"] = df["Daily_Run_Rate"].fillna(0)
    else:
        raise ValueError("Missing 'Daily_Run_Rate' column in the data.")

    def get_inventory_status(days):
        if pd.isna(days) or days == float('inf'):
            return 'No Sales Data'
        elif days <= 20:
            return 'In AIR'
        elif days <= 60:
            return 'Expected to be in air'
        elif days <= 80:
            return 'Sea Shipment'
        elif days <= 100:
            return 'Planned to send in Next Sea Shipment'
        else:
            return 'Sufficient Inventory'

    results = []
    for index, row in df.iterrows():
        shipment_quantities = row[shipment_columns].tolist()
        current_date = datetime.today()
        original_inventory = row["Current inventory"]
        updated_inventory = original_inventory

        for i, shipment_date in enumerate(shipment_columns):
            shipment_date = datetime.strptime(shipment_date, "%d-%m-%Y")
            if shipment_date <= current_date:
                updated_inventory += shipment_quantities[i]
        

        Daily_Run_Rate = row["Daily_Run_Rate"]

        if Daily_Run_Rate == 0:
            out_of_stock_date = "N/A (No consumption rate)"
            expected_date_to_be_in_air = "N/A"
            days_survived = float('inf')
        else:
            out_of_stock_date, expected_date_to_be_in_air = None, None

            for i, shipment_date in enumerate(shipment_columns):
                shipment_date = datetime.strptime(shipment_date, "%d-%m-%Y")
                if shipment_date < current_date:
                    continue
                days_to_next_shipment = (shipment_date - current_date).days
                inventory_needed = days_to_next_shipment * Daily_Run_Rate

                if updated_inventory >= inventory_needed:
                    updated_inventory -= inventory_needed
                    current_date = shipment_date
                    updated_inventory += shipment_quantities[i]
                else:
                    days_survived = updated_inventory // Daily_Run_Rate
                    out_of_stock_date = current_date + timedelta(days=days_survived)
                    break

            if not out_of_stock_date:
                days_survived_after_last_shipment = int(updated_inventory // Daily_Run_Rate)
                out_of_stock_date = current_date + timedelta(days=days_survived_after_last_shipment)

            if out_of_stock_date != "N/A (No consumption rate)":
                expected_date_to_be_in_air = out_of_stock_date - timedelta(days=20)

        inventory_status = get_inventory_status(
            (out_of_stock_date - datetime.today()).days if isinstance(out_of_stock_date, datetime) else float('inf'))

        total_upcoming_shipment = original_inventory + sum(shipment_quantities)

        results.append({
            'Date': row['Date'],
            'ASIN': row['ASIN'],
            'Product Name': row['Product Name'],
            'Current Inventory': row["Current inventory"],
            'Updated Current Inventory': updated_inventory,
            'Daily_Run_Rate': Daily_Run_Rate,
            # 'Target_DRR':row['Target_DRR'],
            'Date of OOS': out_of_stock_date.strftime("%d-%m-%Y") if isinstance(out_of_stock_date, datetime) else out_of_stock_date,
            'Expected Date to be in Air': expected_date_to_be_in_air.strftime("%d-%m-%Y") if isinstance(expected_date_to_be_in_air, datetime) else expected_date_to_be_in_air,
            'Days of inventory': (out_of_stock_date - datetime.today()).days if isinstance(out_of_stock_date, datetime) else "N/A",
            'Inventory Status': inventory_status,
            'Total Upcoming Shipment': total_upcoming_shipment  # New column added
        })

    results_df = pd.DataFrame(results)
    results_df.to_csv('inventory_status_with_updated_inventory_and_total_shipment.csv', index=False)
    print("Results saved to inventory_status_with_updated_inventory_and_total_shipment.csv")

    return results_df



def calculate_shipment_plan(inventory_status, target_date, current_date=None):
    if current_date is None:
        current_date = datetime.now()

    target_date = pd.to_datetime(target_date)
    current_date = pd.to_datetime(current_date)
    result = inventory_status.copy()

    # date_columns = [col for col in result.columns if isinstance(col, datetime)]
    # drr_column = 'Daily_Retail_Rate_Deal' if is_deal_day else 'Daily_Retail_Rate'

    days_until_target = (target_date - current_date).days
    result['Days_To_Target'] = int(days_until_target+1)
    result['Expected_Usage'] = (result['Daily_Run_Rate'] * result['Days_To_Target']).round()

    # future_shipment_cols = [col for col in date_columns if col<= target_date]
    # result['Total Upcoming Shipments'] = result[future_shipment_cols].sum(axis=1) if future_shipment_cols else 0

    result['Total_Available'] = result['Total Upcoming Shipment']
    result['Required Projected Inventory'] = (
        result['Expected_Usage']-result['Total_Available']
    ).round()

    result['Buffer_Stock'] = (result['Daily_Run_Rate'] * 15).round()

    result['Required_Shipment_with_buffer_stock'] = (
        result['Buffer_Stock'] + result['Required Projected Inventory'])
          
    

    # def get_shipment_priority(row):
    #     if row['Status'] == 'No Sales Data':
    #         return 'No Priority - No Sales Data'
    #     elif row['Status'] == 'Urgent Restock':
    #         return 'High - Stockout Expected(IN AIR)'
    #     elif row['Status'] == 'Restock Soon':
    #         return 'Medium - Expected to be in air'
    #     elif row['Status'] == 'Send stocks in Next Shipment':
    #         return 'Medium - Plan for Sea Shipment'
    #     else:
    #         return 'Low - Sufficient Stock'



    # result['Shipment_Priority'] = result.apply(get_shipment_priority, axis=1)
    # result['Estimated_Arrival'] = target_date + timedelta(days=65)


    result.to_csv('shipment_details.csv')
    return result

def calculate_benchmarks(sales_data, profit_data, date_columns_2025):
    """Calculate benchmark metrics from top 5 sales days."""
    def get_highest_ratio_from_top_5(row):
        sales_series = sales_data.loc[row.name, date_columns_2025]
        sorted_sales = sales_series.sort_values(ascending=False).dropna().head(5)
        top_dates = list(sorted_sales.index)
        top_sales = list(sorted_sales.values)
        
        profits_series = profit_data.loc[row.name, top_dates]
        top_profits = list(profits_series.values)
        
        top_ratios = [p / s if s != 0 else 0 for p, s in zip(top_profits, top_sales)]
        
        if top_ratios:
            max_ratio_index = top_ratios.index(max(top_ratios))
            return (top_dates[max_ratio_index], top_sales[max_ratio_index],
                   top_profits[max_ratio_index], top_ratios[max_ratio_index])
        return None, None, None, None

    benchmark_data = pd.DataFrame(index=sales_data.index)
    (benchmark_data["BenchMark_Date"], benchmark_data["BM Sales"],
     benchmark_data["BM Profit"], benchmark_data["Max(Profit/Unit)"]) = zip(
        *sales_data.apply(get_highest_ratio_from_top_5, axis=1)
    )
    
    return benchmark_data

def Performance_Tracker(uploaded_file, sales_sheet="Sales", profit_sheet="Profit", tracker_sheet="Tracker"):
    """
    Function to calculate and display average sales, profit, and DRR based on a selected date range,
    week-over-week analysis, or week-by-year analysis.
    """
    try:
        # Read sales, profit, and tracker data
        sales_data = pd.read_excel(uploaded_file, sheet_name=sales_sheet)
        profit_data = pd.read_excel(uploaded_file, sheet_name=profit_sheet)
        tracker_data = pd.read_excel(uploaded_file, sheet_name=tracker_sheet)

        # Ensure necessary columns exist
        if not {'ASIN', 'Product Name'}.issubset(sales_data.columns) or not {'ASIN', 'Product Name'}.issubset(profit_data.columns):
            st.error("Missing 'ASIN' or 'Product Name' columns in the dataset.")
            return

        # Identify date columns dynamically
        date_columns_sales = [col for col in sales_data.columns if col not in ['ASIN', 'Product Name']]
        date_columns_profit = [col for col in profit_data.columns if col not in ['ASIN', 'Product Name']]

        # Extract 2025 date columns
        date_mapping = {col: pd.to_datetime(col, errors='coerce') for col in date_columns_sales}
        date_columns_2025 = [col for col, date in date_mapping.items() if pd.notna(date) and date.year == 2025]

        # Sort dates
        sorted_dates = sorted(date_mapping.items(), key=lambda x: x[1])

        # Group dates into weeks by year
        week_groups = {}
        for col, date in sorted_dates:
            if pd.notna(date):
                year, week_num = date.year, date.isocalendar()[1]
                week_label = f"Week {week_num} ({year})"
                if week_label not in week_groups:
                    week_groups[week_label] = []
                week_groups[week_label].append(col)

        # Add 'Custom' option
        week_options = list(week_groups.keys()) + ["Custom"]
        selected_option = st.selectbox("📅 Select Date Range", week_options)

        if selected_option == "Custom":
            # Custom Date Selection
            col1, col2 = st.columns(2)
            sorted_dates_str = [str(date.date()) for _, date in sorted_dates if pd.notna(date)]
            start_date = col1.selectbox("📅 Select Start Date", sorted_dates_str)
            end_date = col2.selectbox("📅 Select End Date", sorted_dates_str, index=len(sorted_dates_str) - 1)

            # Convert user-selected dates back to column format
            selected_dates_sales = [col for col, date in sorted_dates if str(date.date()) >= start_date and str(date.date()) <= end_date]
        else:
            # Week-based selection
            selected_dates_sales = week_groups[selected_option]

        selected_dates_profit = selected_dates_sales

        # Convert selected date columns to numeric
        sales_data[selected_dates_sales] = sales_data[selected_dates_sales].apply(pd.to_numeric, errors='coerce')
        profit_data[selected_dates_profit] = profit_data[selected_dates_profit].apply(pd.to_numeric, errors='coerce')

        # Calculate average sales & profit for selected date range
        sales_data["Average Sales"] = sales_data[selected_dates_sales].mean(axis=1)
        profit_data["Total Profit"] = profit_data[selected_dates_profit].sum(axis=1)
        profit_data["Average Profit"] = profit_data[selected_dates_profit].mean(axis=1)

        # Merge sales and profit on ASIN & Product Name
        Pre_final_data = sales_data[['ASIN', 'Product Name', 'Average Sales']].merge(
            profit_data[['ASIN', 'Product Name', "Total Profit", 'Average Profit']],
            on=['ASIN', 'Product Name'],
            how='inner'
        )

        final_data = Pre_final_data[['ASIN', 'Product Name', 'Average Sales', "Total Profit", 'Average Profit']].merge(
            tracker_data[['ASIN', 'Product Name', 'Target DRR']],
            on=['ASIN', 'Product Name'],
            how='inner'
        )

        # Compute performance status
        final_data["Performance Status"] = np.where(
            final_data["Target DRR"] < final_data["Average Sales"], "Leading ✅", "Lagging ⚠️"
        )

        # **Integrate Benchmark Calculation**
        benchmark_data = calculate_benchmarks(sales_data, profit_data, date_columns_2025)
        final_data = final_data.merge(benchmark_data, left_index=True, right_index=True, how='left')

        # Display results in Streamlit
        num_days = len(selected_dates_sales)
        st.write(f"### 📊 Performance & Benchmarks ({selected_option} - {num_days} Days)")
        st.dataframe(final_data)

        # **Download Option**
        csv = final_data.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV 📥", csv, "Performance_Report.csv", "text/csv")

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.exception(e)
        
        
def process_data(uploaded_file, sales_sheet="Sales", profit_sheet="Profit", tracker_sheet="Tracker"):
    """Process Excel data and calculate metrics"""
    try:
        sales_data = pd.read_excel(uploaded_file, sheet_name=sales_sheet)
        profit_data = pd.read_excel(uploaded_file, sheet_name=profit_sheet)
        tracker_data = pd.read_excel(uploaded_file, sheet_name=tracker_sheet)
        
        required_columns = {'ASIN', 'Product Name'}
        if not required_columns.issubset(sales_data.columns) or not required_columns.issubset(profit_data.columns):
            st.error("Missing required columns 'ASIN' or 'Product Name' in the dataset.")
            return None
        
        date_columns_sales = [col for col in sales_data.columns if col not in required_columns]
        date_mapping = {col: pd.to_datetime(col, errors='coerce') for col in date_columns_sales}
        sorted_dates = sorted(date_mapping.items(), key=lambda x: x[1])
        date_columns_2025 = [col for col, date in date_mapping.items() if pd.notna(date) and date.year == 2025]
        
        week_groups = {}
        for col, date in sorted_dates:
            if pd.notna(date):
                year, week_num = date.year, date.isocalendar()[1]
                week_label = f"Week {week_num} ({year})"
                week_groups.setdefault(week_label, []).append(col)
        
        toggle_option = st.toggle("Enable Week-wise Selection", value=False)
        
        if toggle_option:
            week_options = list(week_groups.keys())
            selected_option = st.selectbox("📅 Select Week", week_options)
            selected_dates_sales = week_groups[selected_option]
        else:
            sorted_dates_str = [str(date.date()) for _, date in sorted_dates if pd.notna(date)]
            start_date = st.selectbox("📅 Select Start Date", sorted_dates_str, index=max(len(sorted_dates_str) - 1,0))
            end_date = st.selectbox("📅 Select End Date", sorted_dates_str, index=len(sorted_dates_str) - 1)
            selected_dates_sales = [col for col, date in sorted_dates if start_date <= str(date.date()) <= end_date]
        
        selected_dates_profit = selected_dates_sales
        sales_data[selected_dates_sales] = sales_data[selected_dates_sales].apply(pd.to_numeric, errors='coerce')
        profit_data[selected_dates_profit] = profit_data[selected_dates_profit].apply(pd.to_numeric, errors='coerce')
        
        sales_data["Sales(Units)"] = sales_data[selected_dates_sales].mean(axis=1)
        profit_data["Profit"] = profit_data[selected_dates_profit].mean(axis=1)
        
        final_data = sales_data[['ASIN', 'Product Name', 'Sales(Units)']].merge(
            profit_data[['ASIN', 'Product Name', 'Profit']],
            on=['ASIN', 'Product Name'], how='inner'
        ).merge(
            tracker_data[['ASIN', 'Product Name', 'Target DRR', 'Ad Spend','Revenue','Undercontrol']],
            on=['ASIN', 'Product Name'], how='inner'
        )
        
        final_data["Performance Status"] = np.where(
            final_data["Target DRR"] < final_data["Sales(Units)"], "Leading ✅", "Lagging ⚠️"
        )
        
        final_data["Sales(Units)"] = final_data["Sales(Units)"].round(2)
        final_data["Profit"] = final_data["Profit"].round(2)
        final_data['Profit/Unit'] = final_data["Profit"]/final_data["Sales(Units)"]

        benchmark_data = calculate_benchmarks(sales_data, profit_data, date_columns_2025)
        final_data = final_data.merge(benchmark_data, left_index=True, right_index=True, how='left')
        
        num_days = len(selected_dates_sales)
        st.write(f"### 📊 Performance & Benchmarks ({num_days} Days)")
        
        st.subheader("Filter Data")
        performance_filter = st.multiselect("Filter by Performance Status", 
                                          options=final_data["Performance Status"].unique())
        
        filtered_data = final_data.copy()
        if performance_filter:
            filtered_data = filtered_data[filtered_data["Performance Status"].isin(performance_filter)]
        
        st.subheader("Performance Data")
        st.dataframe(filtered_data)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            filtered_data.to_excel(writer, sheet_name='Performance_Data', index=False)
        
        excel_buffer.seek(0)
        st.download_button("Download Excel 📥", excel_buffer, 
                          "Performance_Report.xlsx", 
                          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        return filtered_data, num_days
        
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None
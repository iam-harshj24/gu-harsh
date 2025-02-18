import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import tempfile
import config
import analysis as analysis_func
import auth as gu_auth
import lang as gu_lang
import os
import components as gu_comp


def handle_file_operations():
    # Define file path location for the saved file
    file_path = config.SAVED_FILE_PATH  # Should point to 'files/main_file.xlsx'

    # Check if the file already exists
    if os.path.exists(file_path):
        # If the file exists, show success message and options to update or delete
        st.sidebar.success(f"File found: {file_path}")
        uploaded_file = None  # No need to upload again

        # Option to update the file (upload a new one)
        uploaded_file = st.sidebar.file_uploader("Upload New File", type=['xlsx'], key="file_uploader")

        if uploaded_file:
            try:
                # Save uploaded file temporarily for processing
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.sidebar.success("File updated successfully!")
            except Exception as e:
                st.error("Error saving the uploaded file")
                st.exception(e)
                return None  # Return None to prevent further processing

        # Option to delete the file
        if st.sidebar.button("Delete File"):
            delete_saved_file(file_path)
            uploaded_file = None  # Set uploaded_file to None after deletion
    else:
        # If the file does not exist, prompt the user to upload it
        uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=['xlsx'], key="file_uploader")
        if uploaded_file:
            try:
                # Save uploaded file temporarily for processing
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                st.sidebar.success("File uploaded and saved successfully!")
            except Exception as e:
                st.error("Error saving the uploaded file")
                st.exception(e)
                return None  # Return None to prevent further processing

    return file_path if os.path.exists(file_path) else None

# Function to delete saved file if it exists
def delete_saved_file(file_path):
    """Delete the saved file if it exists."""
    if os.path.exists(file_path):
        os.remove(file_path)
        st.sidebar.success("Saved file deleted successfully!")
    else:
        st.sidebar.warning("No file found to delete.")
        
def load_all_data_first(uploaded_file):
    merged_data, inventory_data, us_products_data = gu_comp.load_all_data_first_part(uploaded_file)
    st.sidebar.header(gu_lang.LangConfig.get("DRR_SETTINGS"))
    use_manual_drr = st.sidebar.checkbox(gu_lang.LangConfig.get("USE_MANUAL_DRR"), value=False)
    manual_drr_value = None
    if use_manual_drr:
        manual_drr_value = st.sidebar.number_input(gu_lang.LangConfig.get("MANUAL_DRR_VALUE"), min_value=0.0, value=100.0, step=0.1)
    inventory_status = gu_comp.load_all_data_second_part(merged_data, use_manual_drr, manual_drr_value, inventory_data)
    return merged_data, inventory_data, us_products_data, inventory_status

def setup_global_filters(merged_data):
    date_options = gu_comp.setup_global_filters_selected_dates(merged_data)
    selected_dates = st.sidebar.multiselect(
        gu_lang.LangConfig.get("SELECT_DATES"),
        options=date_options,
    )

    asin_options = gu_comp.setup_global_filters_asin_options(merged_data)
    selected_asins = st.sidebar.multiselect(
        gu_lang.LangConfig.get("SELECT_ASINS"),
        options=asin_options
    )

    product_options = gu_comp.setup_global_filters_product_options(merged_data)
    selected_products = st.sidebar.multiselect(
        gu_lang.LangConfig.get("SELECT_PRODUCTS"),
        options=product_options
    )

    return selected_dates, selected_asins, selected_products

def display_overview_tab(filtered_merged_data):
    st.header("Overview")
    # Metrics using filtered data
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Products", len(filtered_merged_data['ASIN'].unique()))
    with col2:
        st.metric("Total Sales", f"{filtered_merged_data['Sales'].sum():,.0f}")
    with col3:
        st.metric("Average Sales", f"{filtered_merged_data['Sales'].mean():,.2f}")
    with col4:
        st.metric("Total Profit", f"${filtered_merged_data['Gross Profit'].sum():,.2f}")

    # Sales Trend with filtered data
    st.subheader("Sales Trend")
    sales_trend = filtered_merged_data.groupby('Date')['Sales'].sum().reset_index()
    fig_sales = px.line(sales_trend, x='Date', y='Sales', title='Daily Sales Trend')
    st.plotly_chart(fig_sales, use_container_width=True)

    # Profit Trend with filtered data
    st.subheader("Profit Trend")
    profit_trend = filtered_merged_data.groupby('Date')['Gross Profit'].sum().reset_index()
    fig_profit = px.line(profit_trend, x='Date', y='Gross Profit', title='Daily Profit Trend')
    st.plotly_chart(fig_profit, use_container_width=True)

    st.subheader("Filtered Data View")
    st.dataframe(filtered_merged_data)

def display_inventory_status_tab(filtered_inventory_status,filtered_inventory_data):
    st.header("Inventory Status")
    # Inventory Status Summary with filtered data
    st.subheader("Inventory Status Summary")
    status_summary = filtered_inventory_status['Inventory Status'].value_counts()
    fig_status = px.pie(values=status_summary.values, 
                        names=status_summary.index,
                        title='Distribution of Inventory Status')
    st.plotly_chart(fig_status)

    # Detailed Inventory Status with filtered data
    st.subheader("Detailed Inventory Status")
    display_columns = config.INVENTORY_STATUS_COLUMNS
    st.dataframe(filtered_inventory_status[display_columns])

    st.subheader("Upcoming Shipments")
    st.dataframe(filtered_inventory_data)

def display_shipment_planning_tab(filtered_inventory_status):
    st.header("Shipment Planning")
    target_date = st.date_input(
        "Select Target Date for Shipment Planning",
        value=datetime.now() + timedelta(days=30),
        min_value=datetime.now()
    )
    
    shipment_plan = analysis_func.calculate_shipment_plan(filtered_inventory_status, target_date)
    
    # Shipment Requirements Visualization with filtered data
    st.subheader("Shipment Requirements")
    fig_shipment = px.bar(shipment_plan, 
                        x='Product Name',
                        y='Required_Shipment_with_buffer_stock',
                        title='Required Shipment Quantities by Product')
    fig_shipment.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_shipment, use_container_width=True)

    # Detailed Shipment Plan
    st.subheader("Detailed Shipment Plan")
    st.dataframe(shipment_plan) 

def display_loss_analysis_tab(selected_dates,temp_path):
    st.header("Loss Analysis")
    loss_report = analysis_func.calculate.calculate_daily_loss_report(temp_path, "Profit")
    
    if selected_dates:
        loss_report = loss_report[loss_report.index.isin(selected_dates)]
    
    # Loss Trend Visualization
    st.subheader("Daily Loss Trend")
    fig_loss = px.line(loss_report, 
                        x=loss_report.index,
                        y='Total Loss',
                        title='Daily Loss Trend')
    st.plotly_chart(fig_loss, use_container_width=True)
    
    # Product Count with Losses
    st.subheader("Products with Losses")
    fig_count = px.bar(loss_report,
                        x=loss_report.index,
                        y='Product Count',
                        title='Number of Products with Losses by Date')
    st.plotly_chart(fig_count, use_container_width=True)
    
    st.subheader("Detailed Loss Report")
    st.dataframe(loss_report)   
    
def display_profit_sale_analysis_tab(apply_filters,temp_path):
    st.header("Profit & Sales Change Analysis")
    st.subheader("Profit Change Analysis")
    profit_analysis = analysis_func.calculate.calculate_averages_and_percentage_change(temp_path, "Profit")
    filtered_profit = apply_filters(profit_analysis)

    fig_profit_change = px.scatter(filtered_profit,
                                    x='3-Day Average',
                                    y='Percentage Change (3-day avg)',
                                    hover_data=['Product Name'],
                                    title='Profit Change vs 3-Day Average')
    st.plotly_chart(fig_profit_change, use_container_width=True)

    st.subheader("Detailed Profit Analysis")
    st.dataframe(filtered_profit)

    # Process Sales Sheet
    st.subheader("Sales Change Analysis")
    sales_analysis = analysis_func.calculate.calculate_averages_and_percentage_change(temp_path, "Sales")
    filtered_sales = apply_filters(sales_analysis)

    fig_sales_change = px.scatter(filtered_sales,
                                    x='3-Day Average',
                                    y='Percentage Change (3-day avg)',
                                    hover_data=['Product Name'],
                                                title='Sales Change vs 3-Day Average')
    st.plotly_chart(fig_sales_change, use_container_width=True)

    st.subheader("Detailed Sales Analysis")
    st.dataframe(filtered_sales)

def display_max_drr_analysis_tab(apply_filters,inventory_data):
    st.header("Maximum DRR Analysis")

    col1, col2, col3 = st.columns(3)
    with col1:
        target_date = st.date_input(
            "Target Date",
            value=datetime.now() + timedelta(days=30)
        )
    with col2:
        future_date = st.date_input(
            "Starting Date",
            value=datetime.now()
        )
    with col3:
        use_manual_drr_max = st.checkbox("Use Manual DRR for Max DRR")
        manual_drr_max = None
        if use_manual_drr_max:
            manual_drr_max = st.number_input("Enter Manual DRR", min_value=0.0, value=100.0, step=0.1)
    if st.button("Calculate Maximum DRR"):
        filtered_inventory_data = apply_filters(inventory_data)
        max_drr_results = analysis_func.calculate.calculate_max_drr_with_push_drr(
            filtered_inventory_data, 
            target_date, 
            future_date,
            manual_drr_max if use_manual_drr_max else None
        )

        if not max_drr_results.empty:
            # Visualization
            st.subheader("Maximum DRR Distribution")
            fig = px.bar(
                max_drr_results,
                x='Product Name',
                y='Max DRR',
                title='Maximum Sustainable DRR by Product'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            # Summary Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Max DRR", f"{max_drr_results['Max DRR'].mean():.2f}")
            with col2:
                st.metric("Median Max DRR", f"{max_drr_results['Max DRR'].median():.2f}")
            with col3:
                st.metric("Total Products", len(max_drr_results))

            # Detailed Results Table
            st.subheader("Detailed Results")
            st.dataframe(max_drr_results)

            # Download Button
            st.download_button(
                label="Download Results",
                data=max_drr_results.to_csv(index=False),
                file_name="max_drr_results.csv",
                mime="text/csv"
            )

def display_daily_drr_calculator_tab(uploaded_file):
    st.title("Daily DRR Calculator")
                
    if uploaded_file:
        sheet_name = "Inventory"  # Use inventory sheet directly
        target_date = st.date_input("Select Target Date", min_value=datetime.today())

        if st.button("Calculate DRR"):
            output = analysis_func.calculate.calculate_daily_drr(uploaded_file, sheet_name, target_date)
            st.success("Calculation Complete!")
            st.dataframe(output)

            # Option to download the results
            csv = output.to_csv().encode('utf-8')
            st.download_button(
                label="Download DRR Results as CSV",
                data=csv,
                file_name='daily_drr_results.csv',
                mime='text/csv'
            )
    else:
        st.warning(gu_lang.LangConfig.get("UPLOAD_WARNING"))

def display_label_planning_tab(uploaded_file,inventory_status,selected_dates,selected_asins,selected_products):
    st.header("Labels Planning")
                
    if uploaded_file is not None:
        target_date = st.date_input(
            "Select Target Date for Label Planning",
            value=datetime.now() + timedelta(days=30),
            min_value=datetime.now(),
            key="label_target_date"
        )
        label_plan =gu_comp.labal_data_calculation(uploaded_file, inventory_status, target_date)
        # label_plan = analysis_func.calculate.process_label_planning(uploaded_file, inventory_status, target_date)

        if not label_plan.empty:
            filtered_label_plan = label_plan.copy()
            if selected_dates:
                filtered_label_plan = filtered_label_plan[
                    filtered_label_plan['Date'].isin(selected_dates)
    ]
            if selected_asins:
                filtered_label_plan = filtered_label_plan[
                    filtered_label_plan['ASIN'].isin(selected_asins)
                ]

            if selected_products:
                filtered_label_plan = filtered_label_plan[
                    filtered_label_plan['Product Name'].isin(selected_products)
                ]

            st.subheader("Label Plan")
            display_columns = config.LABEL_PLAN_COLUMNS

        if all(col in filtered_label_plan.columns for col in display_columns):
            col1, col2, col3 = st.columns(3)
            with col1:
                total_products = len(filtered_label_plan['Product Name'].unique())
                st.metric("Total Products", total_products)
            with col2:
                total_inventory = filtered_label_plan['Current Inventory'].sum()
                st.metric("Total Current Inventory", f"{total_inventory:,.0f}")
            with col3:
                total_required = filtered_label_plan['Required Labels (Stocks+Packed+New Orders)'].sum()
                st.metric("Total Required Inventory", f"{total_required:,.0f}")
            st.dataframe(filtered_label_plan[display_columns])     
            st.download_button(
                    label="Download Filtered Label Plan",
                data=filtered_label_plan.to_csv(index=False),
                file_name="filtered_label_plan.csv",
                mime="text/csv"
            )
        else:
            st.warning(gu_lang.LangConfig.get("COLUMNS_MISSING_ERROR"))
    else:
        st.warning(gu_lang.LangConfig.get("NO_VAILD_LABEL_DATA_FOUND"))

def display_target_sale_mang_tab():
    st.header(gu_lang.LangConfig.get("TAB_TARGET"))
    if 'data' not in st.session_state:
        try:
            st.session_state.data = pd.read_csv(config.TARGET_SALES_DATA_FILE)
        except FileNotFoundError:
            st.session_state.data = pd.DataFrame(columns=['Month', 'ASIN', 'Product_Name', 'Units', 'Price', 'Total'])
    data = st.session_state.data
    month_days = config.MONTH_DAYS
    products = pd.DataFrame(config.PREDEFINED_PRODUCTS)
    month = st.selectbox("Select Month", options=list(month_days.keys()))
    if 'editable_data' not in st.session_state or st.session_state.selected_month != month:
        st.session_state.selected_month = month
        existing_data = data[data['Month'] == month]
        if existing_data.empty:
            editable_data = products.copy()
            editable_data['Month'] = month
            editable_data['Units'] = 0
            editable_data['Price'] = 0.0
            editable_data['Total'] = 0.0
        else:
            editable_data = existing_data[['Month', 'ASIN', 'Product_Name', 'Units', 'Price', 'Total']].copy()
        st.session_state.editable_data = editable_data

    enable_edit = st.toggle("Enable Editing")

    st.subheader(f"Set Targets for {month}")
    if enable_edit:
        edited_data = st.data_editor(
            st.session_state.editable_data[['ASIN', 'Product_Name', 'Units', 'Price']],
            num_rows="fixed", key="edit_table"
        )
        if st.button("Save Targets"):
            edited_data['Month'] = month
            edited_data['Total'] = edited_data['Units'] * edited_data['Price'] * month_days[month]
            data = data[data['Month'] != month]
            data = pd.concat([data, edited_data], ignore_index=True)
            st.session_state.data = data
            data.to_csv('target_sales_data.csv', index=False)
            st.success(gu_lang.LangConfig.get("TARGETS_SAVED",month))
    else:
        st.dataframe(st.session_state.editable_data[['ASIN', 'Product_Name', 'Units', 'Price', 'Total']])

def display_us_product_shipment_planing_tab(us_products_data,filtered_inventory_status):
    st.header(gu_lang.LangConfig.get("TAB_US_PRODUCTS"))
    if not us_products_data.empty:
        target_date = st.date_input(gu_lang.LangConfig.get("SELECT_TARGET_DATE"),
                                    value=datetime.now() + timedelta(days=30),
                                    min_value=datetime.now(),
                                    key="us_target_date")
        us_shipment_plan = analysis_func.calculate.calculate_us_shipment_plan(filtered_inventory_status, us_products_data, target_date)

        st.subheader("Updated Shipment Plan (US Products)")
        display_columns = config.US_PRODUCTS_COLUMNS
        st.dataframe(us_shipment_plan[display_columns])
        # Download option
        st.download_button(label="Download US Shipment Plan",
                            data=us_shipment_plan.to_csv(index=False),
                            file_name="us_shipment_plan.csv",
                            mime="text/csv")
    else:
        st.warning(gu_lang.LangConfig.get("UPLOAD_FILE_NO_US_PRODUCT"))

def display_sale_profit_any_tool_tab(uploaded_file):
        # st.set_page_config(page_title="Sales & Profit Performance Tracker", layout="wide")
    
                st.title("📈 Sales & Profit Performance Tracker")
    
    # Add a sidebar for instructions
                with st.sidebar:
                    st.header("📋 Instructions")
                    st.write("""
        1. Upload your Excel file containing Sales, Profit, and Tracker sheets
        2. Select date range or week for analysis
        3. Filter data by performance status
        4. Choose to send report immediately or schedule for later
        """)
    
                uploaded_file = st.file_uploader("📤 Upload Excel File", type=["xlsx"])
    
                if uploaded_file is not None:
                    result = analysis_func.process_data(uploaded_file)
        
                    if result is not None:
                        filtered_data, num_days = result
            
            # Email Configuration Section
                        with st.expander("📧 Configure Email Reports"):
                # Email recipient configuration
                            emails_input = st.text_area(
                    "Enter receiver emails (one per line)",
                                height=100,
                                help="Enter each email address on a new line"
                            )
                
                # Email sending options
                            email_option = st.radio(
                                "Choose email sending option:",
                                ["Send Now", "Schedule for Later"],
                                horizontal=True
                            )
                
                            if email_option == "Send Now":
                                if st.button("Send Email Now 📨", type="primary"):
                                    if emails_input:
                                        receiver_emails = [email.strip() for email in emails_input.split('\n') if '@' in email]
                                        if receiver_emails:
                                            sender_email = "info@shavgun.com"
                                            password = "Lapu971915@#"
                                            subject = "SVA Analytics and PPC Performance Report"
                                
                                            try:
                                                for receiver_email in receiver_emails:
                                                    analysis_func.send_email_via_hostinger_for_performance_tracker(
                                                        sender_email,
                                                        receiver_email,
                                                        subject,
                                                        filtered_data,
                                                        password,
                                                        num_days
                                                    )
                                                st.success("✅ Emails sent successfully!")
                                            except Exception as e:
                                                st.error(f"❌ Error sending emails: {str(e)}")
                                        else:
                                            st.warning("⚠️ Please enter valid email addresses")
                                    else:
                                        st.warning("⚠️ Please enter at least one email address")
                
                            else:  # Schedule for Later
                                col1, col2 = st.columns(2)
                    
                                with col1:
                                    schedule_date = st.date_input(
                                        "Select start date",
                                        min_value=datetime.now().date(),
                                        value=datetime.now().date()
                                    )
                    
                                with col2:
                                    schedule_time = st.time_input(
                                        "Select time",
                                        datetime.strptime("09:00", "%H:%M").time()
                                    )
                    
                    # Frequency selection
                                frequency = st.selectbox(
                                    "Select frequency",
                                    ["Daily", "Weekly", "Monthly", "One-time"]
                                )
                    
                                if frequency == "Weekly":
                                    weekdays = st.multiselect(
                                        "Select days of the week",
                                        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                                    )
                                elif frequency == "Monthly":
                                    monthly_day = st.number_input(
                                        "Select day of the month",
                                        min_value=1,
                                        max_value=31,
                                        value=1
                                    )
                    
                                if st.button("Schedule Emails ⏰", type="primary"):
                                    if emails_input:
                                        receiver_emails = [email.strip() for email in emails_input.split('\n') if '@' in email]
                                        if receiver_emails:
                                            sender_email = "info@shavgun.com"
                                            password = "Lapu971915@#"
                                            subject = "SVA Analytics and PPC Performance Report"
                                
                                            try:
                                                schedule_datetime = datetime.combine(schedule_date, schedule_time)
                                    
                                                # Pass frequency parameters to schedule_email function
                                                schedule_params = {
                                                    'frequency': frequency,
                                                    'weekdays': weekdays if frequency == "Weekly" else None,
                                                    'monthly_day': monthly_day if frequency == "Monthly" else None,
                                                    'schedule_datetime': schedule_datetime
                                                }
                                    
                                                analysis_func.schedule_email(
                                                    sender_email,
                                                    receiver_emails,
                                                    subject,
                                                    filtered_data,
                                                    password,
                                                    num_days,
                                                    schedule_time,
                                                    **schedule_params
                                                )
                                                st.success("✅ Email scheduling configured successfully!")
                                            except Exception as e:
                                                st.error(f"❌ Error setting up email schedule: {str(e)}")
                                        else:
                                            st.warning("⚠️ Please enter valid email addresses")
                                    else:
                                        st.warning("⚠️ Please enter at least one email address")

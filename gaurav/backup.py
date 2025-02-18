import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import tempfile
import config
import analysis as analysis_func
import auth as gu_auth
import lang as gu_lang

def main():
    if not gu_auth.login.check_password():
        return
    st.sidebar.title(gu_lang.LangConfig.get("WELCOME", st.session_state.current_user))
    st.sidebar.write(gu_lang.LangConfig.get("ROLE", st.session_state.current_role))
    if st.sidebar.button(gu_lang.LangConfig.get("LOGOUT")):
        st.session_state.authenticated = False
        st.rerun()
    if st.session_state.current_user == 'Harsh':
        if st.sidebar.button(gu_lang.LangConfig.get("MANAGE_USERS")):
            st.session_state.show_user_management = True
    if st.session_state.get('show_user_management', False):
        gu_auth.login.user_management()
        if st.button(gu_lang.LangConfig.get("BACK_TO_DASHBOARD")):
            st.session_state.show_user_management = False
            st.rerun()
        return
    
    # Custom CSS styling
    st.markdown(config.CUSTOM_CSS, unsafe_allow_html=True)

    # File upload in Sidebar
    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=['xlsx'], key="excel_uploader")

    if uploaded_file:
        try:
            # Save uploaded file temporarily for processing
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_path = tmp_file.name

            # Load all data first
            with st.spinner(gu_lang.LangConfig.get("LOADING_DATA")):
                sales_data = analysis_func.read_sales_data(uploaded_file, "Sales")
                profit_data = analysis_func.read_gross_profit(uploaded_file, "Profit")
                merged_data = analysis_func.merge_sales_and_profit(sales_data, profit_data)
                inventory_data = analysis_func.read_inventory_data(uploaded_file, "Inventory")
                # label_data = read_labels_data(uploaded_file,'labels')
                us_products_data = analysis_func.calculate.read_us_products_data(uploaded_file, "US Products")
                # Sidebar: DRR settings
                st.sidebar.header(gu_lang.LangConfig.get("DRR_SETTINGS"))
                use_manual_drr = st.sidebar.checkbox(gu_lang.LangConfig.get("USE_MANUAL_DRR"), value=False)
                manual_drr_value = None
                if use_manual_drr:
                    manual_drr_value = st.sidebar.number_input(gu_lang.LangConfig.get("MANUAL_DRR_VALUE"), min_value=0.0, value=100.0, step=0.1)
                drr_data = analysis_func.calculate.calculate_normal_drr(merged_data, use_manual_drr, manual_drr_value)
                inventory_status = analysis_func.shipment_inventory_status(inventory_data, drr_data)

            # Global Filters in Sidebar
            st.sidebar.header(gu_lang.LangConfig.get("GLOBAL_FILTERS"))
            
            # Date filter
            date_options = sorted(merged_data['Date'].unique())
            selected_dates = st.sidebar.multiselect(
                gu_lang.LangConfig.get("SELECT_DATES"),
                options=date_options,
                # default=date_options[-7:] if len(date_options) > 7 else date_options  # Default to last 7 days
            )

            # ASIN filter
            asin_options = sorted(merged_data['ASIN'].unique())
            selected_asins = st.sidebar.multiselect(
                gu_lang.LangConfig.get("SELECT_ASINS"),
                options=asin_options
            )

            # Product filter
            product_options = sorted(merged_data['Product Name'].unique())
            selected_products = st.sidebar.multiselect(
                gu_lang.LangConfig.get("SELECT_PRODUCTS"),
                options=product_options
            )

            # Function to apply filters to any dataframe
            def apply_filters(df):
                filtered_df = df.copy()
                
                if 'Date' in df.columns and selected_dates:
                    filtered_df = filtered_df[filtered_df['Date'].isin(selected_dates)]
                
                if 'ASIN' in df.columns and selected_asins:
                    filtered_df = filtered_df[filtered_df['ASIN'].isin(selected_asins)]
                
                if 'Product Name' in df.columns and selected_products:
                    filtered_df = filtered_df[filtered_df['Product Name'].isin(selected_products)]
                
                return filtered_df

            # Apply filters to all relevant dataframes
            filtered_merged_data = apply_filters(merged_data)
            filtered_inventory_status = apply_filters(inventory_status)
            filtered_inventory_data = apply_filters(inventory_data)

            # Create tabs
            tabs = st.tabs(config.DASHBOARD_TABS)
            # Overview Tab
            with tabs[0]:
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

            # Inventory Status Tab
            with tabs[1]:
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

            # Shipment Planning Tab
            with tabs[2]:
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

            # Loss Analysis Tab
            with tabs[3]:
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

            # Profit Analysis Tab
            with tabs[4]:
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
            

            # Maximum DRR Analysis Tab
            with tabs[5]:
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
            with tabs[6]:
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
            with tabs[7]:
                st.header("Labels Planning")
                
                if uploaded_file is not None:
                    target_date = st.date_input(
                        "Select Target Date for Label Planning",
                        value=datetime.now() + timedelta(days=30),
                        min_value=datetime.now(),
                        key="label_target_date"
                    )

        # Get the label plan first
                    label_plan = analysis_func.calculate.process_label_planning(uploaded_file, inventory_status, target_date)
        
                    if not label_plan.empty:
            # Apply filters to label plan
                        filtered_label_plan = label_plan.copy()
            
            # Apply date filter if selected
                        if selected_dates:
                            filtered_label_plan = filtered_label_plan[
                                filtered_label_plan['Date'].isin(selected_dates)
                ]
            
            # Apply ASIN filter if selected
                        if selected_asins:
                            filtered_label_plan = filtered_label_plan[
                                filtered_label_plan['ASIN'].isin(selected_asins)
                            ]
            
            # Apply product filter if selected
                        if selected_products:
                            filtered_label_plan = filtered_label_plan[
                                filtered_label_plan['Product Name'].isin(selected_products)
                            ]

                        st.subheader("Label Plan")
                        display_columns = config.LABEL_PLAN_COLUMNS
            
                    if all(col in filtered_label_plan.columns for col in display_columns):
                # Display metrics for the filtered data
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
                # Display the filtered dataframe
                        st.dataframe(filtered_label_plan[display_columns])     
                # Download button for filtered data
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
            with tabs[8]:
                st.header(gu_lang.LangConfig.get("TAB_TARGET"))
        # Load or initialize data
                if 'data' not in st.session_state:
                    try:
                        st.session_state.data = pd.read_csv(config.TARGET_SALES_DATA_FILE)
                    except FileNotFoundError:
                        st.session_state.data = pd.DataFrame(columns=['Month', 'ASIN', 'Product_Name', 'Units', 'Price', 'Total'])
                data = st.session_state.data
        # Define month days
                month_days = config.MONTH_DAYS
        # Predefined products and ASINs
                products = pd.DataFrame(config.PREDEFINED_PRODUCTS)
        # Select month
                month = st.selectbox("Select Month", options=list(month_days.keys()))
        # Initialize or load editable data
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
     
            with tabs[9]:  # Ensure tab indexing is correct
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
        except Exception as e:
            st.error("Error processing data")
            st.exception(e)
        with tabs[10]:
                st.title("📊 Sales & Profit Analysis Tool")
                st.write(gu_lang.LangConfig.get("UPLOAD_FILE_SALE_PROFIT_TEXT"))
                analysis_func.function.Performance_Tracker(uploaded_file)
        if gu_auth.login.has_permission('read'):
             st.title(config.DASHBOARD_TITLE)
    else:
        pass

if __name__ == "__main__":
    main()
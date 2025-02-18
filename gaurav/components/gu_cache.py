import streamlit as st
import analysis as analysis_func

@st.cache_data
def setup_global_filters_selected_dates(merged_data):
    date_options = sorted(merged_data['Date'].unique())
    return date_options

@st.cache_data
def setup_global_filters_asin_options(merged_data):
    asin_options = sorted(merged_data['ASIN'].unique())
    return asin_options

@st.cache_data
def setup_global_filters_product_options(merged_data):
    product_options = sorted(merged_data['Product Name'].unique())
    
    return product_options

@st.cache_data
def load_all_data_first_part(uploaded_file):
    sales_data = analysis_func.read_sales_data(uploaded_file, "Sales")
    profit_data = analysis_func.read_gross_profit(uploaded_file, "Profit")
    merged_data = analysis_func.merge_sales_and_profit(sales_data, profit_data)
    inventory_data = analysis_func.read_inventory_data(uploaded_file, "Inventory")
    us_products_data = analysis_func.calculate.read_us_products_data(uploaded_file, "US Products")
    return merged_data, inventory_data, us_products_data

@st.cache_data
def load_all_data_second_part(merged_data, use_manual_drr, manual_drr_value, inventory_data):
    drr_data = analysis_func.calculate.calculate_normal_drr(merged_data, use_manual_drr, manual_drr_value)
    inventory_status = analysis_func.shipment_inventory_status(inventory_data, drr_data)
    return inventory_status
@st.cache_data
def labal_data_calculation(uploaded_file, inventory_status, target_date):
    label_plan = analysis_func.calculate.process_label_planning(uploaded_file, inventory_status, target_date)
    return label_plan
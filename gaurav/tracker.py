import streamlit as st
import tempfile
import config
import auth as gu_auth
import lang as gu_lang
import components as gu_tabs
import ui as gu_css
import os
import components as gu_comp
import pandas as pd
import shutil

def main():
    if not gu_auth.login_check_and_sidebar_actions():
        return
    if gu_auth.manage_users():
        return
    
    # Custom CSS styling
    gu_css.apply_custom_css()

    # Handle file operations (upload, update, delete)
    file_path = gu_comp.handle_file_operations()
    

    if file_path is None:
        st.write("No file loaded. Please upload a file.")
        return

    try:
        # Proceed with loading the data from the file
        with st.spinner(gu_lang.LangConfig.get("LOADING_DATA")):
            merged_data, inventory_data, us_products_data, inventory_status = gu_tabs.load_all_data_first(file_path)

        # Global Filters in Sidebar
        st.sidebar.header(gu_lang.LangConfig.get("GLOBAL_FILTERS"))
        selected_dates, selected_asins, selected_products = gu_tabs.setup_global_filters(merged_data)

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
            gu_tabs.display_overview_tab(filtered_merged_data)

        # Inventory Status Tab
        with tabs[1]:
            gu_tabs.display_inventory_status_tab(filtered_inventory_status, filtered_inventory_data)

        # Shipment Planning Tab
        with tabs[2]:
            gu_tabs.display_shipment_planning_tab(filtered_inventory_status)

        # Loss Analysis Tab
        with tabs[3]:
            gu_tabs.display_loss_analysis_tab(selected_dates, file_path)

        # Profit Analysis Tab
        with tabs[4]:
            gu_tabs.display_profit_sale_analysis_tab(apply_filters, file_path)

        # Maximum DRR Analysis Tab
        with tabs[5]:
            gu_tabs.display_max_drr_analysis_tab(apply_filters, inventory_data)

        with tabs[6]:
            gu_tabs.display_daily_drr_calculator_tab(file_path)

        with tabs[7]:
            gu_tabs.display_label_planning_tab(file_path, inventory_status, selected_dates, selected_asins, selected_products)

        with tabs[8]:
            gu_tabs.display_target_sale_mang_tab()

        with tabs[9]:
            gu_tabs.display_us_product_shipment_planing_tab(us_products_data, filtered_inventory_status)

        with tabs[10]:
            gu_tabs.display_sale_profit_any_tool_tab(file_path)

        # Display title if the user has permission
        if gu_auth.login.has_permission('read'):
            st.title(config.DASHBOARD_TITLE)
            
            
        # # ✅ New Feature: Live Edit and Save Only "Sales" Sheet
        # st.subheader("Live Edit: Sales Sheet")
        
        # # Load all sheets to ensure we don't lose data
        # with pd.ExcelFile(file_path, engine="openpyxl") as xls:
        #     sheets = {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}

        # # Check if "Sales" sheet exists
        # if "Sales" in sheets:
        #     df_sales = sheets["Sales"]  # Load "Sales" sheet
        #     edited_sales = st.data_editor(df_sales, num_rows="dynamic")  # Allow live edit

        #     # Save changes
        #     if st.button("Save Changes"):
        #         # Create a temporary copy of the file
        #         temp_file_path = "files/main_file_temp.xlsx"
        #         shutil.copy(file_path, temp_file_path)  # Copy original file
                
        #         try:
        #             # Save the changes only to the "Sales" sheet
        #             sheets["Sales"] = edited_sales

        #             # Write back to a temporary file first
        #             with pd.ExcelWriter(temp_file_path, engine="openpyxl", mode="w") as writer:
        #                 for sheet_name, data in sheets.items():
        #                     data.to_excel(writer, sheet_name=sheet_name, index=False)

        #             # Replace the original file
        #             shutil.move(temp_file_path, file_path)

        #             st.success("Sales sheet updated successfully!")

        #         except Exception as e:
        #             st.error("Error saving the file.")
        #             st.exception(e)
        #             os.remove(temp_file_path)  # Remove temp file if error occurs
        # else:
        #     st.error("Sales sheet not found in the uploaded Excel file!")

    except Exception as e:
        st.error("Error processing data")
        st.exception(e)

if __name__ == "__main__":
    main()
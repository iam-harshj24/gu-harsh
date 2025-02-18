class LangConfig:
    MESSAGES = {
        # Authentication messages
        "WELCOME": "Welcome, {}",
        "ROLE": "Role: {}",
        "LOGOUT": "Logout",
        "MANAGE_USERS": "Manage Users",
        "BACK_TO_DASHBOARD": "Back to Dashboard",

        # Dashboard title
        "DASHBOARD_TITLE": "Sales & Inventory Dashboard",

        # Sidebar messages
        "UPLOAD_EXCEL": "Upload Excel File",
        "LOADING_DATA": "Loading data...",
        "GLOBAL_FILTERS": "Global Filters",
        "SELECT_DATES": "Select Dates",
        "SELECT_ASINS": "Select ASINs",
        "SELECT_PRODUCTS": "Select Products",

        # DRR Settings
        "DRR_SETTINGS": "DRR Settings",
        "USE_MANUAL_DRR": "Use Manual DRR",
        "MANUAL_DRR_VALUE": "Enter Manual DRR Value",

        # Tab names
        "TAB_OVERVIEW": "Overview",
        "TAB_INVENTORY": "Inventory Status",
        "TAB_SHIPMENT": "Shipment Planning",
        "TAB_LOSS": "Loss Analysis",
        "TAB_PROFIT": "Profit & Sales Change Analysis",
        "TAB_MAX_DRR": "Maximum DRR Analysis",
        "TAB_DAILY_DRR": "Daily DRR Calculator",
        "TAB_LABELS": "Labels Planning",
        "TAB_TARGET": "Target Sales Management",
        "TAB_US_PRODUCTS": "US Products Shipment Planning",
        "TAB_PERFORMANCE": "Performance Analysis",

        # Overview metrics
        "TOTAL_PRODUCTS": "Total Products",
        "TOTAL_SALES": "Total Sales",
        "AVG_SALES": "Average Sales",
        "TOTAL_PROFIT": "Total Profit",
        "SALES_TREND": "Sales Trend",
        "PROFIT_TREND": "Profit Trend",
        "DAILY_SALES_TREND": "Daily Sales Trend",
        "DAILY_PROFIT_TREND": "Daily Profit Trend",
        "FILTERED_DATA": "Filtered Data View",

        # Inventory Status
        "INVENTORY_SUMMARY": "Inventory Status Summary",
        "INVENTORY_STATUS": "Inventory Status",
        "DETAILED_INVENTORY": "Detailed Inventory Status",
        "UPCOMING_SHIPMENTS": "Upcoming Shipments",

        # Shipment Planning
        "SELECT_TARGET_DATE": "Select Target Date for Shipment Planning",
        "SHIPMENT_REQUIREMENTS": "Shipment Requirements",
        "DETAILED_SHIPMENT": "Detailed Shipment Plan",

        # Loss Analysis
        "DAILY_LOSS_TREND": "Daily Loss Trend",
        "PRODUCTS_WITH_LOSSES": "Products with Losses",
        "DETAILED_LOSS": "Detailed Loss Report",

        # Buttons and Actions
        "CALCULATE_DRR": "Calculate DRR",
        "DOWNLOAD_RESULTS": "Download Results",
        "SAVE_TARGETS": "Save Targets",
        "ENABLE_EDITING": "Enable Editing",

        # Messages
        "CALCULATION_COMPLETE": "Calculation Complete!",
        "TARGETS_SAVED": "Targets for {} saved successfully!",

        # Warnings and Errors
        "COLUMNS_MISSING_ERROR":"Some expected columns are missing in the Label Plan data.",
        "NO_VAILD_LABEL_DATA_FOUND":"No valid label data found in the uploaded file.",
        "UPLOAD_WARNING": "Please upload an Excel file to proceed.",
        "ERROR_PROCESSING": "Error processing data",
        "NO_DATA_FOUND": "No valid {} data found in the uploaded file.",
        "MISSING_COLUMNS": "Some expected columns are missing in the {} data.",
        "UPLOAD_FILE_SALE_PROFIT_TEXT":"Upload an Excel file containing sales and profit data to analyze the average sales and profit for a selected date range.",
        "UPLOAD_FILE_NO_US_PRODUCT":"No US Products data found in the uploaded file."
    }

    @staticmethod
    def get(key: str, *args) -> str:
        """
        Get message by key with optional formatting arguments
        """
        message = LangConfig.MESSAGES.get(key, key)
        if args:
            return message.format(*args)
        return message
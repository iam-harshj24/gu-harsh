# Application configuration settings
APP_TITLE = "Inventory Management Dashboard"
DEFAULT_PORT = 5000
DEFAULT_HOST = "0.0.0.0"
SAVED_FILE_PATH = "files/main_file.xlsx"

# Data processing settings
DATE_FORMAT = "%Y%m%d"
DEFAULT_DECIMAL_PLACES = 2

# Dashboard Settings
DASHBOARD_TITLE = "SVA Analytics"
PAGE_TITLE = "Inventory Management Dashboard"
PAGE_LAYOUT = "wide"

# File Settings
ALLOWED_FILE_TYPES = ['xlsx']
TEMP_FILE_SUFFIX = '.xlsx'

# Sheet Names
SHEET_NAMES = {
    'SALES': "Sales",
    'PROFIT': "Profit",
    'INVENTORY': "Inventory",
    'US_PRODUCTS': "US Products"
}

# Date Settings
DEFAULT_FORECAST_DAYS = 30
DEFAULT_START_DATE = None  # Will be set to datetime.now() when used

# DRR Settings
DEFAULT_DRR_VALUE = 100.0
MIN_DRR_VALUE = 0.0
DRR_STEP = 0.1

# Month Configuration
MONTH_DAYS = {
    'January': 31, 
    'February': 28, 
    'March': 31, 
    'April': 30,
    'May': 31, 
    'June': 30, 
    'July': 31, 
    'August': 31,
    'September': 30, 
    'October': 31, 
    'November': 30, 
    'December': 31
}

# Predefined Products
PREDEFINED_PRODUCTS = [
    {'ASIN': 'B07GNLN5K2', 'Product_Name': 'SVA Peppermint Arvensis 4 Oz'},
    {'ASIN': 'B07GCQDX6M', 'Product_Name': 'SVA Citronella Oil 4 Oz'},
    {'ASIN': 'B072M2MTK1', 'Product_Name': 'SVA Rose Water 4 Oz (US)'},
]

# Display Settings
CUSTOM_CSS = """
    <style>
        .main-header {text-align: center; padding: 1rem;}
        .filter-section {background-color: #f0f2f6; padding: 1rem; border-radius: 5px;}
        .stMetricValue {font-size: 24px !important;}
        .status-urgent {color: red;}
        .status-warning {color: orange;}
        .status-good {color: green;}
    </style>
"""

# Tab Names
DASHBOARD_TABS = [
    "Overview",
    "Inventory Status",
    "Shipment Planning",
    "Loss Analysis",
    "Profit Analysis",
    "Maximum DRR Analysis",
    "DRR Timeline",
    "Labels data",
    "Target Sales Management",
    "US Products Shipment Planning",
    "Performance Tracker"
]

# Column Configurations
INVENTORY_STATUS_COLUMNS = [
    'Date', 'ASIN', 'Product Name', 'Current Inventory',
    'Daily_Run_Rate', 'Date of OOS', 'Days of inventory',
    'Inventory Status'
]

LABEL_PLAN_COLUMNS = [
    'Date', 'ASIN', 'Product Name', 'Current Inventory',
    'Daily_Run_Rate', 'Expected_Usage', 'IN Stocks',
    'Packed', 'New Orders', 'Total Available Label (Stocks+Packed)',
    'Required Labels (Stocks+Packed+New Orders)'
]

US_PRODUCTS_COLUMNS = [
    'ASIN', 'Product Name', 'Current Inventory',
    'Daily_Run_Rate', 'Expected_Usage', 'Total Upcoming Shipment',
    'AWD', 'Backstock', 'Upcoming Orders', 'Required Inventory(AWD+BS+ORDERS)'
]

# File Paths
TARGET_SALES_DATA_FILE = 'target_sales_data.csv'
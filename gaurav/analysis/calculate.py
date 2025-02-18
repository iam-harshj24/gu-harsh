import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import schedule
import time
import auth as gu_auth
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import ssl
import io


def send_email_via_hostinger_for_performance_tracker(sender_email, receiver_email, subject, filtered_data, password, num_days):
    """Send email with HTML content and Excel attachment"""
    try:
        smtp_server = "smtp.hostinger.com"
        smtp_port = 587
        
        message = MIMEMultipart("alternative")
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        
        # Create and attach HTML content
        html_content = create_email_html(filtered_data, num_days)
        if html_content:
            message.attach(MIMEText(html_content, "html"))
        
        # Create Excel attachment
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            for group_name, group_data in filtered_data.groupby('Undercontrol'):
                group_data.to_excel(writer, sheet_name=str(group_name), index=False)
        
        excel_buffer.seek(0)
        part = MIMEBase("application", "octet-stream")
        part.set_payload(excel_buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename="Performance_Report.xlsx")
        message.attach(part)
        
        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
            st.success(f"Email sent successfully to {receiver_email}!")
            
    except Exception as e:
        st.error(f"Error sending email to {receiver_email}: {str(e)}")
def create_email_html(filtered_data, num_days):
    """Create HTML email content with KPIs"""
    try:
        # Calculate KPIs
        total_sales = filtered_data['Sales(Units)'].sum()
        total_revenue = filtered_data['Revenue'].sum()
        total_ad_spend = filtered_data['Ad Spend'].sum()
        total_profit = filtered_data['Profit'].sum()
        
        # Format date range
        today = datetime.now()
        date_range = f"{(today - timedelta(days=num_days)).strftime('%A, %b %d, %Y')} - {today.strftime('%A, %b %d, %Y')}"

        # Create HTML template
        html = f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .header {{
                        padding: 20px 0;
                        border-bottom: 2px solid #eee;
                    }}
                    .title {{
                        color: #333;
                        font-size: 24px;
                        margin-bottom: 10px;
                    }}
                    .date-range {{
                        color: #666;
                        font-size: 14px;
                    }}
                    .kpi-container {{
                        display: flex;
                        justify-content: space-between;
                        margin: 20px 0;
                        flex-wrap: wrap;
                    }}
                    .kpi-box {{
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 8px;
                        margin: 10px;
                        min-width: 200px;
                    }}
                    .kpi-title {{
                        font-size: 14px;
                        color: #666;
                        margin-bottom: 5px;
                    }}
                    .kpi-value {{
                        font-size: 20px;
                        font-weight: bold;
                        color: #0066cc;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="title">Daily SVA Analytics and PPC Performance Report</div>
                    <div class="date-range">{date_range}</div>
                </div>
                
                <div class="kpi-container">
                    <div class="kpi-box">
                        <div class="kpi-title">Total Sales Unit</div>
                        <div class="kpi-value">{total_sales:,.2f}</div>
                    </div>
                    <div class="kpi-box">
                        <div class="kpi-title">Total Revenue</div>
                        <div class="kpi-value">${total_revenue:,.2f}</div>
                    </div>
                    <div class="kpi-box">
                        <div class="kpi-title">Total Ad Spend</div>
                        <div class="kpi-value">${total_ad_spend:,.2f}</div>
                    </div>
                    <div class="kpi-box">
                        <div class="kpi-title">Total Profit</div>
                        <div class="kpi-value">${total_profit:,.2f}</div>
                    </div>
                </div>
                
                <div class="performance-summary">
                    <h3>Performance Summary</h3>
                    <p>Total Products: {len(filtered_data)}</p>
                    <p>Leading Products: {len(filtered_data[filtered_data["Performance Status"] == "Leading ✅"])}</p>
                    <p>Lagging Products: {len(filtered_data[filtered_data["Performance Status"] == "Lagging ⚠️"])}</p>
                </div>
            </body>
        </html>
        """
        return html
    except Exception as e:
        st.error(f"Error creating email HTML: {str(e)}")
        return None
def schedule_email(sender_email, receiver_emails, subject, filtered_data, password, num_days, schedule_time):
    """Schedule email to be sent at specified time"""
    def job():
        for receiver_email in receiver_emails:
            gu_auth.send_email_via_hostinger(sender_email, receiver_email, subject, filtered_data, password, num_days)
    
    schedule.every().day.at(schedule_time).do(job)
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

def calculate_daily_loss_report(file_path, sheet_name, decimal_places=2):
    # Load the data from the specified Excel sheet
    data = pd.read_excel(file_path, sheet_name=sheet_name)

    # Ensure the data is a DataFrame
    if isinstance(data, pd.DataFrame):
        # Dictionary to store the results for each day
        daily_report = {}

        # Loop through each product row starting from the second row (index 1)
        for index, row in data.iterrows():
            product_name = row[1]  # assuming the second column is product name
            ASIN = row[0]  # assuming the first column contains the ASIN

            # Extract the profit data excluding ASIN and product name (which are in columns 0 and 1)
            profit_data = row[2:]

            # Loop through each day's profit and calculate losses (if any)
            for date, profit in profit_data.items():
                if profit < 0:  # Loss condition
                    if date not in daily_report:
                        daily_report[date] = {'Total Loss': 0, 'Product Count': 0}
                    daily_report[date]['Total Loss'] += profit
                    daily_report[date]['Product Count'] += 1

        # Round the total losses to the specified number of decimal places
        for date, report in daily_report.items():
            report['Total Loss'] = round(report['Total Loss'], decimal_places)

        # Convert the daily report dictionary to a DataFrame
        report_df = pd.DataFrame.from_dict(daily_report, orient='index')

        # Sort the DataFrame by the index (date) in descending order (latest dates first)
        report_df = report_df.sort_index(ascending=False)

        # Write the report to a CSV file
       

        return report_df
    else:
        raise ValueError("Input data must be a pandas DataFrame.")
    




import pandas as pd

def calculate_averages_and_percentage_change(file_path, sheet_name, decimal_places=2):
    # Load the data from the specified Excel sheet
    data = pd.read_excel(file_path, sheet_name=sheet_name)

    # Ensure the data is a DataFrame
    if isinstance(data, pd.DataFrame):
        # List to store the results
        results = []

        # Loop through each product row starting from the second row (index 1)
        for index, row in data.iterrows():
            # The product name is now the second column (index 1) and ASIN is in the first column (index 0)
            ASIN = row[0]
            product_name = row[1]

            # Extract the profit values (skipping the first two columns, ASIN and product name)
            profit_data = row[2:]

            # Ensure there are enough days of data to calculate the averages and percentage change
            if len(profit_data) >= 5:
                # Extract the last 5 days of data excluding today's and the previous day's data
                last_five_days = profit_data.head(5)
                today_profit = last_five_days.iloc[0]  # The second to last day's data (2-day lag)
                last_three_days = profit_data.head(3)  # The first 3 days of the last 5 days excluding the lag

                # Calculate the 3-day average (excluding today's and previous day's data)
                three_day_avg = last_three_days.mean()
                three_day_avg = round(three_day_avg, decimal_places)

                # Calculate the 5-day average (excluding today's and previous day's data)
                five_day_avg = last_five_days.mean()
                five_day_avg = round(five_day_avg, decimal_places)

                # Calculate the percentage change based on the 3-day average
                if three_day_avg != 0:
                    percentage_change_3_day = ((today_profit - three_day_avg) / three_day_avg) * 100
                else:
                    percentage_change_3_day = None

                # Calculate the percentage change based on the 5-day average
                if five_day_avg != 0:
                    percentage_change_5_day = ((today_profit - five_day_avg) / five_day_avg) * 100
                else:
                    percentage_change_5_day = None
            else:
                three_day_avg = None
                five_day_avg = None
                percentage_change_3_day = None
                percentage_change_5_day = None
                today_profit = None

            # Append the data as a row in the results list
            results.append({
                'Product Name': product_name,
                'ASIN': ASIN,
                'Today\'s Data': today_profit,
                '3-Day Average': three_day_avg,
                'Percentage Change (3-day avg)': percentage_change_3_day,
                '5-Day Average': five_day_avg,

                'Percentage Change (5-day avg)': percentage_change_5_day,

            })

        # Convert results list to a DataFrame
        results_df = pd.DataFrame(results)
        results_df.to_csv('unnatural changes in profit.csv')
        return results_df
    else:
        raise ValueError("Input data must be a pandas DataFrame.")
    

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
    
    return df.round()

def calculate_max_drr_with_push_drr(inventory_data, target_date, future_date, manual_drr=None):
    df = inventory_data.copy()
    
    # Validate dates
    target_date = pd.to_datetime(target_date)
    future_date = pd.to_datetime(future_date)
    current_date = (datetime.now() - timedelta(days=2)).date()
    
    # Initialize results list
    results = []
    
    for _, row in df.iterrows():
        product_name = row['Product Name']
        current_inventory = row['Current inventory']
        
        # Get shipment columns
        shipment_cols = [col for col in df.columns if isinstance(col, datetime) or 
                       (isinstance(col, str) and col not in ['ASIN', 'Product Name', 'Current inventory'])]
        
        # Create validated shipments list
        shipments = []
        for col in shipment_cols:
            try:
                date = pd.to_datetime(col)
                if pd.notnull(row[col]):
                    shipments.append((date, float(row[col])))
            except:
                continue
        
        # Sort shipments by date
        shipments.sort(key=lambda x: x[0])
        
        # Calculate initial inventory based on future date
        initial_inventory = current_inventory
        calc_start_date = current_date if future_date.date() <= current_date else future_date.date()
        
        # If manual DRR is provided, calculate inventory adjustment up to future date
        if manual_drr is not None:
            days_to_future = (calc_start_date - current_date).days
            initial_inventory -= (days_to_future * manual_drr)
        
        # Add all shipments up to the future date
        for ship_date, ship_qty in shipments:
            if ship_date.date() <= calc_start_date:
                initial_inventory += ship_qty
        
        # Get remaining shipments after future date
        future_shipments = [(d, q) for d, q in shipments if d.date() > calc_start_date and d.date() <= target_date.date()]
        
        # Binary search for maximum DRR
        left, right = 0, 10000  # Reasonable upper bound
        max_drr = 0
        best_ending_inventory = 0
        
        while left <= right:
            mid = (left + right) // 2
            current_inventory = initial_inventory
            valid = True
            temp_date = calc_start_date
            shipment_index = 0
            
            while temp_date <= target_date.date():
                # Process any shipments for this date
                while (shipment_index < len(future_shipments) and 
                       future_shipments[shipment_index][0].date() <= temp_date):
                    current_inventory += future_shipments[shipment_index][1]
                    shipment_index += 1
                
                # Subtract daily consumption
                current_inventory -= mid
                
                if current_inventory < 0:
                    valid = False
                    break
                
                temp_date += timedelta(days=1)
            
            if valid:
                if mid > max_drr:
                    max_drr = mid
                    best_ending_inventory = current_inventory
                left = mid + 1
            else:
                right = mid - 1
        
        # Calculate total incoming shipments for both periods
        shipments_before_future = sum(qty for date, qty in shipments if date.date() <= calc_start_date)
        shipments_after_future = sum(qty for date, qty in shipments if calc_start_date < date.date() <= target_date.date())
        
        results.append({
            'Product Name': product_name,
            'ASIN': row.get('ASIN', 'N/A'),
            'Current Inventory': initial_inventory,
            'Max DRR': max_drr,
            # 'Ending Inventory': best_ending_inventory,
            'Total Shipments Before Future': shipments_before_future,
            'Total Shipments After Future': shipments_after_future,
            # 'Manual DRR Used': manual_drr if manual_drr is not None else 'No',
            # 'Calculation Start Date': calc_start_date
        })
    
    return pd.DataFrame(results)

def calculate_daily_drr(file_path, sheet_name, target_date):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return pd.DataFrame()

    required_cols = ['Product Name', 'Current inventory']
    if not all(col in df.columns for col in required_cols):
        st.error("Missing required columns in the Excel sheet.")
        return pd.DataFrame()

    df['Current inventory'] = pd.to_numeric(df['Current inventory'], errors='coerce').fillna(0).astype(int)

    # Identify shipment columns
    shipment_cols = df.columns[df.columns.get_loc('Current inventory')+1:]
    shipment_dates = pd.to_datetime(shipment_cols, errors='coerce')
    valid_shipments = {date: col for date, col in zip(shipment_dates, shipment_cols) if pd.notnull(date)}

    try:
        target_date = pd.to_datetime(target_date)
    except ValueError:
        st.error("Invalid target date format.")
        return pd.DataFrame()

    date_range = pd.date_range(start=datetime.today(), end=target_date, freq='D')
    results = {}

    for _, row in df.iterrows():
        product_name = row['Product Name']
        initial_inventory = row['Current inventory']
        shipments = [(date, int(pd.to_numeric(row[col], errors='coerce'))) for date, col in valid_shipments.items() if pd.notnull(row[col]) and row[col] > 0]
        shipments.sort()

        left, right = 0, max(initial_inventory + sum(qty for _, qty in shipments), 1000)
        base_drr = 0

        # Binary search for max sustainable DRR
        while left <= right:
            mid = (left + right) // 2
            remaining = initial_inventory
            current_date = datetime.today()
            shipment_idx = 0
            is_sustainable = True

            while current_date <= target_date:
                while shipment_idx < len(shipments) and shipments[shipment_idx][0] <= current_date:
                    remaining += shipments[shipment_idx][1]
                    shipment_idx += 1

                remaining -= mid
                if remaining < 0:
                    is_sustainable = False
                    break

                current_date += timedelta(days=1)

            if is_sustainable:
                base_drr = mid
                left = mid + 1
            else:
                right = mid - 1

        # Adjust DRR for different periods
        total_days = len(date_range)
        period_length = total_days // 3
        drr_data = {}

        for i, date in enumerate(date_range):
            if i < period_length:
                multiplier = 0.9
            elif i < 2 * period_length:
                multiplier = 1.1
            else:
                multiplier = 1.3

            drr_data[date.strftime('%Y-%m-%d')] = int(base_drr * multiplier)

        results[product_name] = {'Current inventory': initial_inventory, **drr_data}

    result_df = pd.DataFrame.from_dict(results, orient='index')
    return result_df

# Update the main tabs section in your main() function:
# def main():
    # ... (previous code remains the same until tabs creation)
    
    # Create tabs with the new DRR Timeline tab
    # tabs = st.tabs(["Overview", "Inventory Status", "Shipment Planning", 
                    # "Loss Analysis", "Profit Analysis", "Maximum DRR Analysis", 
                    # "DRR Timeline"])
    
    # ... (previous tab content remains the same)
    
    # Add the new DRR Timeline tab
    # with tabs[6]:
    #     add_drr_timeline_tab()

def read_us_products_data(uploaded_file, sheet_name="US Products"):
    """Reads US Products sheet from Excel file and returns a DataFrame with ASIN, AWD, Backstock, and Upcoming Orders."""
    try:
        df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        df = df[['ASIN','Product Name', 'AWD', 'Backstock', 'Upcoming Orders']].dropna()
        return df
    except Exception as e:
        st.error(f"Error reading {sheet_name} sheet: {e}")
        return pd.DataFrame()
    
def calculate_us_shipment_plan(inventory_status, us_products_data, target_date):
    if target_date is None:
        target_date = datetime.now() + timedelta(days=30)

    target_date = pd.to_datetime(target_date)
    result = inventory_status.copy()

    # Filter inventory status to include only ASINs present in the US Products sheet
    result = result[result['ASIN'].isin(us_products_data['ASIN'])]

    # Calculate Days until Target
    result['Days_To_Target'] = (target_date - datetime.today()).days + 1
    result['Expected_Usage'] = (result['Daily_Run_Rate'] * result['Days_To_Target']).round()

    # Merge inventory data with US Products AWD, Backstock, and Upcoming Order
    result = result.merge(us_products_data, on='ASIN', how='left').fillna(0)
    result['Product Name'] = result['Product Name_x']

    # Display all columns (including AWD, Backstock, and Upcoming Orders)
    result = result[['ASIN', 'Product Name', 'Current Inventory', 'Daily_Run_Rate', 'Expected_Usage',
                     'Total Upcoming Shipment', 'Days_To_Target', 
                     'AWD', 'Backstock', 'Upcoming Orders']]

    # Adjust total available inventory
    result['Total Available Stocks with BS & AWD'] = result['Total Upcoming Shipment'] + result['AWD'] + result['Backstock'] 
    result['Total Available Stocks with BS,AWD & Orders'] = result['Total Upcoming Shipment'] + result['AWD'] + result['Backstock']+result['Upcoming Orders']

    # Calculate Required Projected Inventory
    # result['Required Projected Inventory With AWD & BS'] = (result['Expected_Usage'] - result['Total Available Stocks with BS & AWD']).round()
    result['Required Inventory(AWD+BS+ORDERS)'] = (result['Expected_Usage'] - result['Total Available Stocks with BS,AWD & Orders']).round()
    # Subtract AWD, Backstock, and Upcoming Orders from Required Projected Inventory
    # result['Final Required Shipment'] = result['Required Projected Inventory'] - result['AWD'] - result['Backstock'] - result['Upcoming Orders']

    # Ensure Final Required Shipment is not negative
    # result['Final Required Shipment'] = result['Final Required Shipment'].apply(lambda x: max(x, 0))
  
    result.to_csv('us_shipment_pla.csv', index=False)
    return result
def process_label_planning(uploaded_file, inventory_status, target_date=None):
    """Reads label data, merges with inventory data, and calculates label planning details."""
    try:
        # Read label data
        label_data = pd.read_excel(uploaded_file, sheet_name='labels')
        label_data = label_data[['ASIN', 'Product Name', 'IN Stocks', 'Packed', 'New Orders']].dropna()
    except Exception as e:
        st.error(f"Error reading labels sheet: {e}")
        return pd.DataFrame()
    
    if target_date is None:
        target_date = datetime.now() + timedelta(days=30)
    target_date = pd.to_datetime(target_date)
    
    # Copy inventory status and calculate expected usage
    result = inventory_status.copy()
    result['Days_To_Target'] = (target_date - datetime.today()).days + 1
    result['Expected_Usage'] = (result['Daily_Run_Rate'] * result['Days_To_Target']).round()
    
    # Merge label data
    result = result.merge(label_data, on='ASIN', how='left').fillna(0)
    result['Product Name'] = result['Product Name_x']
    
    # Calculate required inventory
    result['Total Available Label (Stocks+Packed)'] = result['Total Upcoming Shipment'] + result['IN Stocks'] + result['Packed'] 
    result['Total Available Label (Stocks+Packed+New Orders)'] = result['Total Available Label (Stocks+Packed)'] + result['New Orders']
    result['Required Labels (Stocks+Packed+New Orders)'] = (result['Expected_Usage'] - result['Total Available Label (Stocks+Packed+New Orders)']).round()
    
    return result[['Date','ASIN', 'Product Name', 'Current Inventory', 'Daily_Run_Rate', 'Expected_Usage',
                   'Total Upcoming Shipment', 'Days_To_Target', 'IN Stocks', 'Packed', 'New Orders',
                   'Total Available Label (Stocks+Packed)', 'Total Available Label (Stocks+Packed+New Orders)',
                   'Required Labels (Stocks+Packed+New Orders)']]
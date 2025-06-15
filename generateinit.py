import pandas as pd
import os

csv_file_path = 'customer_data.csv'
df = pd.read_csv(csv_file_path)

# Define the exact column names and their PostgreSQL types
column_definitions = {
    "Customer ID": "VARCHAR(50)",
    "Product": "VARCHAR(100)",
    "Quantity": "INTEGER",
    "Unit Price (USD)": "NUMERIC",
    "Total Price (USD)": "NUMERIC",
    "Purchase Date": "DATE",
    "Customer Name": "VARCHAR(255)",
    "Industry": "VARCHAR(100)",
    "Annual Revenue (USD)": "NUMERIC",
    "Number of Employees": "INTEGER",
    "Customer Priority Rating": "VARCHAR(50)",
    "Account Type": "VARCHAR(50)",
    "Location": "VARCHAR(255)",
    "Current Products": "VARCHAR(255)",
    "Product Usage (%)": "NUMERIC",
    "Cross-Sell Synergy": "VARCHAR(255)",
    "Last Activity Date": "DATE",
    "Opportunity Stage": "VARCHAR(100)"
}

if not list(df.columns) == list(column_definitions.keys()):
    print("ERROR: CSV columns do not match expected DDL columns. Please check your customer_data.csv.")
    print(f"Expected: {list(column_definitions.keys())}")
    print(f"Found: {list(df.columns)}")
    exit()

with open('init.sql', 'w') as f:
    f.write("-- init.sql\n")
    f.write("DROP TABLE IF EXISTS customer_purchases;\n") # Added to ensure clean slate on re-initialization
    f.write("CREATE TABLE customer_purchases (\n")
    
    ddl_statements = []
    for col_name, sql_type in column_definitions.items():
        ddl_statements.append(f'    "{col_name}" {sql_type}')
    f.write(",\n".join(ddl_statements) + "\n);\n\n")
    
    f.write("-- Insert sample data\n")
    
    for index, row in df.iterrows():
        values = []
        for col_name in column_definitions.keys():
            val = row[col_name]
            if pd.isna(val):
                values.append("NULL")
            elif col_name in ["Quantity", "Number of Employees"]:
                values.append(str(int(val)))
            elif col_name in ["Unit Price (USD)", "Total Price (USD)", "Annual Revenue (USD)", "Product Usage (%)"]:
                values.append(str(float(val)))
            elif col_name in ["Purchase Date", "Last Activity Date"]:
                if isinstance(val, pd.Timestamp):
                    values.append(f"'{val.strftime('%Y-%m-%d')}'")
                else:
                    try:
                        values.append(f"'{pd.to_datetime(val).strftime('%Y-%m-%d')}'")
                    except:
                        values.append("NULL")
            else:
                # Corrected line: Use double quotes for the replace arguments
                values.append(f"'{str(val).replace("'", "''")}'") 
        f.write(f"INSERT INTO customer_purchases VALUES ({','.join(values)});\n")
print("init.sql generated successfully.")

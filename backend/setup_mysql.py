import os
import sys
import getpass
from pathlib import Path

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

sql_file = Path(__file__).with_name('init_mysql.sql')
if not sql_file.exists():
    print('Error: init_mysql.sql not found in backend/.')
    sys.exit(1)

root_user = os.getenv('MYSQL_ROOT_USER', 'root')
root_password = os.getenv('MYSQL_ROOT_PASSWORD')
mysql_host = os.getenv('DB_HOST', 'localhost')

if not root_password:
    root_password = getpass.getpass(prompt='Enter MySQL root password: ')

print(f"Connecting to MySQL server at {mysql_host} as {root_user}...")

try:
    connection = mysql.connector.connect(
        host=mysql_host,
        user=root_user,
        password=root_password,
    )

    if not connection.is_connected():
        raise Error('Unable to establish connection')

    cursor = connection.cursor()
    sql_script = sql_file.read_text()
    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]

    for statement in statements:
        cursor.execute(statement)

    connection.commit()
    print('✓ Database and dedicated MySQL user created/updated successfully.')
    print('  You can now run the backend with DB_USER=pricing_app and DB_PASSWORD=PricingEngine@2026.')

except Error as err:
    print(f'Error initializing MySQL database: {err}')
    print('Tip: verify MYSQL_ROOT_USER and MYSQL_ROOT_PASSWORD values in backend/.env or enter the correct root password when prompted.')
    sys.exit(1)

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals() and connection.is_connected():
        connection.close()

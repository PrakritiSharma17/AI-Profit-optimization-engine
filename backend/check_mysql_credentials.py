import mysql.connector
from mysql.connector import Error

creds = [
    ("root", "Prakriti08"),
    ("root", ""),
    ("pricing_app", "PricingEngine@2026"),
]

for user, password in creds:
    try:
        conn = mysql.connector.connect(host="localhost", user=user, password=password)
        print('OK', user, repr(password))
        conn.close()
    except Error as e:
        print('ERR', user, repr(password), e)

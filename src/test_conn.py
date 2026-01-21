
import mysql.connector

cloud_config = {
    'host': 'bj6praqdpuirvzoqna22-mysql.services.clever-cloud.com',
    'database': 'bj6praqdpuirvzoqna22',
    'user': 'uefcnqzqensby1sf',
    'password': 'OvHa0yP4p1XVa4aUCEXt',
    'port': 3306
}

try:
    conn = mysql.connector.connect(**cloud_config)
    print("Cloud Connection: SUCCESS")
    conn.close()
except Exception as e:
    print(f"Cloud Connection: FAILED - {e}")

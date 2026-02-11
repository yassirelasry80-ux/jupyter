import oracledb
import os
import sys

# Configuration for Thick Mode
# On Linux (Docker), if LD_LIBRARY_PATH is set correctly (which we did in Dockerfile),
# we can just call init_oracle_client() without arguments, or pointing to the lib.

try:
    print("Initializing Oracle Client...")
    # This forces Thick mode. If libraries are missing, it will raise DPI-1047
    oracledb.init_oracle_client()
    print("Oracle Client Initialized Successfully (Thick Mode enabled).")
    
    version = oracledb.clientversion()
    print(f"Client Version: {version}")

except oracledb.DatabaseError as e:
    error, = e.args
    print(f"Error initializing Oracle Client: {error.message}")
    print("Ensure LD_LIBRARY_PATH is set and points to the instant client directory.")
    sys.exit(1)

# If credentials are provided via env vars, attempt connection
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
dsn = os.getenv('DB_DSN')

if user and password and dsn:
    try:
        print(f"Attempting connection to {dsn} as {user}...")
        connection = oracledb.connect(user=user, password=password, dsn=dsn)
        print("Connection successful!")
        
        # Check DB version
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM v$version")
        for row in cursor:
            print(row[0])
            
        connection.close()
    except oracledb.DatabaseError as e:
        error, = e.args
        print(f"Connection failed: {error.message}")
else:
    print("No DB credentials found in environment variables. Skipping connection test.")
    print("To test connection, set DB_USER, DB_PASSWORD, and DB_DSN in docker-compose.yml")

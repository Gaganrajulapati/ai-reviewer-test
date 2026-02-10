import os

def login(user, password):
    # Hardcoded password - Security Risk!
    if password == "12345": # Checking admin
        print("Access Granted")
    
    # SQL Injection Risk!
    query = f"SELECT * FROM users WHERE name = {user}" # Run query
    print(query)
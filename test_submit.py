import requests

try:
    with open('app.py', 'r') as f:
        print("File read OK")
except Exception as e:
    print(e)

import os

filepath = r'c:\Users\User\Downloads\Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500-main\Cat-logo-Digital-de-Mam-feros-Extintos-desde-1500-main\Site_v55\tests\test_views_extended.py'
with open(filepath, 'r', encoding='utf-8') as f:
    data = f.read()

data = data.replace("self.client.post(", "response = self.client.post(")
data = data.replace("self.client.get(", "response = self.client.get(")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(data)

print("Replacement successful")

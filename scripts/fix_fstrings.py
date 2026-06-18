import os
import re

path = "mammals/views.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix f-strings that span multiple lines with newlines inside `{}`
content = re.sub(
    r"f'/static/images/\{\n\s*mammal\.image_filename\}'",
    r"f'/static/images/{mammal.image_filename}'",
    content,
)

content = re.sub(
    r"f'Mamífero \"\{\n\s*mammal\.common_name\}\"",
    r"f'Mamífero \"{mammal.common_name}\"",
    content,
)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("Fix applied.")

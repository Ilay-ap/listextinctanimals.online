import os

with open("mammals/views.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

old_block_pattern = r"# Obter coordenadas do arquivo JSON.*?map_data = \{\n\s+'coordinates': coordinates,\n\s+'center': \{'lat': avg_lat, 'lon': avg_lon\},\n\s+'zoom': zoom,\n\s+\}"

new_block = """# Obter coordenadas diretamente do banco de dados (já auditado)
    map_data = None
    if mammal_obj.latitude is not None and mammal_obj.longitude is not None:
        location_name = "Desconhecido"
        if mammal_obj.distribution:
            location_name = str(mammal_obj.distribution).split(',')[0].strip()
            
        map_data = {
            'coordinates': [{'lat': mammal_obj.latitude, 'lon': mammal_obj.longitude, 'location': location_name}],
            'center': {'lat': mammal_obj.latitude, 'lon': mammal_obj.longitude},
            'zoom': 5,
        }"""

content = re.sub(old_block_pattern, new_block, content, flags=re.DOTALL)

with open("mammals/views.py", "w", encoding="utf-8") as f:
    f.write(content)
print("mammal_detail patched.")

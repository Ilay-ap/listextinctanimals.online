import os
import re

with open("mammals/views.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix global_map_data
old_global = '''def global_map_data(request):
    """Endpoint JSON com dados de todas as espécies para o mapa global"""
    try:
        # Buscar todos os mamíferos do banco de dados - apenas campos necessários
        mammals = Mammal.objects.only(
            'id', 'common_name', 'binomial_name', 'continent', 'image_filename'
        ).all()
        
        # Estrutura para armazenar dados agregados por localização
        location_data = {}
        # Processar cada mamifero uma unica vez
        for mammal in mammals:
            lat = mammal.latitude
            lon = mammal.longitude
            
            geocoding_info = GEOCODING_DATA.get(mammal.pk)
            location_raw = ""
            if geocoding_info and geocoding_info.get('coordinates'):
                coords = geocoding_info['coordinates']
                location_raw = coords[0].get('location', '')
                if lat is None:
                    lat = coords[0].get('lat', 0)
                if lon is None:
                    lon = coords[0].get('lon', 0)
            
            if lat is None or lon is None:
                continue
                
            # Extrair pais
            if not location_raw and mammal.distribution:
                location_raw = mammal.distribution.strip().split('\\n')[0].split(',')[0].strip()'''

new_global = '''def global_map_data(request):
    """Endpoint JSON com dados de todas as espécies para o mapa global"""
    try:
        # Buscar todos os mamíferos do banco de dados - incluindo latitude, longitude e distribuição
        mammals = Mammal.objects.only(
            'id', 'common_name', 'binomial_name', 'continent', 'image_filename', 'latitude', 'longitude', 'distribution'
        ).all()
        
        # Estrutura para armazenar dados agregados por localização
        location_data = {}
        # Processar cada mamifero uma unica vez
        for mammal in mammals:
            lat = mammal.latitude
            lon = mammal.longitude
            
            if lat is None or lon is None:
                continue
                
            location_raw = "Desconhecido"
            if mammal.distribution:
                location_raw = str(mammal.distribution).strip().split('\\n')[0].split(',')[0].strip()'''

# Instead of exact replace, I'll use regex to nuke the old logic
content = re.sub(
    r"def global_map_data.*?if lat is None or lon is None:\s+continue.*?if not location_raw and mammal.distribution:.*?location_raw = mammal.distribution.*?strip\(\)",
    new_global,
    content,
    flags=re.DOTALL,
)

with open("mammals/views.py", "w", encoding="utf-8") as f:
    f.write(content)
print("global_map_data patched.")

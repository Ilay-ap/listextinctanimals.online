import os
import re

with open("templates/mammals/global_map.html", "r", encoding="utf-8") as f:
    content = f.read()

pattern = r'<div class="map-stat-card">\s*<div>\s*<div class="map-stat-value" id="stat-locations">-</div>\s*<div class="map-stat-label">\{% trans "Locations on Map" %\}</div>\s*</div>\s*</div>'

content = re.sub(pattern, "", content)

with open("templates/mammals/global_map.html", "w", encoding="utf-8") as f:
    f.write(content)
print("Removed Locations on Map stat card.")

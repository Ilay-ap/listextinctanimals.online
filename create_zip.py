import os
import zipfile

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        # Exclude pycache and hidden git folders
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.pytest_cache', '.git')]
        for file in files:
            if file.endswith('.zip') or file == "zip_project.py":
                continue
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, path)
            ziph.write(file_path, arcname)

zipf = zipfile.ZipFile('listextinctanimals_production.zip', 'w', zipfile.ZIP_DEFLATED)
zipdir('.', zipf)
zipf.close()
print("Zip criado com sucesso: listextinctanimals_production.zip")

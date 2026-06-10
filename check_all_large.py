import os

def check_all_large_files(start_path):
    sizes = []
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp) and '.git' not in fp:
                size_mb = os.path.getsize(fp) / (1024*1024)
                sizes.append((size_mb, fp))
    
    sizes.sort(reverse=True)
    for s, fp in sizes[:15]:
        print(f"{fp}: {s:.2f} MB")
    
    print(f"Total uncompressed size (without .git): {sum(s for s, fp in sizes):.2f} MB")

check_all_large_files('.')

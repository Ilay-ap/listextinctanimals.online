import os


def check_large_files(start_path):
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                size_mb = os.path.getsize(fp) / (1024 * 1024)
                if size_mb > 1:
                    print(f"{fp}: {size_mb:.2f} MB")


check_large_files("./static")

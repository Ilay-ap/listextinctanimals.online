import os

def get_dir_sizes(start_path = '.'):
    for entry in os.listdir(start_path):
        full_path = os.path.join(start_path, entry)
        if os.path.isdir(full_path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(full_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
            size_mb = total_size / (1024*1024)
            if size_mb > 1:
                print(f"{entry}: {size_mb:.2f} MB")

get_dir_sizes('.')

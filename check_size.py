import os

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

print(f"Total size: {get_size('.') / (1024*1024):.2f} MB")
print(f"Media size: {get_size('./media') / (1024*1024):.2f} MB")
try:
    print(f"Static size: {get_size('./static') / (1024*1024):.2f} MB")
except:
    pass
try:
    print(f"Staticfiles size: {get_size('./staticfiles') / (1024*1024):.2f} MB")
except:
    pass

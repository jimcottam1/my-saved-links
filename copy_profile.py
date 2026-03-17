import shutil, os

src = r"C:\Users\jim_c\AppData\Local\Google\Chrome\User Data"
dst = r"C:\Users\jim_c\ChromePW"

SKIP_DIRS = {"Cache", "Code Cache", "GPUCache", "ShaderCache", "DawnCache", "CrashPad"}

def copy_tree(s, d):
    os.makedirs(d, exist_ok=True)
    try:
        entries = list(os.scandir(s))
    except Exception:
        return
    for item in entries:
        if item.is_dir():
            if item.name in SKIP_DIRS:
                continue
            copy_tree(item.path, os.path.join(d, item.name))
        else:
            try:
                shutil.copy2(item.path, os.path.join(d, item.name))
            except Exception:
                pass

print("Copying Chrome profile (excluding cache)...")
copy_tree(src, dst)
print("Done! Profile copied to:", dst)

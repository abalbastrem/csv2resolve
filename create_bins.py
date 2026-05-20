### For Davinci Resolve v20, 
### copy this script into ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility
### run from Davinci Resolve itself. Workspace > scripts.

# DaVinci Resolve - Create Bin Structure
# clips/
#   - mc
#   - mc_pending
#   - offline
#   - online
if not resolve:
    raise RuntimeError("PANIC: Could not connect to resolve")
else:
    print("successfully connected to resolve")

pm = resolve.GetProjectManager()
project = pm.GetCurrentProject()
media_pool = project.GetMediaPool()

# --- CONFIG ---
SUBFOLDERS = ["mc", "mc_pending", "offline", "online"]
ROOT_NAME = "clips"

# def get_or_create_folder(parent, name):
#     """
#     Finds or creates a folder under the given parent.
#     """
#     root = parent.GetRootFolder()
    
#     def search(folder):
#         for f in folder.GetSubFolders():
#             if f.GetName() == name:
#                 return f
#         return None

#     found = search(root)
#     if found:
#         return found

#     return media_pool.AddSubFolder(root, name)

# def ensure_structure():
#     root = media_pool.GetRootFolder()

#     # Create / get top folder "clips"
#     clips = None
#     for f in root.GetSubFolders():
#         if f.GetName() == BIN_ROOT:
#             clips = f
#             break

#     if not clips:
#         clips = media_pool.AddSubFolder(root, BIN_ROOT)

#     # Subfolders
#     names = BIN_NAMES

#     existing = {f.GetName(): f for f in clips.GetSubFolders()}

#     for name in names:
#         if name not in existing:
#             media_pool.AddSubFolder(clips, name)

# ensure_structure()

# print("Bin structure created under 'clips'")


def get_subfolders(folder):
    # Compatible amb APIs que retornen Folder objects
    try:
        return folder.GetSubFolderList()
    except:
        return []


def find_folder(parent, name):
    for f in get_subfolders(parent):
        if f and f.GetName() == name:
            return f
    return None


def ensure_folder(parent, name):
    folder = find_folder(parent, name)
    if folder:
        return folder
    return media_pool.AddSubFolder(parent, name)


def ensure_structure():
    root = media_pool.GetRootFolder()

    # Create / find "clips"
    clips = find_folder(root, ROOT_NAME)
    if not clips:
        clips = media_pool.AddSubFolder(root, ROOT_NAME)

    # Create subfolders
    for name in SUBFOLDERS:
        ensure_folder(clips, name)

    print("Bin structure created under 'clips'")


ensure_structure()
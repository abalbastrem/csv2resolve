### For Davinci Resolve v20, 
### copy this script into ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility
### run from Davinci Resolve itself. Workspace > scripts.

# This script DOES NOT generate multicam clips. It simply find B cams in the filesystem for every A cam in the mediapool and puts them both in a bin.
# Then multicams must be created manually by selecting both clips, rightclick 'Create new multicam clip using selected clips...' and choosing the appropiate options.
if not resolve:
    raise RuntimeError("PANIC: Could not connect to resolve")
else:
    print("successfully connected to resolve")

import os
import sys

pm = resolve.GetProjectManager()
project = pm.GetCurrentProject()
mediaPool = project.GetMediaPool()
rootFolder = mediaPool.GetRootFolder()

print("all resources instantiated")

# --- CONFIG ---
OFFLINE_BIN_NAME = "clips/offline"
MC_PENDING_BIN_NAME = "clips/mc_pending"
INGRESS_BIN_NAMES = "clips/online", "clips/single"

# --- Helpers ---

def find_or_create_bin_path(root, path):
    parts = path.split("/")
    current = root

    for part in parts:
        found = None

        for sub in current.GetSubFolderList():
            if sub.GetName() == part:
                found = sub
                break

        if not found:
            found = mediaPool.AddSubFolder(current, part)

        current = found

    return current

def get_clips_from_bins(root, bin_names):
    clips = []

    for bin_path in bin_names:
        folder = find_or_create_bin_path(root, bin_path)
        if not folder:
            print(f"[WARN] Bin not found: {bin_path}")
            continue

        clips += get_all_clips(folder)

    return clips

def print_clips(clips):
    for clip in clips:
        print(clip.GetName())

def get_all_clips(folder):
    clips = folder.GetClipList()
    for sub in folder.GetSubFolderList():
        clips += get_all_clips(sub)
    return clips

def get_clips_a(all_clips):
    clips_a = list()
    for clip in all_clips:
        if not clip.GetName().endswith("_a.mp4"):
            continue
        if clip.GetClipProperty("Type") == "Multicam":
            continue
        clips_a.append(clip)
    return clips_a

def get_clips_b(all_clips):
    clips_b = list()
    for clip in all_clips:
        if not clip.GetName().endswith("_b.mp4"):
            continue
        if clip.GetClipProperty("Type") == "Multicam":
            continue
        clips_b.append(clip)
    return clips_b

def get_clips_mc(all_clips):
    clips_mc = list()
    for clip in all_clips:
        if not clip.GetName().endswith("_mc"):
            continue
        if not clip.GetClipProperty("Type") == "Multicam":
            continue
        clips_mc.append(clip)
    return clips_mc

### GET INITIAL CLIPS ###
# --- 0. Ensure there are no clips in offline bin ---
offline_clips = get_clips_from_bins(rootFolder, [OFFLINE_BIN_NAME])

if len(offline_clips) > 0:
    print("")
    print("################################################")
    print("ERROR: Offline bin is not empty.")
    print("Remove all clips from clips/offline before running this script.")
    print("Found:")
    print_clips(offline_clips)
    print("################################################")
    print("")
    print("FAIL")
    sys.exit(1)

# --- 1.1 Get all clips ---
all_clips = get_clips_from_bins(rootFolder, INGRESS_BIN_NAMES)
print("ALL CLIPS in ", INGRESS_BIN_NAMES)
print_clips(all_clips)

# --- 1.1 Get A clips ---
clips_a = get_clips_a(all_clips)
print("A CLIPS")
print_clips(clips_a)

# --- 2.1 Import all B clips from filesystem ---

def find_clipB_path(clipA):
    # Path complet del fitxer A
    file_path = clipA.GetClipProperty("File Path")
    folder = os.path.dirname(file_path)
    file_name = clipA.GetName()

    # Separar base i extensió
    base, ext = os.path.splitext(file_name)

    # Treure _a
    if not base.endswith("_a"):
        return None

    base_clean = base[:-2]  # treu "_a"

    # Construir nom B
    clipB_name = base_clean + "_b" + ext

    # Path complet B
    clipB_path = os.path.join(folder, clipB_name)

    return clipB_path

clips_b = list()
for clipA in clips_a:
    camB_path = find_clipB_path(clipA)

    if not os.path.exists(camB_path):
        print(f"[MISS] No camB file: {camB_path}")
        continue

    print(f"[FOUND] camB: {camB_path}")

    clip_b = mediaPool.ImportMedia([camB_path])

    if not clip_b:
        print(f"[ERROR] Could not import {camB_path}")

    clips_b.append(clip_b)


# --- 3. Group clips by naming pattern ---
all_clips = get_clips_from_bins(rootFolder, INGRESS_BIN_NAMES)

groups = {}

for clip in all_clips:
    name = clip.GetName()
    base, ext = os.path.splitext(name)

    if base.endswith("_a"):
        key = base[:-2]
        groups.setdefault(key, {})["a"] = clip

    elif base.endswith("_b"):
        key = base[:-2]
        groups.setdefault(key, {})["b"] = clip

# --- 4. Prepare multicam pending bin ---
mc_pending_bin = find_or_create_bin_path(rootFolder, MC_PENDING_BIN_NAME)
print("created multicam pending bin")

# --- 5. Move A/B couples to mc_pending ---
for base, cams in groups.items():

    if "a" not in cams or "b" not in cams:
        print(f"[SKIP] incomplete pair: {base}")
        continue

    clipA = cams["a"]
    clipB = cams["b"]

    print(f"[MOVE] {base}")

    mediaPool.MoveClips([clipA, clipB], mc_pending_bin)

print("SUCCESS")
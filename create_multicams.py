if not resolve:
    raise RuntimeError("PANIC: Could not connect with resolve")
else:
    print("successfully connected to resolve")

import re

pm = resolve.GetProjectManager()
project = pm.GetCurrentProject()
mediaPool = project.GetMediaPool()
rootFolder = mediaPool.GetRootFolder()

print("all resources instantiated")

# --- CONFIG ---
MC_BIN_NAME = "mc"
SUFFIX_MC = "_mc"

# --- Helpers ---

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

def find_or_create_bin(parent, name):
    for sub in parent.GetSubFolderList():
        if sub.GetName() == name:
            return sub
    return mediaPool.AddSubFolder(parent, name)

### GET INITIAL CLIPS ###
# --- 1.1 Get all clips ---
all_clips = get_all_clips(rootFolder)
print("ALL CLIPS")
print_clips(all_clips)

# --- 1.1 Get A clips ---
clips_a = get_clips_a(all_clips)
print("A CLIPS")
print_clips(clips_a)

# clips_b = get_clips_b(all_clips)
# print("B CLIPS")
# print_clips(clips_b)

# clips_mc = get_clips_mc(all_clips)
# print("MC CLIPS")
# print_clips(clips_mc)

# --- 2.1 Import all B clips from filesystem ---

import os

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
all_clips = get_all_clips(rootFolder)

print_clips(all_clips)

# groups = {}
# pattern = re.compile(r"(.+)_([ab])$", re.IGNORECASE)

# for clip in all_clips:
#     name = clip.GetName()
#     match = pattern.match(name)
    
#     if not match:
#         continue
    
#     base = match.group(1)
#     cam = match.group(2).lower()
    
#     if base not in groups:
#         groups[base] = {}
    
#     groups[base][cam] = clip

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

print(groups)
print("grouped clips")

# --- 4. Prepare multicam bin ---
# mc_bin = find_or_create_bin(rootFolder, MC_BIN_NAME)
# print("created multicam bin")

# --- 5. Crear multicams ---
# for base, cams in groups.items():
#     mc_name = base + SUFFIX_MC

#     # Skip si ja existeix
#     if mc_name in existing_mc:
#         print(f"[SKIP] Existinc multicam: {mc_name}")
#         continue

#     # Validació de càmeres
#     if "a" not in cams or "b" not in cams:
#         if "a" not in cams:
#             print(f"[WARN] Missing camA for: {base}")
#         if "b" not in cams:
#             print(f"[WARN] Missing camB for: {base}")
#         continue

#     clipA = cams["a"]
#     clipB = cams["b"]

#     print(f"[OK] Creating multicam: {mc_name}")

#     multicam = mediaPool.CreateMulticamClip([clipA, clipB])

#     if multicam:
#         multicam.SetClipProperty("Clip Name", mc_name)
#         mediaPool.MoveClips([multicam], mc_bin)
#     else:
#         print(f"[ERROR] Could not create multicam: {base}")

# print("created multicams")
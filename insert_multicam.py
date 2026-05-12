# master2multicam_timeline.py
#
# Crea una nova timeline basada en la timeline actual.
# Substitueix clips acabats en "_a" pels seus equivalents "_mc"
# trobats al bin "mc".
#
# Exemple:
#   alfredo_a  -> alfredo_mc
#
# Clips sense multicam:
#   es mantenen tal qual.
#
# IMPORTANT:
# - Executar des de Resolve
# - Timeline original ha d'estar oberta/seleccionada
# - Els multicams han de ser al bin "mc"

import sys

if not resolve:
    raise RuntimeError("PANIC: Could not connect with resolve")
else:
    print("successfully connected to resolve")

pm = resolve.GetProjectManager()
project = pm.GetCurrentProject()

if not project:
    raise RuntimeError("No current project")

mediaPool = project.GetMediaPool()
rootFolder = mediaPool.GetRootFolder()

timeline = project.GetCurrentTimeline()

if not timeline:
    raise RuntimeError("No current timeline")

print("Current timeline:", timeline.GetName())


# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

BIN_CLIPS_MC = "clips/mc"
MC_SUFFIX = "_mc"
CAM_A_SUFFIX = "_a"

NEW_TIMELINE_NAME = timeline.GetName() + "_mc"


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def find_bin_by_path(root, path):
    """
    Find a Media Pool bin recursively using a slash-separated path.

    Example:
        "clips/2mc_done"
    """

    path_parts = path.split("/")
    current = root
    for part in path_parts:
        found = None
        for sub in current.GetSubFolderList():
            if sub.GetName() == part:
                found = sub
                break
        if not found:
            return None
        current = found
    return current


def get_all_clips(folder):
    clips = folder.GetClipList()

    for sub in folder.GetSubFolderList():
        clips += get_all_clips(sub)

    return clips

### TEST
# mc_bin = find_bin_by_path(rootFolder, BIN_CLIPS_MC)
# clips = mc_bin.GetClipList()
# print("DIR CLIP")
# print(dir(clips[0]))
# print("GET PROPERTY")
# print(dir(clips[0].GetProperty()))
# sys.exit(0)


# ------------------------------------------------------------
# FIND MC BIN
# ------------------------------------------------------------

mc_bin = find_bin_by_path(rootFolder, BIN_CLIPS_MC)

if not mc_bin:
    raise RuntimeError(f"Could not find bin: {BIN_CLIPS_MC}")

print("Found multicam bin:", mc_bin.GetName())


# ------------------------------------------------------------
# BUILD MULTICAM MAP
# str basename -> clip basename_mc
# ------------------------------------------------------------

multicam_map = {}

mc_clips = get_all_clips(mc_bin)

for clip in mc_clips:

    clip_type = clip.GetClipProperty("Type")
    clip_name = clip.GetName()

    if clip_type != "Multicam":
        print(f"[WARN] Following clip is not multicam: {clip_name}")
        continue

    if not clip_name.endswith(MC_SUFFIX):
        print(f"[WARN] Multicam without _mc suffix: {clip_name}")
        continue

    base_name = clip_name[:-len(MC_SUFFIX)]

    multicam_map[base_name] = clip

    print(f"[MC] {base_name} -> {clip_name}")

print("Total multicams:", len(multicam_map))


# ------------------------------------------------------------
# LAY MULTICAM TO TIMELINE
# ------------------------------------------------------------

import os

video_track_count = timeline.GetTrackCount("video")
timeline.AddTrack("video")

for track_index in range(1, video_track_count + 1):

    print(f"\n=== TRACK {track_index} ===")

    items = timeline.GetItemListInTrack("video", track_index)

    if not items:
        continue

    for item in items:
        media_pool_item = item.GetMediaPoolItem()
        if not media_pool_item:
            print("[SKIP] No media pool item")
            continue
        source_name = media_pool_item.GetName()
        clip_name, ext = os.path.splitext(source_name)
        source_clip = media_pool_item

        # ----------------------------------------------------
        # MULTICAM REPLACEMENT
        # ----------------------------------------------------

        if clip_name.endswith(CAM_A_SUFFIX):
            base_name = clip_name[:-len(CAM_A_SUFFIX)]
            if base_name in multicam_map:
                source_clip = multicam_map[base_name]
                print(f"[REPLACE] {source_name} -> {source_clip.GetName()}")
                item.SetClipColor("Orange")
            else:
                print(f"[KEEP] No multicam for: {source_name}")

        # ----------------------------------------------------
        # TIMECODE DATA
        # ----------------------------------------------------

        fps = float(media_pool_item.GetClipProperty("FPS"))
        timeline_fps = float(project.GetSetting("timelineFrameRate"))

        # frames -> time
        start_sec = item.GetSourceStartFrame() / fps
        end_sec = item.GetSourceEndFrame() / fps

        start_tl = start_sec * timeline_fps
        end_tl = end_sec * timeline_fps

        # time -> frames
        start_frame = int(round(start_sec * timeline_fps))
        end_frame = int(round(end_sec * timeline_fps))

        record_frame = item.GetStart()

        # ----------------------------------------------------
        # APPEND
        # ----------------------------------------------------

        clip_info = {
            "mediaPoolItem": source_clip,
            "startFrame": start_frame,
            "endFrame": end_frame,
            "recordFrame": record_frame,
            "trackIndex": 2,
            "mediaType": 1
        }

        # audio_info = {
        #     "mediaPoolItem": source_clip,
        #     "startFrame": start_frame,
        #     "endFrame": end_frame,
        #     "recordFrame": record_frame,
        #     "trackIndex": 2,
        #     "mediaType": 2
        # }

        result = mediaPool.AppendToTimeline([clip_info])

        if not result:
            print(f"[ERROR] Could not append: {source_name}")

print("\nDONE")
# En la pista de video MULTICAM, posa clips _mc equivalents als _a de la pista de vídeo original.
# La resta de clips es copia a aquesta pista MULTICAM tal qual.
#
# Exemple:
#   V1 alfredo_a  -> V2 (MULTICAM) alfredo_mc
#   V1 juicio2007 -> V2 (MULTICAM) juicio2007
#
# IMPORTANT:
# - Executar des de Resolve
# - Timeline original ha d'estar oberta/seleccionada
# - Tots els multicams han de ser al bin "mc". L'script fallarà si no els troba primer.

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

def validate_all_multicams_exist(timeline, multicam_map):
    """
    Verifica que tots els clips *_a presents a la timeline
    tenen el seu multicam corresponent al multicam_map.

    Si en falta algun, imprimeix la llista completa i falla.
    """

    import os

    missing_multicams = set()

    video_track_count = timeline.GetTrackCount("video")

    for track_index in range(1, video_track_count + 1):

        items = timeline.GetItemListInTrack("video", track_index)

        if not items:
            continue

        for item in items:

            media_pool_item = item.GetMediaPoolItem()
            if not media_pool_item:
                continue

            source_name = media_pool_item.GetName()
            clip_name, ext = os.path.splitext(source_name)
            if not clip_name.endswith(CAM_A_SUFFIX):
                continue

            base_name = clip_name[:-len(CAM_A_SUFFIX)]
            if base_name not in multicam_map:
                missing_multicams.add(base_name)

    if missing_multicams:

        print("")
        print("################################################")
        print("ERROR: Missing multicam clips")
        print("")

        for base_name in sorted(missing_multicams):
            print(f"  {base_name}{MC_SUFFIX}")

        print("")
        print("################################################")

        print(f"Missing {len(missing_multicams)} multicam clips")
        print("")
        print("FAIL")
        sys.exit(1)

    print("[OK] All required multicams found")

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


def get_all_clips(bin):
    clips = bin.GetClipList()

    for sub in bin.GetSubFolderList():
        clips += get_all_clips(sub)

    return clips


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

validate_all_multicams_exist(timeline, multicam_map)


# ------------------------------------------------------------
# LAY MULTICAM TO TIMELINE
# ------------------------------------------------------------

import os

video_track_count = timeline.GetTrackCount("video")

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
            source_clip = multicam_map[base_name]
            print(f"[REPLACE] {source_name} -> {source_clip.GetName()}")
            item.SetClipColor("Orange")

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

        result = mediaPool.AppendToTimeline([clip_info])

        if not result:
            print(f"[ERROR] Could not append: {source_name}")

print("\nDONE")
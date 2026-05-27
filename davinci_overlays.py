### For Davinci Resolve v20, 
### copy this script into ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility
### run from Davinci Resolve itself. Workspace > scripts.

import os
import csv
import sys

# =========================
# CONFIG
# =========================

# CSV
CSV_PATH = r"C:\Users\bulbastre\Videos\proves\timeline.csv"
COLUMN_TAGS = "TAGS"
COLUMN_TOPIC = "TOPIC"
COLUMN_LACKS_SOURCE = "LACKS SOURCE?"
COLUMN_SOURCES = "FUENTES"
COLUMN_COMMENTS = "COMMENTS"

# RESOLVE
TEMPLATE_FOLDER = "overlays"
TEMPLATE_TAG = "TAG+"
TEMPLATE_TOPIC = "TOPIC+"
TEMPLATE_SRC_LACKING = "SRC_lacking"
TEMPLATE_SOURCES = "sources"
TEMPLATE_COMMENTS = "comments"

TRACK_VIDEO = 1
TRACK_TAG = 2
TRACK_SRC_LACKING = 3
TRACK_SOURCES = 4
TRACK_COMMENTS = 5

TRACK_NAMES = {
    TRACK_VIDEO: "VIDEO",
    TRACK_TAG: "TAG",
    TRACK_SRC_LACKING: "SRC_LACKING",
    TRACK_SOURCES: "SOURCES",
    TRACK_COMMENTS: "COMMENTS",
}


# =========================
# CSV LOADING
# =========================

def read_csv(path):
    if not os.path.exists(path):
        print(f"[ERROR] CSV not found: {path}")
        return []

    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


# =========================
# RESOLVE HELPERS (STUBS)
# =========================
# These assume Resolve API context is available


def find_template(media_pool, name):
    """
    Finds a template clip inside Power Bin folder.
    """
    root = media_pool.GetRootFolder()
    folders = root.GetSubFolderList()

    for f in folders:
        if f.GetName() == TEMPLATE_FOLDER:
            clips = f.GetClipList()
            for c in clips:
                if c.GetName() == name:
                    return c
    return None


def ensure_video_tracks(timeline, track_names):
    required_count = max(track_names.keys())

    current = timeline.GetTrackCount("video")

    while current < required_count:
        timeline.AddTrack("video")
        current += 1

    for index, name in track_names.items():
        timeline.SetTrackName("video", index, name)


def add_clip(timeline, clip, track, start_frame, end_frame):
    """
    Inserts clip and sets track/duration.
    """
    items = timeline.AppendToTimeline([clip])
    if not items:
        return None

    item = items[0]

    item.SetStartFrame(start_frame)
    item.SetEndFrame(end_frame)
    item.SetTrackIndex(track)

    return item


# =========================
# MAIN LOGIC
# =========================

def set_textplus_text(timeline_item, text):

    fusion = timeline_item.GetFusionCompByIndex(1)

    if not fusion:
        print("[ERROR] No Fusion comp found (probably not Text+)")
        return False

    tools = fusion.GetToolList()

    for _, tool in tools.items():

        # Text+ node IDs can vary slightly
        if hasattr(tool, "StyledText"):
            try:
                tool.StyledText = text
                return True
            except:
                pass

        if tool.GetInput("StyledText") is not None:
            tool.SetInput("StyledText", text)
            return True

    print("[ERROR] No Text+ node found")
    return False

def append_overlay(media_pool, template, track_index, timeline_start, record_frame, duration):
    """
    Creates a timeline overlay instance from a MediaPool template.
    """

    clip_info = {
        "mediaPoolItem": template,

        # source range inside template
        "startFrame": 0,
        "endFrame": duration,

        # destination in timeline
        "recordFrame": timeline_start + record_frame,
        "trackIndex": track_index,
    }

    result = media_pool.AppendToTimeline([clip_info])

    if not result:
        print(f"[ERROR] Failed to append overlay to V{track_index}")
        return None

    return result[0]

def build_overlays(csv_rows):
    project = resolve.GetProjectManager().GetCurrentProject()
    media_pool = project.GetMediaPool()
    timeline = project.GetCurrentTimeline()
    timeline_start = timeline.GetStartFrame()

    ensure_video_tracks(timeline, TRACK_NAMES)

    for row in csv_rows:
        if bool(row.get("CHECK")) != True:
            continue

        # =====================================
        # TIME BASE
        # =====================================

        try:
            start = int(row.get("fTL_IN", 0))
            end = int(row.get("fTL_OUT", 0))
        except Exception:
            print("[WARNING] Invalid frame data, skipping row")
            continue

        duration = end - start

        if duration <= 0:
            print("[WARNING] Invalid duration, skipping row")
            continue


        # =====================================
        # TAG  → V2
        # =====================================

        tag_value = row.get(COLUMN_TAGS, "").strip()

        if tag_value:

            template = find_template(media_pool, TEMPLATE_TAG)

            if not template:
                print("PANIC: no {TEMPLATE_TAG} template")
                return

            item = append_overlay(
                media_pool,
                template,
                TRACK_TAG,
                timeline_start,
                start,
                duration
            )

            if not item:
                print("PANIC: {TEMPLATE_TAG} {tag_value} could not be added")
                sys.exit(1)
            
            set_textplus_text(item, tag_value)
            item.SetName(f"TAG_{tag_value}")

            print(item)
            print(item.GetName())
            print(item.GetFusionCompByIndex(0))
            print(item.GetFusionCompCount())
            print(item.GetFusionCompNameList())


        # =====================================
        # SRC_LACKING → V3
        # =====================================

        lacks_source = row.get(COLUMN_LACKS_SOURCE, "").strip().lower()

        if lacks_source == "true":

            template = find_template(
                media_pool,
                TEMPLATE_SRC_LACKING
            )

            if not template:
                print("PANIC: no SRC_LACKING template")
                return

            item = append_overlay(
                media_pool,
                template,
                TRACK_SRC_LACKING,
                timeline_start,
                start,
                duration
            )

            if item:
                item.SetName("SRC_LACKING")


        # =====================================
        # SOURCES → V4
        # =====================================

        sources_value = row.get(COLUMN_SOURCES, "").strip()

        if sources_value:

            template = find_template(
                media_pool,
                TEMPLATE_SOURCES
            )

            if not template:
                print("PANIC: no SOURCES template")
                return

            item = append_overlay(
                media_pool,
                template,
                TRACK_SOURCES,
                timeline_start,
                start,
                duration
            )

            if item:
                item.SetName(f"SOURCES_{sources_value}")


        # =====================================
        # COMMENTS → V5
        # =====================================

        comments_value = row.get(COLUMN_COMMENTS, "").strip()

        if comments_value:

            template = find_template(
                media_pool,
                TEMPLATE_COMMENTS
            )

            if not template:
                print("PANIC: no COMMENTS template")
                return

            item = append_overlay(
                media_pool,
                template,
                TRACK_COMMENTS,
                timeline_start,
                start,
                duration
            )

            if item:
                item.SetName(f"COMMENTS_{comments_value}")


        # =====================================
        # TOPIC
        # =====================================
        # intentionally skipped for now


def main():
    rows = read_csv(CSV_PATH)
    print(f"[INFO] Loaded rows: {len(rows)}")
    build_overlays(rows)
    print("[DONE]")


if __name__ == "__main__":
    main()
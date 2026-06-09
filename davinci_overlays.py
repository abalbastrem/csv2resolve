### For Davinci Resolve v20, 
### copy this script into ProgramData\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility
### run from Davinci Resolve itself. Workspace > scripts.

if not resolve:
    raise RuntimeError("PANIC: Could not connect to resolve")
else:
    print("successfully connected to resolve")

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
COLUMN_SOURCES = "SOURCES"
COLUMN_COMMENTS = "COMMENTS"

# RESOLVE
OVERLAYS_BIN = "overlays"

OVERLAY_TAG = "TAG"
OVERLAY_TOPIC = "TOPIC"
OVERLAY_SRC_LACKING = "SRC!"
OVERLAY_SRC_LIST = "SRC_list"
OVERLAY_COMMENTS = "comments"

OVERLAY_TEMPLATES = [
    OVERLAY_TAG,
    OVERLAY_TOPIC,
    OVERLAY_SRC_LACKING,
    OVERLAY_SRC_LIST,
    OVERLAY_COMMENTS,
]

TRACK_VIDEO = 1
TRACK_MULTICAM = 2
TRACK_TAG = 3
TRACK_SRC_LACKING = 4
TRACK_SRC_LIST = 5
TRACK_COMMENTS = 6
TRACK_TOPIC = 7

TRACK_NAMES = {
    TRACK_VIDEO: "VIDEO",
    TRACK_MULTICAM: "MULTICAM",
    TRACK_TAG: "TAG",
    TRACK_SRC_LACKING: "SRC_LACKING",
    TRACK_SRC_LIST: "SOURCES",
    TRACK_COMMENTS: "COMMENTS",
    TRACK_TOPIC: "TOPIC"
}

project = resolve.GetProjectManager().GetCurrentProject()
media_pool = project.GetMediaPool()
timeline = project.GetCurrentTimeline()
timeline_start = timeline.GetStartFrame()


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

def ensure_overlays():
    missing = []

    for template_name in OVERLAY_TEMPLATES:
        if not find_template(template_name):
            missing.append(template_name)

    if missing:

        print("")
        print("========================================")
        print("ERROR: Missing overlay templates")
        print("========================================")

        for name in missing:
            print(f" - {name}")

        print("")
        print(f"Perhaps '{OVERLAYS_BIN}' bin is missing?")
        print("")

        return False

    print("[OK] All overlay templates found")

    return True

def ensure_video_tracks(timeline, track_names):
    required_count = max(track_names.keys())

    current = timeline.GetTrackCount("video")

    while current < required_count:
        timeline.AddTrack("video")
        current += 1

    for index, name in track_names.items():
        timeline.SetTrackName("video", index, name)

def find_template(name):
    """
    Finds a template clip inside Power Bin folder.
    """
    root = media_pool.GetRootFolder()
    folders = root.GetSubFolderList()

    for f in folders:
        if f.GetName() == OVERLAYS_BIN:
            clips = f.GetClipList()
            for c in clips:
                if c.GetName() == name:
                    return c
    return None


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

    # ==========================================
    # Normalize text
    # ==========================================

    if text is None:
        text = ""

    text = str(text).strip()

    # Split ';' into multiple lines
    # Example:
    # "TAG1;TAG2;TAG3"
    # ->
    # "TAG1\nTAG2\nTAG3"

    text = "\n".join(
        part.strip()
        for part in text.split(";")
        if part.strip()
    )

    tools = fusion.GetToolList()

    for _, tool in tools.items():

        # --------------------------------------
        # Direct StyledText attribute
        # --------------------------------------

        if hasattr(tool, "StyledText"):
            try:
                tool.StyledText = text
                return True
            except:
                pass

        # --------------------------------------
        # StyledText input socket
        # --------------------------------------

        try:
            if tool.GetInput("StyledText") is not None:
                tool.SetInput("StyledText", text)
                return True
        except:
            pass

    print("[ERROR] No Text+ node found")
    return False

def append_overlay(template, track_index, tl_in, tl_out):
    """
    Creates a timeline overlay instance from a MediaPool template.
    """

    duration = tl_out - tl_in

    if duration <= 0:
        return

    clip_info = {
        "mediaPoolItem": template,

        # source range inside template
        "startFrame": 0,
        "endFrame": duration, # will logically equal src_out

        # destination in timeline
        "recordFrame": timeline_start + tl_in,
        "trackIndex": track_index,
    }

    result = media_pool.AppendToTimeline([clip_info])

    if not result:
        print(f"[ERROR] Failed to append overlay to V{track_index}")
        return None

    return result[0]

def build_overlays(csv_rows):

    for row in csv_rows:
        if bool(row.get("CHECK")) != True:
            continue

        # =====================================
        # TIME BASE
        # =====================================

        try:
            tl_in = int(row.get("fTL_IN", 0))
            tl_out = int(row.get("fTL_OUT", 0))
        except Exception:
            print("[WARNING] Invalid frame data, skipping row")
            continue

        duration = tl_out - tl_in

        if duration <= 0:
            print("[WARNING] Invalid duration, skipping row")
            continue


        # =====================================
        # TAG  → V2
        # =====================================

        tag_value = row.get(COLUMN_TAGS, "").strip()

        if tag_value:

            template = find_template(OVERLAY_TAG)

            if not template:
                print("PANIC: no {TEMPLATE_TAG} template")
                return

            item = append_overlay(
                template,
                TRACK_TAG,
                tl_in,
                tl_out
            )

            if not item:
                print("PANIC: {TEMPLATE_TAG} {tag_value} could not be added")
                sys.exit(1)
            
            set_textplus_text(item, tag_value)
            item.SetName(f"TAG_{tag_value}")


        # =====================================
        # SRC_LACKING → V3
        # =====================================

        lacks_source = row.get(COLUMN_LACKS_SOURCE, "").strip().lower()

        if lacks_source == "true":

            template = find_template(OVERLAY_SRC_LACKING)

            if not template:
                print("PANIC: no SRC_LACKING template")
                return

            item = append_overlay(
                template,
                TRACK_SRC_LACKING,
                tl_in,
                tl_out
            )

            if item:
                item.SetName("SRC_LACKING")


        # =====================================
        # SOURCES → V4
        # =====================================

        sources_value = row.get(COLUMN_SOURCES, "").strip()

        if sources_value:

            template = find_template(OVERLAY_SRC_LIST)

            if not template:
                print("PANIC: no SOURCES template")
                return

            item = append_overlay(
                template,
                TRACK_SRC_LIST,
                tl_in,
                tl_out
            )

            if item:
                item.SetName(f"SOURCES_{sources_value}")
                set_textplus_text(item, sources_value)


        # =====================================
        # COMMENTS → V5
        # =====================================

        comments_value = row.get(COLUMN_COMMENTS, "").strip()

        if comments_value:

            template = find_template(OVERLAY_COMMENTS)

            if not template:
                print("PANIC: no COMMENTS template")
                return

            item = append_overlay(
                template,
                TRACK_COMMENTS,
                tl_in,
                tl_out
            )

            if item:
                item.SetName(f"COMMENTS_{comments_value}")
                set_textplus_text(item, comments_value)


def build_topics(csv_rows):

    template = find_template(OVERLAY_TOPIC)

    if not template:
        print("PANIC: no TOPIC template")
        return

    current_topic = None
    current_start = None
    current_end = None

    def flush_topic(topic, tl_in, tl_out):

        if not topic:
            return

        item = append_overlay(
            template,
            TRACK_TOPIC,
            tl_in,
            tl_out
        )

        if item:
            set_textplus_text(item, topic)
            item.SetName(f"TOPIC_{topic}")

    for row in csv_rows:
        topic = row.get("TOPIC", "").strip()

        try:
            tl_in = int(row.get("fTL_IN", 0))
            tl_out = int(row.get("fTL_OUT", 0))
        except:
            continue

        # --------------------------------------
        # Empty topic
        # --------------------------------------

        if not topic:

            flush_topic(
                current_topic,
                current_start,
                current_end
            )

            current_topic = None
            current_start = None
            current_end = None

            continue

        # --------------------------------------
        # First topic
        # --------------------------------------

        if current_topic is None:
            current_topic = topic
            current_start = tl_in
            current_end = tl_out

            continue

        # --------------------------------------
        # Same topic → extend range
        # --------------------------------------

        if topic == current_topic:
            current_end = tl_out
            continue

        # --------------------------------------
        # Topic changed
        # --------------------------------------

        flush_topic(
            current_topic,
            current_start,
            current_end
        )

        current_topic = topic
        current_start = tl_in
        current_end = tl_out

    # ==========================================
    # Flush final topic
    # ==========================================

    flush_topic(
        current_topic,
        current_start,
        current_end
    )

def main():
    ensure_overlays()
    ensure_video_tracks(timeline, TRACK_NAMES)
    rows = read_csv(CSV_PATH)

    print(f"[INFO] Loaded rows: {len(rows)}")

    build_overlays(rows)
    build_topics(rows)

    print("[DONE]")


if __name__ == "__main__":
    main()
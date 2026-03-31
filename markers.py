import csv
import random

# Fitxers
input_csv = r"..\master3.csv"
output_edl = "markers.edl"

FPS = 24  # IMPORTANT: 24 per evitar drifting a Resolve

# Colors disponibles (evitem Lavender pels topics)
TOPIC_COLORS = [
    "ResolveColorRed",
    "ResolveColorGreen",
    "ResolveColorBlue",
    "ResolveColorCyan",
    "ResolveColorMagenta",
    "ResolveColorYellow",
    "ResolveColorOrange",
    "ResolveColorPink",
    "ResolveColorPurple"
]

topic_color_map = {}
color_pool = TOPIC_COLORS.copy()
random.shuffle(color_pool)

def get_topic_color(topic):
    global color_pool

    if topic not in topic_color_map:
        if not color_pool:
            color_pool = TOPIC_COLORS.copy()
            random.shuffle(color_pool)

        topic_color_map[topic] = color_pool.pop()

    return topic_color_map[topic]

# Global per evitar col·lisions de TAGs amb l'inici de TOPICs
topic_frames = set()

def frames_to_tc(f):
    """
    Conversió robusta de frames a HH:MM:SS:FF
    Evita acumulació d'errors.
    """
    total_frames = int(f)

    ff = total_frames % FPS
    total_seconds = total_frames // FPS

    s = total_seconds % 60
    total_minutes = total_seconds // 60

    m = total_minutes % 60
    h = total_minutes // 60

    return f"{h+1:02}:{m:02}:{s:02}:{ff:02}"  # +1h offset timeline


def write_marker(f, idx, tc_in, tc_out, description):
    f.write(f"{idx:03}  001      V     C        {tc_in} {tc_out} {tc_in} {tc_out}  \n")
    f.write(description + "\n\n")

def write_topic_block(f, idx, topic, f_in, f_out, speakers_set):
    duration = f_out - f_in + 1
    tc_in = frames_to_tc(f_in)
    tc_out = frames_to_tc(f_out)
    color = get_topic_color(topic)

    f.write(f"{idx:03}  001      V     C        {tc_in} {tc_out} {tc_in} {tc_out}  \n")
    f.write(f"topic: {topic}, speakers: {', '.join(sorted(speakers_set))} |C:{color} |M:{topic} |D:{duration}\n\n")

    return idx + 1


def generate_tag_markers(rows, f, start_idx):
    idx = start_idx

    for row in rows:
        check = row.get("CHECK", "").strip()
        tag = row.get("TAGS", "").strip()
        speaker = row.get("SPEAKER", "").strip()

        if check == "1" and tag != "":
            f_in = int(row.get("fTL_IN", "0"))
            if f_in in topic_frames:
                f_in += 1
            
            f_out = f_in + 1  # 1 frame
            duration = 1

            tc_in = frames_to_tc(f_in)
            tc_out = frames_to_tc(f_out)

            desc = f"tags: {tag}, speakers: {speaker} |C:ResolveColorLavender |M:{tag} |D:{duration}"

            write_marker(f, idx, tc_in, tc_out, desc)
            idx += 1

    return idx

def generate_topic_markers(rows, f, idx):
    global topic_frames

    current_topic = None
    current_start = None
    current_end = None
    speakers_set = set()

    for row in rows:
        check = (row.get("CHECK") or "").strip()
        topic = (row.get("TOPIC") or "").strip()
        speaker = (row.get("SPEAKER") or "").strip()

        valid_row = (check == "1" and topic != "")

        if valid_row:
            try:
                f_in = int(row.get("fTL_IN", "0"))
                f_out = int(row.get("fTL_OUT", "0"))
            except ValueError:
                continue

        # --- CAS 1: fila vàlida ---
        if valid_row:
            if current_topic is None:
                # inici nou bloc
                current_topic = topic
                current_start = f_in
                current_end = f_out
                speakers_set = {speaker} if speaker else set()

            elif topic == current_topic:
                # continuació del bloc
                current_end = f_out
                if speaker:
                    speakers_set.add(speaker)

            else:
                # tanquem bloc anterior
                idx = write_topic_block(
                    f, idx, current_topic, current_start, current_end, speakers_set
                )

                topic_frames.add(current_start)
                topic_frames.add(current_end)

                # inici nou bloc
                current_topic = topic
                current_start = f_in
                current_end = f_out
                speakers_set = {speaker} if speaker else set()

        # --- CAS 2: fila NO vàlida → trenca bloc ---
        else:
            if current_topic is not None:
                idx = write_topic_block(
                    f, idx, current_topic, current_start, current_end, speakers_set
                )

                topic_frames.add(current_start)
                topic_frames.add(current_end)

                current_topic = None
                current_start = None
                current_end = None
                speakers_set = set()

    # tancar últim bloc
    if current_topic is not None:
        idx = write_topic_block(
            f, idx, current_topic, current_start, current_end, speakers_set
        )

        topic_frames.add(current_start)
        topic_frames.add(current_end)

    return idx

def generate_topic_markersOLD(rows, f, start_idx):
    idx = start_idx

    current_topic = None
    start_frame = None
    end_frame = None
    speakers = set()

    topic_colors = {}
    color_pool = TOPIC_COLORS.copy()
    random.shuffle(color_pool)

    def get_color(topic):
        if topic not in topic_colors:
            if not color_pool:
                color_pool.extend(TOPIC_COLORS)
                random.shuffle(color_pool)
            topic_colors[topic] = color_pool.pop()
        return topic_colors[topic]

    def flush():
        nonlocal idx, current_topic, start_frame, end_frame, speakers

        if current_topic is None:
            return

        duration = end_frame - start_frame

        if duration <= 0:
            return

        tc_in = frames_to_tc(start_frame)
        tc_out = frames_to_tc(end_frame)

        speaker_str = ", ".join(sorted(speakers))
        color = get_color(current_topic)

        desc = f"topic: {current_topic}, speakers: {speaker_str} |C:{color} |M:{current_topic} |D:{duration}"

        write_marker(f, idx, tc_in, tc_out, desc)
        idx += 1

    for row in rows:
        check = row.get("CHECK", "").strip()
        topic = row.get("TOPIC", "").strip()
        speaker = row.get("SPEAKER", "").strip()

        if check != "1" or topic == "":
            # tall de bloc
            flush()
            current_topic = None
            speakers = set()
            continue

        f_in = int(row.get("fTL_IN", "0"))
        f_out = int(row.get("fTL_OUT", "0"))

        if topic != current_topic:
            # nou bloc
            flush()

            current_topic = topic
            start_frame = f_in
            end_frame = f_out
            speakers = set([speaker])
        else:
            # mateix bloc
            end_frame = f_out
            speakers.add(speaker)

    # últim bloc
    flush()

    return idx


# MAIN
with open(input_csv, newline='', encoding='utf-8') as csvfile, \
     open(output_edl, 'w', encoding='utf-8') as f:

    reader = list(csv.DictReader(csvfile))

    f.write("TITLE: exported_markers\n")
    f.write("FCM: NON-DROP FRAME\n\n")

    idx = 1

    # 1. TOPICS (duration markers)
    idx = generate_topic_markers(reader, f, idx)

    # 2. TAGS (punctual markers)
    idx = generate_tag_markers(reader, f, idx)


print(f"EDL generat correctament: {output_edl}")
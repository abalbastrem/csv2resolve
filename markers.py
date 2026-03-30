import csv
import random

input_csv = r"..\master2.csv"
output_edl = "markers.edl"
FPS = 24

TOPIC_COLORS = ["ResolveColorRed", "ResolveColorGreen", "ResolveColorBlue",
                "ResolveColorMagenta", "ResolveColorCyan", "ResolveColorYellow",
                "ResolveColorOrange", "ResolveColorPurple"]

# Global per evitar col·lisions de TAGs amb l'inici de TOPICs
topic_frames = set()

def frames_to_tc(f):
    total_seconds = f / FPS
    h = int(total_seconds // 3600)
    m = int((total_seconds % 3600) // 60)
    s = int(total_seconds % 60)
    ff = round((total_seconds - int(total_seconds)) * FPS)
    return f"{h+1:02}:{m:02}:{s:02}:{ff:02}"  # +1 hora

def create_topic_markers(rows, f):
    """
    Escriu TOPICs com duration markers
    """
    global topic_frames
    current_topic = None
    current_start = None
    current_end = None
    speakers_set = set()
    
    for row in rows:
        check = row.get("CHECK", "").strip()
        topic = row.get("TOPIC", "").strip()

        if check != "1" or topic == "":
            continue

        speaker = row.get("SPEAKER", "").strip()
        f_in = int(row.get("fTL_IN", "0"))
        f_out = int(row.get("fTL_OUT", "0"))

        

        if topic != current_topic:
            if current_topic is not None:
                # escrivim bloc anterior
                duration = current_end - current_start + 1
                tc_in = frames_to_tc(current_start)
                tc_out = frames_to_tc(current_end)
                color = random.choice(TOPIC_COLORS)
                f.write(f"{create_topic_markers.counter:03}  001      V     C        {tc_in} {tc_out} {tc_in} {tc_out}  \n")
                f.write(f"topic: {current_topic}, speakers: {', '.join(sorted(speakers_set))} |C:{color} |M:{current_topic} |D:{duration}\n\n")
                create_topic_markers.counter += 1
                topic_frames.add(current_start)
                topic_frames.add(current_end)

            # iniciar nou bloc
            current_topic = topic
            current_start = f_in
            current_end = f_out
            speakers_set = {speaker} if speaker else set()
        else:
            current_end = f_out
            if speaker:
                speakers_set.add(speaker)

    # escrivim últim bloc
    if current_topic is not None:
        duration = current_end - current_start + 1
        tc_in = frames_to_tc(current_start)
        tc_out = frames_to_tc(current_end)
        color = random.choice(TOPIC_COLORS)
        f.write(f"{create_topic_markers.counter:03}  001      V     C        {tc_in} {tc_out} {tc_in} {tc_out}  \n")
        f.write(f"topic: {current_topic}, speakers: {', '.join(sorted(speakers_set))} |C:{color} |M:{current_topic} |D:{duration}\n\n")
        create_topic_markers.counter += 1
        topic_frames.add(current_start)
        topic_frames.add(current_end)

create_topic_markers.counter = 1  # variable per numeració global de markers

def create_tag_markers(rows, f):
    """
    Escriu TAGs com markers d'1 frame
    """
    global topic_frames
    for row in rows:
        check = row.get("CHECK", "").strip()
        tag = row.get("TAGS", "").strip()

        if check != "1" or tag == "":
            continue
        
        speaker = row.get("SPEAKER", "").strip()
        f_in = int(row.get("fTL_IN", "0"))

        # Evitem col·lisió amb inici de TOPIC
        if f_in in topic_frames:
            f_in += 1

        f_out = f_in
        duration = 1
        tc_in = frames_to_tc(f_in)
        tc_out = frames_to_tc(f_out)
        f.write(f"{create_topic_markers.counter:03}  001      V     C        {tc_in} {tc_out} {tc_in} {tc_out}  \n")
        f.write(f"tags: {tag}, speakers: {speaker} |C:ResolveColorLavender |M:{tag} |D:{duration}\n\n")
        create_topic_markers.counter += 1

# ---------- MAIN ----------
with open(input_csv, newline='', encoding='utf-8') as csvfile, \
     open(output_edl, 'w', encoding='utf-8') as f:

    reader = list(csv.DictReader(csvfile))
    f.write("TITLE: exported_markers\nFCM: NON-DROP FRAME\n\n")

    create_topic_markers(reader, f)
    create_tag_markers(reader, f)

print(f"EDL generat correctament: {output_edl}")
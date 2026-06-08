import csv
import os
import argparse

CSV_FILE = "../timeline.csv"
METADATA_FILE = "../output/video_metadata.csv"
OUTPUT_XML = "../output/timeline.xml"
SOURCES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sources"))
MEDIA_PRIORITY = ["offline", "single", "online"]

def load_metadata():
    metadata = {}

    with open(METADATA_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            asset_id = row["filename"].strip()
            # asset_id = row["path"].strip()

            path = row["path"].strip()
            duration = int(row["total_frames"])

            # detectem tipus (si no tens camp explícit)
            lower_path = path.lower()

            if "offline" in lower_path:
                variant = "offline"
            elif "online" in lower_path:
                variant = "online"
            else:
                variant = "single"

            if asset_id not in metadata:
                metadata[asset_id] = {
                    "duration": duration,
                    "media": {}
                }

            # guarda variant
            metadata[asset_id]["media"][variant] = path

    return metadata

def resolve_media(asset, online=False):
    if online:
        priority = ["online", "single", "offline"]
    else:
        priority = MEDIA_PRIORITY
    media = asset["media"]

    for t in priority:
        if t in media:
            return {
                "type": t,
                "path": media[t],
                "duration": asset["duration"]
            }

    raise Exception("No media available")

def validate_clips(clips, metadata):
    seen_gids = set()
    prev_gid = None

    for i, c in enumerate(clips):

        # --- GID ---
        global_id_v = str(c["global_id"]).strip() 
        # comma float to dot float
        global_id_v = global_id_v.replace(",", ".")

        try:
            gid = round(float(global_id_v) * 100)
        except ValueError:
            raise Exception(f"GID no numèric a index {i}: {global_id_v}")

        if gid in seen_gids:
            raise Exception(f"GID duplicat: {gid}")
        seen_gids.add(gid)

        if prev_gid is not None and gid <= prev_gid:
            raise Exception(
                f"GID no ascendent a index {i}: {gid} <= {prev_gid}"
            )
        prev_gid = gid

        # --- CHECK temporal ---
        if c["src_in"] >= c["src_out"]:
            raise Exception(f"SRC_IN >= SRC_OUT a GID {gid}")

        if c["tl_in"] >= c["tl_out"]:
            raise Exception(f"TL_IN >= TL_OUT a GID {gid}")

        # --- durada coherent ---
        expected = c["src_out"] - c["src_in"]
        if expected != c["dur"]:
            raise Exception(
                f"Durada incorrecta a GID {gid}: FR_DUR={c['dur']} vs calc={expected}"
            )

        # --- metadata consistència ---
        video_name = c["video_name"]
        if video_name not in metadata:
            raise Exception(f"Metadata missing: {video_name}")

        if metadata[video_name]["duration"] <= 0:
            raise Exception(f"Durada invàlida metadata: {video_name}")

    # --- timeline order check (TL) ---
    for i in range(1, len(clips)):
        if clips[i]["tl_in"] < clips[i-1]["tl_out"]:
            raise Exception(
                f"Overlap TL entre GID {clips[i-1]['global_id']} i {clips[i]['global_id']}"
            )

def generate_xml(csv_path, output_path, online=False, relaxed=False):
    base_dir = os.path.dirname(os.path.abspath(csv_path))
    
    metadata = load_metadata()
    clips = []

    # CSV del muntatge
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Filtre: només CHECK == 1
            if row["CHECK"].strip() != "1":
                continue

            video_name = row["ID VIDEO"]

            if video_name not in metadata:
                raise Exception(f"Vídeo no trobat a metadata: {video_name}")

            asset = metadata[video_name]
            variant = resolve_media(asset, online)

            clips.append({
                "global_id": row["GID"],
                "local_id": row["LID"],
                "video_name": video_name,
                "video_path": variant["path"],
                "video_duration": variant["duration"],
                "src_in": int(row["fSRC_IN"]),
                "src_out": int(row["fSRC_OUT"]),
                "dur": int(row["fDUR"]),
                "tl_in": int(row["fTL_IN"]),
                "tl_out": int(row["fTL_OUT"]),
            })

    if not clips:
        raise Exception("No hi ha clips vàlids després del filtre CHECK == 1")
    
    if not relaxed:
      validate_clips(clips, metadata)

    total_duration = clips[-1]["tl_out"]

    file_ids = {}
    file_counter = 1

    def get_file_block(c):
        nonlocal file_counter

        video_key = c["video_name"]

        if video_key not in file_ids:
            file_id = f"file{file_counter}"
            file_ids[video_key] = file_id
            file_counter += 1

            raw_path = c["video_path"]
            abs_path = os.path.abspath(os.path.join(SOURCES_DIR, raw_path)).replace("\\", "/")

            file_block = f"""
            <file id="{file_id}">
              <duration>{c['video_duration']}</duration>
              <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
              <name>{video_key}</name>
              <pathurl>file://localhost/{abs_path}</pathurl>
              <timecode>
                <string>00:00:00:00</string>
                <displayformat>NDF</displayformat>
                <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
              </timecode>
              <media>
                <video>
                  <duration>{c['video_duration']}</duration>
                  <samplecharacteristics>
                    <width>1920</width>
                    <height>1080</height>
                  </samplecharacteristics>
                </video>
                <audio>
                  <channelcount>2</channelcount>
                </audio>
              </media>
            </file>
            """
        else:
            file_id = file_ids[video_key]
            file_block = f'<file id="{file_id}"/>'

        return file_block, file_id

    def video_clip_xml(c):
        file_block, file_id = get_file_block(c)

        return f"""
          <clipitem id="clip{c['global_id']}">
            <name>{c['video_name']}</name>
            <duration>{c['dur']}</duration>
            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
            <start>{c['tl_in']}</start>
            <end>{c['tl_out']}</end>
            <enabled>TRUE</enabled>
            <in>{c['src_in']}</in>
            <out>{c['src_out']}</out>
            {file_block}
            <link><linkclipref>clip{c['global_id']}</linkclipref></link>
            <link><linkclipref>clip{c['global_id']}a</linkclipref></link>
          </clipitem>
        """, file_id

    def audio_clip_xml(c, file_id):
        return f"""
          <clipitem id="clip{c['global_id']}a">
            <start>{c['tl_in']}</start>
            <end>{c['tl_out']}</end>
            <in>{c['src_in']}</in>
            <out>{c['src_out']}</out>
            <file id="{file_id}"/>
            <sourcetrack>
              <mediatype>audio</mediatype>
              <trackindex>1</trackindex>
            </sourcetrack>
            <link>
              <linkclipref>clip{c['global_id']}</linkclipref>
              <mediatype>video</mediatype>
            </link>
          </clipitem>
        """

    video_clips_xml = ""
    audio_clips_xml = ""

    for c in clips:
        if c["src_out"] > c["video_duration"]:
            raise Exception(f"Clip excedeix durada del vídeo: {c['video_name']}")

        video_xml, file_id = video_clip_xml(c)
        video_clips_xml += video_xml
        audio_clips_xml += audio_clip_xml(c, file_id)

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="5">
  <sequence>

    <name>GENERATED_TIMELINE</name>
    <duration>{total_duration}</duration>

    <rate>
      <timebase>24</timebase>
      <ntsc>TRUE</ntsc>
    </rate>

    <in>-1</in>
    <out>-1</out>

    <timecode>
      <string>01:00:00:00</string>
      <frame>86400</frame>
      <displayformat>NDF</displayformat>
      <rate>
        <timebase>24</timebase>
        <ntsc>TRUE</ntsc>
      </rate>
    </timecode>

    <media>

      <video>
        <track>
          {video_clips_xml}
          <enabled>TRUE</enabled>
          <locked>FALSE</locked>
        </track>

        <format>
          <samplecharacteristics>
            <width>1920</width>
            <height>1080</height>
            <pixelaspectratio>square</pixelaspectratio>
            <rate><timebase>24</timebase><ntsc>TRUE</ntsc></rate>
          </samplecharacteristics>
        </format>

      </video>

      <audio>
        <track>
          {audio_clips_xml}
          <enabled>TRUE</enabled>
          <locked>FALSE</locked>
        </track>
      </audio>

    </media>

  </sequence>
</xmeml>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"XML generat: {output_path}")


if __name__ == "__main__":
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument("--relaxed", action="store_true")
    parser.add_argument("--csv", default=CSV_FILE)
    parser.add_argument("--online", action="store_true")
    args = parser.parse_args()

    csv_file = args.csv

    if not os.path.isfile(csv_file):
        print(f"PANIC: CSV FILE NOT FOUND: {csv_file}")
        sys.exit(1)


    generate_xml(csv_file, OUTPUT_XML, online=args.online, relaxed=args.relaxed)
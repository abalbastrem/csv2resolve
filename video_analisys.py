import subprocess
import csv
import os
import sys
import json
import argparse

VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi")
FFPROBE = "ffprobe"
METADATA_FILE_PATH = "../output/video_metadata.csv"
VIDEO_SOURCES_PATH = "../sources/"

def run_ffprobe_json(cmd):
    try:
        output = subprocess.check_output(cmd)
        return json.loads(output.decode())
    except subprocess.CalledProcessError:
        print("FFPROBE FAILED:", cmd)
        return None

def get_fast_stream_info(path):
    return run_ffprobe_json([
        FFPROBE,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=nb_frames,avg_frame_rate,r_frame_rate,time_base",
        "-show_entries",
        "format=duration",
        "-of", "json",
        path
    ])

def get_precise_frame_count(path):
    data = run_ffprobe_json([
        FFPROBE,
        "-v", "error",
        "-count_frames",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=nb_read_frames",
        "-of", "json",
        path
    ])

    if not data:
        return "N/A"

    stream = data.get("streams", [{}])[0]

    return stream.get("nb_read_frames", "N/A")

def get_stream_info(path):
    data = get_fast_stream_info(path)

    if not data:
        return {
            "frames": "N/A",
            "avg_fps": "N/A",
            "r_fps": "N/A",
            "time_base": "N/A",
            "duration": "N/A",
        }

    stream = data.get("streams", [{}])[0]
    fmt = data.get("format", {})

    frames = stream.get("nb_frames")
    if not frames or frames == "N/A":
        print("nb_frames unavailable → falling back to slow frame count")
        frames = get_precise_frame_count(path)

    return {
        "frames": frames,
        "avg_fps": stream.get("avg_frame_rate", "N/A"),
        "r_fps": stream.get("r_frame_rate", "N/A"),
        "time_base": stream.get("time_base", "N/A"),
        "duration": fmt.get("duration", "N/A"),
    }

def find_videos(path=VIDEO_SOURCES_PATH):
    video_files = []
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            if f.lower().endswith(VIDEO_EXTENSIONS):
                full_path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(full_path, path)
                video_files.append({"filename":f, 
                                    "rel_path":rel_path,
                                    "full_path": full_path})
    if video_files == []:
        print("PANIC: NO VIDEO FILES FOUND")
        sys.exit(1)
    return video_files

def load_already_processed_videos(csv_path=METADATA_FILE_PATH):
    # Reads the existing metadata CSV and returns a set of video paths
    # that have already been processed. This allows the pipeline to be
    # safely resumed after interruption (Ctrl+C, crash, etc.) without
    # duplicating work or rewriting previously analyzed videos.

    processed = set()

    if not os.path.exists(csv_path):
        return processed

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            processed.add(row["path"])

    return processed

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--path",
        default=VIDEO_SOURCES_PATH,
        help="Folder to scan for videos"
    )

    args = parser.parse_args()

    videos = find_videos(args.path)

    # deterministic sort, necessary for journaling
    videos.sort(key=lambda v: v["rel_path"])

    do_write_header = not os.path.exists(METADATA_FILE_PATH)

    processed = load_already_processed_videos(METADATA_FILE_PATH)

    with open(METADATA_FILE_PATH, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if do_write_header:
            writer.writerow([
                "filename",
                "path",
                "total_frames",
                "avg_frame_rate",
                "r_frame_rate",
                "time_base",
                "duration_seconds"
            ])

        for video in videos:
            if video["rel_path"] in processed:
                print(f"Skipping already processed: {video['rel_path']}")
                continue

            print(f"Processing: {video['rel_path']}")

            info = get_stream_info(video["full_path"])

            name_without_ext = os.path.splitext(video["filename"])[0]

            writer.writerow([
                name_without_ext,
                video["rel_path"],
                info["frames"],
                info["avg_fps"],
                info["r_fps"],
                info["time_base"],
                info["duration"]
            ])

    print(f"Done. {len(videos)} videos processed → video_metadata.csv")

if __name__ == "__main__":
    main()
    print("SUCCESS")
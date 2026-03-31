import subprocess
import csv
import os
import json

VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".avi")
FFPROBE = "ffprobe"

def run_ffprobe_json(cmd):
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return json.loads(output.decode())
    except subprocess.CalledProcessError:
        return None

def get_stream_info(path):
    data = run_ffprobe_json([
        FFPROBE, "-v", "error",
        "-count_frames",
        "-select_streams", "v:0",
        "-show_entries",
        "stream=nb_read_frames,avg_frame_rate,r_frame_rate,time_base",
        "-show_entries",
        "format=duration",
        "-of", "json",
        path
    ])

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

    return {
        "frames": stream.get("nb_read_frames", "N/A"),
        "avg_fps": stream.get("avg_frame_rate", "N/A"),
        "r_fps": stream.get("r_frame_rate", "N/A"),
        "time_base": stream.get("time_base", "N/A"),
        "duration": fmt.get("duration", "N/A"),
    }

def find_videos(root="."):
    video_files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.lower().endswith(VIDEO_EXTENSIONS):
                full_path = os.path.join(dirpath, f)
                rel_path = os.path.relpath(full_path, root)
                video_files.append((f, rel_path))
    return video_files

def main():
    videos = find_videos(".")

    with open("metadata.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "filename",
            "path",
            "total_frames",
            "avg_frame_rate",
            "r_frame_rate",
            "time_base",
            "duration_seconds"
        ])

        for filename, rel_path in videos:
            print(f"Processing: {rel_path}")

            info = get_stream_info(rel_path)

            name_without_ext = os.path.splitext(filename)[0]

            writer.writerow([
                name_without_ext,
                rel_path,
                info["frames"],
                info["avg_fps"],
                info["r_fps"],
                info["time_base"],
                info["duration"]
            ])

    print(f"Done. {len(videos)} videos processed → metadata.csv")

if __name__ == "__main__":
    main()
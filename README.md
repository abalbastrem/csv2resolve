v0.3
- Consider making a subtitles script

v0.2
- Scripts should first check for any forseeable problems, error with actionable message and halt. That way, errors are not made halfway through, whether fatal or otherwise.
- Should make sure mediapool clips and other items are located in the corresponding bins for every ingress and outgress of every script.

v0.1

script VIDEO ANALYSIS
Analyses videos and stores data in a file.
- filename
- path
- total_frames
- avg_frame_rate
- r_frame_rate
- time_base
- duration_seconds

This will be used in the following script to convert from frames to timecode.

script CSV2XML
From CSV, creates timeline in XML format to be imported in Davinci Resolve. Compatible with Davinci Resolve v20.

script MARKERS
From CSV, imports markers to Resolve.

action EDIT
Edit with proxies. Make sure proxies that will be replaced with multicams are appended with ´_a´.

action RELINK
Rightclick ´operations->replace selected clips´. Works regardless of framerate. Master videofiles must end with ´_a´ if they are to be substituted by multicams later on.

script PREPARE MULTICAMS
Takes all mediapool clips that end with ´_a´, looks for their ´_b´ counterpart in the filesystem, imports those, and creates multicam clips with both.

script INSERT MULTICAMS
Creates new video track in current timeline, for all _a clips, places corresponding multicam clips in the new video track, and for all other clips simply copies them up. The original video track is all marked in orange and should be disabled manually.
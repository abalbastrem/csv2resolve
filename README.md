# CSV2RESOLVE workflow v0.2
A series of actions and python scripts to execute from inside and outside DaVinci Resolve in order to have an effective video workflow that handles markers, proxies, masters and multicam.
This workflow is specifically tailored to my own personal project and would likely not work for yours without some modifying. Feel free to download or fork to your convenience.

You will need:
- DaVinci Resolve v20
- Python version recommended by DaVinci Resolve v20.
Other versions may work too, but are not ensured.

### HOW TO USE
1. Prepping
1.1. script **create_dir_structure**
Creates folder structure in filesystem. Skips folders already created.
1.2. script **check_csv**
Checks integrity of csv file.
1.3. script **davinci_create_bins**
Creates all bins that will be used for the following clips and, generally speaking, to keep everything tidy.

2. script **video_analysis**
Analyses videos and stores the following metadata fields in a file:
- filename
- path
- total_frames
- avg_frame_rate
- r_frame_rate
- time_base
- duration_seconds

This will be used in the following script to convert from frames to timecode.

3. script **csv2timeline**
From edit CSV and video_metadata.csv, creates timeline in XML format to be imported in Davinci Resolve.

4. action **manually move imported clips to bins**
Move recently imported clips in media pool to the corresponding bins, usually _offline_ and _single_. If not there, move timeline to _Master_.

5. script **davinci_overlays**
From CSV, creates overlaying clips in the timeline. Make sure to copy _overlays_ powerbin to the project MediaPool.
Types of overlaying clips:
- TOPIC
- TAGS
- SRC!: if source is needed but is missing. It is simply boolean.
- SRC_list: list of sources.
- comments

6. action **edit**
Edit with proxies. Make sure proxies that will be replaced with multicams are appended with ´_a´.

7. action **conform**
Conforms proxies to masters. For difficult clips, such as the ones that change aspect ratio or framerrate, this must be done manually, clip by clip. In the mediapool, select all clips to be conformed in _offline_ bin, rightclick _clip operations > replace selected clip_ and change to online folder.  Works regardless of framerate and metadata gets updated correctly. Master videofiles must end with ´_a´_ if they are to be substituted by multicams later on. When done, move clips from _offline_ to _online_ bin.
For all clips that are not troublesome, perhaps they can be conformed all at once with _clip operations > change source folder_, although metadata won't update.

8. Multicams
8.1. script **davinci prepare multicams**
Takes all mediapool clips in _online_ and _single_ bin that end with ´\_a´, looks for their ´\_b´ counterpart in the filesystem, imports those, and moves them both to _mc\_pending_.
This script DOES NOT generate multicam clips.
8.2. action **manually make multicams**
No API actions to make this into a script at the moment. Manually select both clips in _mc\_pending_, rightclick _'Create new multicam clip using selected clips...'_ and choose the appropiate options. 
Check for correct framerate, and these options should be ideal for this production:
- Angle Sync: Timecode
- Multicam Audio: Source Audio Channels
- Name must end with '\mc'.
Manually move all the multicam clips to bin _mc_ and all used clips to _mc\_done_.
8.3. script **davinci insert multicams**
Creates new video track in current timeline, for all _a clips, places corresponding multicam clips in the new video track, and for all other clips simply copies them up. The original video track is all marked in orange and should be disabled/deleted manually.
8.4. action **edit multicams**

9. action **Export**

### VERSION HISTORY
v0.3
- Consider making a subtitles script

v0.2
- Scripts check for any forseeable problems, error with actionable message and halt. That way, errors are not made halfway through, whether fatal or otherwise.
- Enforces folder and bin structure. Should make sure mediapool clips and other items are located in the corresponding bins for every ingress and outgress of every script.

v0.1
- First semiworking version

### TODO
- Test whole workflow with singles from the very beginning.
- Link A1 and V1, early on and perhaps again after the multicam script.
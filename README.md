# CSV2RESOLVE workflow v0.2
A series of actions and python scripts to execute from inside and outside DaVinci Resolve in order to have an effective video workflow that handles markers, proxies, masters and multicam.
This workflow is specifically tailored to my own personal project and would likely not work for yours without some modifying. Feel free to download or fork to your convenience.

You will need:
- DaVinci Resolve v20
- Python version recommended by DaVinci Resolve v20.
Other versions may work too, but are not ensured.

### HOW TO USE
1. script **create folder structure**
Creates folder structure in filesystem. Skips folders already created.

2. script **video analysis**
Analyses videos and stores the following metadata fields in a file:
- filename
- path
- total_frames
- avg_frame_rate
- r_frame_rate
- time_base
- duration_seconds

This will be used in the following script to convert from frames to timecode.

3. script **davinci create bins**
Creates all bins that will be used for the following clips and, generally speaking, to keep everything tidy and in order.

4. script **csv2timeline**
From edit CSV and video_metadata.csv, creates timeline in XML format to be imported in Davinci Resolve.

5. action **manually move imported clips to bins**
Move recently imported clips in media pool to the corresponding bins, usually _offline_ and _single_.

6. script **markers**
From CSV, creates markers.edl file. In order to import, right click on timeline _Mediapool Item > Timelines > Import > Timeline Markers from EDL_.

7. action **edit**
Edit with proxies. Make sure proxies that will be replaced with multicams are appended with ´_a´.

8. action **conform**
Conforms proxies to masters. In the mediapool, select all clips to be conformed in _offline_ bin, rightclick _clip operations > replace selected folder_ and change to online folder. Works regardless of framerate. Master videofiles must end with ´_a´_ if they are to be substituted by multicams later on. When done, move clips from _offline_ to _online_ bin.
Note: Clip metadata won't be updated in Resolve, so it's hard to tell which mediapool clips are proxy and which are master, so make folders.
Troubleshooting: proxies and masters must have same aspect ratio and pixel type. If not, a wrong aspect ratio will come up. A way to fix it is to simply rightclick _clip operations > replace selected clip_ on the individual troublesome clip.

9. script **davinci prepare multicams**
Takes all mediapool clips in _online_ and _single_ bin that end with ´\_a´, looks for their ´\_b´ counterpart in the filesystem, imports those, and moves them both to _mc\_pending_.
This script DOES NOT generate multicam clips.

10. action **manually make multicams**
No API actions to make this into a script at the moment. Manually select both clips in _mc\_pending_, rightclick _'Create new multicam clip using selected clips...'_ and choose the appropiate options. 
Check for correct framerate, and these options should be ideal for this production:
- Angle Sync: Timecode
- Multicam Audio: Source Audio Channels

11. script **davinci insert multicams**
Creates new video track in current timeline, for all _a clips, places corresponding multicam clips in the new video track, and for all other clips simply copies them up. The original video track is all marked in orange and should be disabled manually.

### VERSION HISTORY
v0.3
- Consider making a subtitles script

v0.2
- Scripts check for any forseeable problems, error with actionable message and halt. That way, errors are not made halfway through, whether fatal or otherwise.
- Enforces folder and bin structure. Should make sure mediapool clips and other items are located in the corresponding bins for every ingress and outgress of every script.

v0.1
- First semiworking version

### TODO
- Test with singles from the very beginning
- Should I make markers clips with transparency in order to help with the editing?
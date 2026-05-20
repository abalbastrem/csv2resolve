# Checks and creates folder structure in filesystem.
# - scripts: where these and all other scripts live
# - output: output of scripts
# - sources: video sources
# -- online: proxies
# -- offline: masters
# -- single: vids with one version, no proxy/master variation

import os

# Base path: one level above current directory
BASE_PATH = os.path.abspath(os.path.join(os.getcwd(), ".."))

# Root folders
ROOT_FOLDERS = [
    "scripts",
    "output",
    "sources",
]

# Subfolders inside sources
SOURCE_SUBFOLDERS = [
    "online",
    "offline",
    "single",
]


def ensure_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"[CREATED] {path}")
    else:
        print(f"[SKIPPED] {path}")


def main():
    # Create root folders
    for folder in ROOT_FOLDERS:
        ensure_folder(os.path.join(BASE_PATH, folder))

    # Create sources subfolders
    sources_path = os.path.join(BASE_PATH, "sources")

    for subfolder in SOURCE_SUBFOLDERS:
        ensure_folder(os.path.join(sources_path, subfolder))


if __name__ == "__main__":
    main()
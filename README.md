# mk-msdir
This script is a Python-based tool for organizing and processing media server directory structures, primarily used in the context of music or media archiving. It is based on original work by Frank Zalkow (2011–2012) and has been updated and extended by Lennart Rathgeb (2022–2025).

## Features

The current version of the script supports:

- **Booklet processing**:
  - Automatic rotation
  - Sharpening
  - Renaming and deletion of unprocessed files
  - Opening all processed booklet files

- **Composer/Performer metadata management**:
  - Default values for yes/no questions
  - Support for previous composer and ensemble entries

- **File and folder handling**:
  - Dialog-based folder selection
  - Structured renaming and validation of directory contents
  - Creation and management of destination boxes
  - Moving folders to target destinations

- **Data tracking**:
  - Appending structured data to an Excel spreadsheet (macOS only)

## Requirements

- Python 3.x
- Operating System:
  - macOS 14/15
  - Windows 11  (no image processing and Excel export)
- Required Python packages (only on macOS):
  - `pillow`
  - `pandas`

## Usage

1. Run the script in a terminal using:
	`python mk-msdir_work.py`

2. Follow the guided prompts to:
	- Choose the working directory
	- Input metadata (composer, title, performer, etc.)
	- Process booklets and manage folders
3. Booklet folder is automatically created and managed using macOS launchd (optional):
	`launchctl unload ~/Library/LaunchAgents/com.user.bookletchecker.plist`
	`launchctl load ~/Library/LaunchAgents/com.user.bookletchecker.plist`
	A more detailed description of this automation can be found at:
    /Users/bibliothek/Scripts/Automatic-booklet-folder_description.md

## Project Structure
- `mk-msdir_2022.py `- Original Version by Frank Zalkow (2011–2012)
- `mk-msdir_work.py` – Main script for directory processing by Lennart Rathgeb (2022-2025)
- Additional scripts and resources for GUI development exist in a separate branch (GUI-Experiment), but are currently not working nor maintained.

## Notes
- This script is designed for internal use in a library or archival environment.
- GUI development was started in a separate branch but was discontinued.

## License
- This project is not yet licensed. 
- Contact the author if you wish to use or modify the code.

## Authors
- Original: Frank Zalkow
- Updated and maintained by: Lennart Rathgeb (2022–2025)
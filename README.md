# orca2flashforge

orca2flashforge is a universal post-process script for OrcaSlicer, which restores FlashForge specific metadata

## What It Does

This script restructures G-code files from OrcaSlicer to match the format expected by FlashForge printers and their API. Without this conversion, the printer won't display the information, and it won't populate in the HTTP API

### Restored Information

The conversion ensures the printer correctly recognizes the following info:

- **Estimated Print Time (ETA)** - Time remaining and total print duration
- **Filament Usage** - Amount used in mm, cm³, grams, and cost
- **Layer Count** - Total layers and current layer progress
- **Print Settings** - Infill percentage, print speeds, layer height
- **Temperature Settings** - Nozzle and bed temperatures
- **Printer Configuration** - All slicer settings and parameters

### Optional Features

- **Spaghetti Detector Integration** (default on):  
  Adds the subroutine calls into the `.gcode`, triggered by `; filament start gcode` and `; filament end gcode` (default in OrcaSlicer).  
  While this behavior runs by default, it can be toggled via a simple flag within the script.


## Installation

1. Clone or download this repository
2. Ensure Python 3.6+ is installed

## Setup
> OrcaSlicer documentation [here](https://github.com/SoftFever/OrcaSlicer/wiki/others_settings_post_processing_scripts)


(path to python) (path to convert.py)

<img width="608" height="582" alt="image" src="https://github.com/user-attachments/assets/9919c016-2519-42c0-8c43-81dd26662fb5" />

Save settings. The script will automatically run after every slice.

## Example
This file was sliced by OrcaSlicer *without* the post-process script, and lacks filament usage, eta, and more
> The ETA shows as the current time
<img width="340" height="239" alt="image" src="https://github.com/user-attachments/assets/7b580a56-6271-4311-bb9d-790f463b4b34" />

This file was passed through the post-process script, allowing the printer and other programs to fetch/display the correct information
> The ETA is correctly calculated, and filament information is populated
<img width="333" height="166" alt="image" src="https://github.com/user-attachments/assets/33a12f31-8b44-43e7-b5cc-cc854862d7eb" />



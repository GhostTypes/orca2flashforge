#!/usr/bin/env python3
"""
Post-processing script for OrcaSlicer to convert G-code format to match Orca-FlashForge
This ensures proper ETA display on FlashForge printers and API compatibility

Includes optional Spaghetti Detector insertion.

Usage: Add this script to OrcaSlicer's post-processing scripts.
"""

import sys
import os
from typing import Tuple

# ---------------- CONFIG ----------------
enable_spaghetti_detector = True  # Enable/Disable the spaghetti detector (default: True)
# ----------------------------------------

def extract_sections(gcode_content: str) -> Tuple[str, str, str, str, str]:
    """
    Extract different sections from the G-code file
    Returns: (header_block, thumbnail_block, executable_gcode, metadata, config_block)
    """

    lines = gcode_content.split('\n')

    header_block = []
    thumbnail_block = []
    config_block = []
    metadata = []
    executable_gcode = []

    # Simple boolean flags for tracking sections
    in_header = False
    in_config = False
    in_thumbnail = False
    collecting_metadata = True

    # Metadata fields to explicitly look for
    metadata_fields = [
        "; filament used [mm]", "; filament used [cm3]", "; filament used [g]",
        "; filament cost", "; total filament used [g]", "; total filament cost",
        "; total layers count", "; estimated printing time (normal mode)"
    ]

    for line in lines:
        stripped = line.strip()

        # CONFIG block detection
        if stripped == "; CONFIG_BLOCK_START":
            in_config = True
            config_block.append(line)
            continue
        elif stripped == "; CONFIG_BLOCK_END":
            config_block.append(line)
            in_config = False
            continue
        elif in_config:
            config_block.append(line)
            continue

        # HEADER block detection
        if stripped == "; HEADER_BLOCK_START":
            in_header = True
            header_block.append(line)
            continue
        elif stripped == "; HEADER_BLOCK_END":
            header_block.append(line)
            in_header = False
            continue
        elif in_header:
            header_block.append(line)
            continue

        # THUMBNAIL block detection
        if stripped == "; THUMBNAIL_BLOCK_START":
            in_thumbnail = True
            thumbnail_block.append(line)
            continue
        elif stripped == "; THUMBNAIL_BLOCK_END":
            thumbnail_block.append(line)
            in_thumbnail = False
            continue
        elif in_thumbnail:
            thumbnail_block.append(line)
            continue

        # Metadata collection (before CONFIG_BLOCK_START)
        if collecting_metadata:
            if any(field in stripped for field in metadata_fields):
                metadata.append(line)
                continue
            elif stripped == "; CONFIG_BLOCK_START":
                collecting_metadata = False

        # Everything else goes to executable gcode
        executable_gcode.append(line)

    return (
        '\n'.join(header_block),
        '\n'.join(thumbnail_block),
        '\n'.join(executable_gcode),
        '\n'.join(metadata),
        '\n'.join(config_block)
    )

def add_spaghetti_detector(executable_gcode: str) -> str:
    """
    Insert M981 commands for spaghetti detector if enabled.
    Looks for OrcaSlicer comments like '; filament start gcode' and '; filament end gcode'.
    """
    if not enable_spaghetti_detector:
        return executable_gcode

    lines = executable_gcode.split('\n')
    new_lines = []

    for line in lines:
        stripped = line.strip().lower()

        if "; filament start gcode" in stripped:
            new_lines.append("M981 S1 P20000 ; Enable spaghetti detector")
        elif "; filament end gcode" in stripped:
            new_lines.append("M981 S0 P20000 ; Disable spaghetti detector")

        new_lines.append(line)

    return '\n'.join(new_lines)

def restructure_gcode(input_file: str) -> str:
    """
    Restructure G-code from OrcaSlicer format to Orca-FlashForge format
    """
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {input_file}: {e}")
        return None
    
    # Extract sections
    header_block, thumbnail_block, executable_gcode, metadata, config_block = extract_sections(content)

    # Optionally add spaghetti detector
    executable_gcode = add_spaghetti_detector(executable_gcode)
    
    # Build new structure following Orca-FlashForge format:
    # 1. Header block
    # 2. Metadata (filament usage, ETA, etc.)
    # 3. Config block  
    # 4. Thumbnail block
    # 5. Executable G-code
    
    restructured_parts = []
    
    if header_block.strip():
        restructured_parts.append(header_block)
        restructured_parts.append("")  # spacing
    
    if metadata.strip():
        restructured_parts.append(metadata)
        restructured_parts.append("")
    
    if config_block.strip():
        restructured_parts.append(config_block)
        restructured_parts.append("")
    
    if thumbnail_block.strip():
        restructured_parts.append(thumbnail_block)
        restructured_parts.append("")
    
    if executable_gcode.strip():
        restructured_parts.append(executable_gcode)
    
    return '\n'.join(restructured_parts)

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert.py <gcode_file>")
        sys.exit(1)
    
    gcode_file = sys.argv[1]
    
    if not os.path.exists(gcode_file):
        print(f"Error: File {gcode_file} does not exist")
        sys.exit(1)
    
    print(f"[OrcaPost] Converting G-code: {gcode_file}")
    
    # Create backup
    backup_file = gcode_file + ".backup"
    try:
        with open(gcode_file, 'r', encoding='utf-8') as src:
            with open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"[OrcaPost] Backup created: {backup_file}")
    except Exception as e:
        print(f"[OrcaPost] Warning: Could not create backup: {e}")
    
    # Restructure the file
    restructured_content = restructure_gcode(gcode_file)
    
    if restructured_content is None:
        print("[OrcaPost] Error: Failed to restructure G-code")
        sys.exit(1)
    
    # Write the restructured content back to the original file
    try:
        with open(gcode_file, 'w', encoding='utf-8') as f:
            f.write(restructured_content)
        print(f"[OrcaPost] ✅ Successfully converted {gcode_file} to Orca-FlashForge format")
        if enable_spaghetti_detector:
            print("[OrcaPost] Spaghetti detector commands added ✅")
        print("[OrcaPost] ETA and metadata should now display correctly on FlashForge printers")
    except Exception as e:
        print(f"[OrcaPost] Error writing file {gcode_file}: {e}")
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r', encoding='utf-8') as src:
                    with open(gcode_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                print("[OrcaPost] Restored original file from backup")
            except:
                print("[OrcaPost] Failed to restore backup - manual intervention required")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Post-processing script for OrcaSlicer to convert G-code format to match Orca-FlashForge
This ensures proper ETA display on FlashForge printers and API compatibility

Usage: Add this script to OrcaSlicer's post-processing scripts
The script will automatically restructure the G-code file format

Optional: Use --add-md5 flag to add MD5 checksum for forge-x firmware compatibility
"""

import sys
import os
import argparse
import hashlib
from typing import Tuple

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
    
    # Build new structure following Orca-FlashForge format:
    # 1. Header block
    # 2. Metadata (filament usage, ETA, etc.)
    # 3. Config block  
    # 4. Thumbnail block
    # 5. Executable G-code
    
    restructured_parts = []
    
    # 1. Header block
    if header_block.strip():
        restructured_parts.append(header_block)
        restructured_parts.append("")  # Empty line for spacing
    
    # 2. Metadata (the crucial part for ETA display)
    if metadata.strip():
        restructured_parts.append(metadata)
        restructured_parts.append("")  # Empty line for spacing
    
    # 3. Config block
    if config_block.strip():
        restructured_parts.append(config_block)
        restructured_parts.append("")  # Empty line for spacing
    
    # 4. Thumbnail block
    if thumbnail_block.strip():
        restructured_parts.append(thumbnail_block)
        restructured_parts.append("")  # Empty line for spacing
    
    # 5. Executable G-code
    if executable_gcode.strip():
        restructured_parts.append(executable_gcode)
    
    return '\n'.join(restructured_parts)

def add_md5_checksum(gcode_file: str) -> bool:
    """
    Add MD5 checksum to the beginning of the G-code file for forge-x firmware compatibility.

    This prepends "; MD5:[hash]" to the file, which allows the forge-x firmware to verify
    file integrity before printing, preventing issues from corrupted files.

    Args:
        gcode_file: Path to the G-code file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Read the entire file content
        with open(gcode_file, 'rb') as f:
            file_content = f.read()

        # Calculate MD5 hash
        md5_hash = hashlib.md5(file_content).hexdigest()

        # Create the MD5 comment line
        md5_line = f"; MD5:{md5_hash}\n"

        # Prepend MD5 to the file content
        new_content = md5_line.encode('utf-8') + file_content

        # Write back to the file
        with open(gcode_file, 'wb') as f:
            f.write(new_content)

        print(f"MD5 checksum added: {md5_hash}")
        return True

    except Exception as e:
        print(f"Error adding MD5 checksum: {e}")
        return False

def main():
    """
    Main function for post-processing script
    """

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Post-processing script for OrcaSlicer to convert G-code format to Orca-FlashForge',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s file.gcode                    # Convert format only
  %(prog)s file.gcode --add-md5          # Convert format and add MD5 checksum
  %(prog)s file.gcode -m                 # Short form for MD5
        """
    )
    parser.add_argument('gcode_file', help='Path to the G-code file to process')
    parser.add_argument('--add-md5', '-m', action='store_true',
                        help='Add MD5 checksum for forge-x firmware compatibility')

    # Parse arguments (support both argparse and OrcaSlicer's positional args)
    if len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
        # OrcaSlicer only passes filename, no flags
        args = parser.parse_args([sys.argv[1]])
    else:
        args = parser.parse_args()

    gcode_file = args.gcode_file

    if not os.path.exists(gcode_file):
        print(f"Error: File {gcode_file} does not exist")
        sys.exit(1)

    print(f"Converting G-code format: {gcode_file}")
    if args.add_md5:
        print("MD5 checksum generation: ENABLED")

    # Create backup
    backup_file = gcode_file + ".backup"
    try:
        with open(gcode_file, 'r', encoding='utf-8') as src:
            with open(backup_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print(f"Backup created: {backup_file}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")

    # Restructure the file
    restructured_content = restructure_gcode(gcode_file)

    if restructured_content is None:
        print("Error: Failed to restructure G-code")
        sys.exit(1)

    # Write the restructured content back to the original file
    try:
        with open(gcode_file, 'w', encoding='utf-8') as f:
            f.write(restructured_content)
        print(f"Successfully converted {gcode_file} to Orca-FlashForge format")
        print("ETA and metadata should now be properly displayed on FlashForge printer and API")
    except Exception as e:
        print(f"Error writing file {gcode_file}: {e}")
        # Try to restore backup
        if os.path.exists(backup_file):
            try:
                with open(backup_file, 'r', encoding='utf-8') as src:
                    with open(gcode_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                print("Restored original file from backup")
            except:
                print("Failed to restore backup - manual intervention required")
        sys.exit(1)

    # Add MD5 checksum if requested
    if args.add_md5:
        print("\nAdding MD5 checksum for forge-x firmware...")
        if not add_md5_checksum(gcode_file):
            print("Warning: Failed to add MD5 checksum, but file conversion was successful")
            sys.exit(1)

if __name__ == "__main__":
    main()
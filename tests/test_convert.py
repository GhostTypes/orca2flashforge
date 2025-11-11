#!/usr/bin/env python3
"""
Test suite for OrcaSlicer to Orca-FlashForge post-processing script.
Validates that the conversion produces correctly structured G-code files.
"""

import unittest
import os
import shutil
import subprocess
import sys
import hashlib
from typing import List, Dict, Optional


class TestOrcaToFlashForgeConversion(unittest.TestCase):
    """Test cases for validating G-code conversion to Orca-FlashForge format."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures and paths."""
        cls.script_dir = os.path.dirname(os.path.abspath(__file__))
        cls.convert_script = os.path.join(os.path.dirname(cls.script_dir), "convert.py")
        cls.test_fixture = os.path.join(cls.script_dir, "test.gcode")

        # Verify required files exist
        if not os.path.exists(cls.convert_script):
            raise FileNotFoundError(f"Convert script not found: {cls.convert_script}")
        if not os.path.exists(cls.test_fixture):
            raise FileNotFoundError(f"Test fixture not found: {cls.test_fixture}")

    def setUp(self):
        """Create a temporary copy of the test fixture for each test."""
        self.temp_gcode = os.path.join(self.script_dir, "temp_test.gcode")
        self.temp_backup = self.temp_gcode + ".backup"

        # Copy test fixture to temp file
        shutil.copy2(self.test_fixture, self.temp_gcode)

        # Run the conversion script
        result = subprocess.run(
            [sys.executable, self.convert_script, self.temp_gcode],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Conversion script failed: {result.stderr}")

        # Read the converted content
        with open(self.temp_gcode, 'r', encoding='utf-8') as f:
            self.converted_content = f.read()

        self.converted_lines = self.converted_content.split('\n')

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_gcode):
            os.remove(self.temp_gcode)
        if os.path.exists(self.temp_backup):
            os.remove(self.temp_backup)

    def _find_line_index(self, search_text: str) -> Optional[int]:
        """Find the index of a line containing the search text."""
        for i, line in enumerate(self.converted_lines):
            if search_text in line:
                return i
        return None

    def _find_all_line_indices(self, search_text: str) -> List[int]:
        """Find all indices of lines containing the search text."""
        indices = []
        for i, line in enumerate(self.converted_lines):
            if search_text in line:
                indices.append(i)
        return indices

    def _get_block_positions(self) -> Dict[str, Optional[int]]:
        """Get the line positions of all major blocks."""
        return {
            'header_start': self._find_line_index('; HEADER_BLOCK_START'),
            'header_end': self._find_line_index('; HEADER_BLOCK_END'),
            'config_start': self._find_line_index('; CONFIG_BLOCK_START'),
            'config_end': self._find_line_index('; CONFIG_BLOCK_END'),
            'thumbnail_start': self._find_line_index('; THUMBNAIL_BLOCK_START'),
            'thumbnail_end': self._find_line_index('; THUMBNAIL_BLOCK_END'),
        }

    # ========== Block Structure Tests ==========

    def test_header_block_exists(self):
        """Test that HEADER_BLOCK_START and HEADER_BLOCK_END exist."""
        positions = self._get_block_positions()

        self.assertIsNotNone(
            positions['header_start'],
            "Missing ; HEADER_BLOCK_START"
        )
        self.assertIsNotNone(
            positions['header_end'],
            "Missing ; HEADER_BLOCK_END"
        )
        self.assertLess(
            positions['header_start'],
            positions['header_end'],
            "HEADER_BLOCK_START should come before HEADER_BLOCK_END"
        )

    def test_config_block_exists(self):
        """Test that CONFIG_BLOCK_START and CONFIG_BLOCK_END exist."""
        positions = self._get_block_positions()

        self.assertIsNotNone(
            positions['config_start'],
            "Missing ; CONFIG_BLOCK_START"
        )
        self.assertIsNotNone(
            positions['config_end'],
            "Missing ; CONFIG_BLOCK_END"
        )
        self.assertLess(
            positions['config_start'],
            positions['config_end'],
            "CONFIG_BLOCK_START should come before CONFIG_BLOCK_END"
        )

    def test_thumbnail_block_exists(self):
        """Test that THUMBNAIL_BLOCK exists and is properly formed."""
        positions = self._get_block_positions()

        # Require thumbnail block to exist
        self.assertIsNotNone(
            positions['thumbnail_start'],
            "Missing ; THUMBNAIL_BLOCK_START"
        )
        self.assertIsNotNone(
            positions['thumbnail_end'],
            "Missing ; THUMBNAIL_BLOCK_END"
        )
        self.assertLess(
            positions['thumbnail_start'],
            positions['thumbnail_end'],
            "THUMBNAIL_BLOCK_START should come before THUMBNAIL_BLOCK_END"
        )

    def test_block_ordering(self):
        """Test that blocks appear in the correct order: Header → Metadata → Config → Thumbnail → Executable."""
        positions = self._get_block_positions()

        # Header should come first
        self.assertIsNotNone(positions['header_start'], "Missing header block")

        # Find first metadata line (should be after header, before config)
        metadata_fields = [
            '; filament used [mm]',
            '; filament used [g]',
            '; total filament used [g]',
            '; estimated printing time (normal mode)'
        ]

        metadata_positions = []
        for field in metadata_fields:
            pos = self._find_line_index(field)
            if pos is not None:
                metadata_positions.append(pos)

        if metadata_positions:
            first_metadata_pos = min(metadata_positions)

            # Metadata should come after header
            self.assertLess(
                positions['header_end'],
                first_metadata_pos,
                "Metadata should come after HEADER_BLOCK_END"
            )

            # Metadata should come before config
            self.assertLess(
                first_metadata_pos,
                positions['config_start'],
                "Metadata should come before CONFIG_BLOCK_START"
            )

        # Config should come before thumbnail (if thumbnail exists)
        if positions['thumbnail_start'] is not None:
            self.assertLess(
                positions['config_end'],
                positions['thumbnail_start'],
                "CONFIG_BLOCK should come before THUMBNAIL_BLOCK"
            )

    # ========== Metadata Validation Tests ==========

    def test_metadata_fields_present(self):
        """Test that critical metadata fields are present."""
        required_fields = [
            '; filament used [mm]',
            '; filament used [g]',
            '; total filament used [g]',
            '; estimated printing time (normal mode)'
        ]

        for field in required_fields:
            with self.subTest(field=field):
                pos = self._find_line_index(field)
                self.assertIsNotNone(
                    pos,
                    f"Missing required metadata field: {field}"
                )

    def test_metadata_before_config(self):
        """Test that all metadata fields appear before CONFIG_BLOCK_START."""
        positions = self._get_block_positions()
        config_start = positions['config_start']

        self.assertIsNotNone(config_start, "Missing CONFIG_BLOCK_START")

        metadata_fields = [
            '; filament used [mm]',
            '; filament used [g]',
            '; total filament used [g]',
            '; estimated printing time (normal mode)'
        ]

        for field in metadata_fields:
            with self.subTest(field=field):
                pos = self._find_line_index(field)
                if pos is not None:
                    self.assertLess(
                        pos,
                        config_start,
                        f"Metadata field '{field}' should appear before CONFIG_BLOCK_START"
                    )

    def test_metadata_after_header(self):
        """Test that all metadata fields appear after HEADER_BLOCK_END."""
        positions = self._get_block_positions()
        header_end = positions['header_end']

        self.assertIsNotNone(header_end, "Missing HEADER_BLOCK_END")

        metadata_fields = [
            '; filament used [mm]',
            '; filament used [g]',
            '; total filament used [g]',
            '; estimated printing time (normal mode)'
        ]

        for field in metadata_fields:
            with self.subTest(field=field):
                pos = self._find_line_index(field)
                if pos is not None:
                    self.assertGreater(
                        pos,
                        header_end,
                        f"Metadata field '{field}' should appear after HEADER_BLOCK_END"
                    )

    # ========== Header Block Tests ==========

    def test_header_contains_generated_by(self):
        """Test that the header block contains a 'generated by' line."""
        positions = self._get_block_positions()
        header_start = positions['header_start']
        header_end = positions['header_end']

        self.assertIsNotNone(header_start, "Missing HEADER_BLOCK_START")
        self.assertIsNotNone(header_end, "Missing HEADER_BLOCK_END")

        # Search within header block
        found_generated_by = False
        for i in range(header_start, header_end + 1):
            if 'generated by' in self.converted_lines[i].lower():
                found_generated_by = True
                break

        self.assertTrue(
            found_generated_by,
            "Header block should contain a 'generated by' line"
        )

    # ========== Content Preservation Tests ==========

    def test_no_data_loss(self):
        """Test that no significant content was lost during conversion."""
        # Read original file
        with open(self.test_fixture, 'r', encoding='utf-8') as f:
            original_content = f.read()

        original_lines = [line.strip() for line in original_content.split('\n') if line.strip()]
        converted_lines = [line.strip() for line in self.converted_content.split('\n') if line.strip()]

        # Allow for minor line count differences due to formatting
        line_diff = abs(len(original_lines) - len(converted_lines))

        self.assertLess(
            line_diff,
            10,
            f"Significant difference in line count: original={len(original_lines)}, converted={len(converted_lines)}"
        )


class TestMD5Checksum(unittest.TestCase):
    """Test cases for validating MD5 checksum generation for forge-x firmware."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures and paths."""
        cls.script_dir = os.path.dirname(os.path.abspath(__file__))
        cls.convert_script = os.path.join(os.path.dirname(cls.script_dir), "convert.py")
        cls.test_fixture = os.path.join(cls.script_dir, "test.gcode")

        # Verify required files exist
        if not os.path.exists(cls.convert_script):
            raise FileNotFoundError(f"Convert script not found: {cls.convert_script}")
        if not os.path.exists(cls.test_fixture):
            raise FileNotFoundError(f"Test fixture not found: {cls.test_fixture}")

    def setUp(self):
        """Create a temporary copy of the test fixture for each test."""
        self.temp_gcode = os.path.join(self.script_dir, "temp_md5_test.gcode")
        self.temp_backup = self.temp_gcode + ".backup"

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_gcode):
            os.remove(self.temp_gcode)
        if os.path.exists(self.temp_backup):
            os.remove(self.temp_backup)

    def test_md5_flag_adds_checksum(self):
        """Test that --add-md5 flag adds MD5 checksum to the beginning of the file."""
        # Copy test fixture to temp file
        shutil.copy2(self.test_fixture, self.temp_gcode)

        # Run the conversion script with --add-md5 flag
        result = subprocess.run(
            [sys.executable, self.convert_script, self.temp_gcode, '--add-md5'],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

        # Read the converted content
        with open(self.temp_gcode, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        # First line should be MD5 checksum
        self.assertTrue(
            lines[0].startswith('; MD5:'),
            f"First line should start with '; MD5:', got: {lines[0]}"
        )

    def test_md5_checksum_format(self):
        """Test that MD5 checksum has the correct format."""
        # Copy test fixture to temp file
        shutil.copy2(self.test_fixture, self.temp_gcode)

        # Run the conversion script with --add-md5 flag
        result = subprocess.run(
            [sys.executable, self.convert_script, self.temp_gcode, '--add-md5'],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

        # Read the first line
        with open(self.temp_gcode, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()

        # Verify format: "; MD5:" followed by 32 hex characters
        self.assertTrue(first_line.startswith('; MD5:'))
        md5_hash = first_line[6:]  # Remove "; MD5:" prefix

        self.assertEqual(len(md5_hash), 32, f"MD5 hash should be 32 characters, got {len(md5_hash)}")
        self.assertTrue(
            all(c in '0123456789abcdef' for c in md5_hash.lower()),
            f"MD5 hash should only contain hex characters, got: {md5_hash}"
        )

    def test_md5_checksum_validity(self):
        """Test that the MD5 checksum is correctly calculated."""
        # Copy test fixture to temp file
        shutil.copy2(self.test_fixture, self.temp_gcode)

        # Run the conversion script with --add-md5 flag
        result = subprocess.run(
            [sys.executable, self.convert_script, self.temp_gcode, '--add-md5'],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

        # Read the file
        with open(self.temp_gcode, 'rb') as f:
            content = f.read()

        # Extract MD5 from first line
        first_line = content.split(b'\n')[0].decode('utf-8')
        expected_md5 = first_line[6:]  # Remove "; MD5:" prefix

        # Calculate MD5 of the rest of the file (excluding the MD5 line)
        content_without_md5 = content.split(b'\n', 1)[1]
        calculated_md5 = hashlib.md5(content_without_md5).hexdigest()

        self.assertEqual(
            expected_md5,
            calculated_md5,
            f"MD5 checksum mismatch: expected={expected_md5}, calculated={calculated_md5}"
        )

    def test_without_md5_flag_no_checksum(self):
        """Test that without --add-md5 flag, no MD5 checksum is added."""
        # Copy test fixture to temp file
        shutil.copy2(self.test_fixture, self.temp_gcode)

        # Run the conversion script WITHOUT --add-md5 flag
        result = subprocess.run(
            [sys.executable, self.convert_script, self.temp_gcode],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

        # Read the converted content
        with open(self.temp_gcode, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()

        # First line should NOT be MD5 checksum
        self.assertFalse(
            first_line.startswith('; MD5:'),
            f"Without --add-md5 flag, first line should not be MD5 checksum, got: {first_line}"
        )

    def test_md5_short_flag(self):
        """Test that -m short flag works the same as --add-md5."""
        # Copy test fixture to temp file
        shutil.copy2(self.test_fixture, self.temp_gcode)

        # Run the conversion script with -m flag
        result = subprocess.run(
            [sys.executable, self.convert_script, self.temp_gcode, '-m'],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

        # Read the converted content
        with open(self.temp_gcode, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()

        # First line should be MD5 checksum
        self.assertTrue(
            first_line.startswith('; MD5:'),
            f"First line should start with '; MD5:' when using -m flag, got: {first_line}"
        )

    def test_md5_preserves_flashforge_metadata(self):
        """Test that MD5 generation preserves FlashForge-specific metadata structure."""
        # Copy test fixture to temp file
        shutil.copy2(self.test_fixture, self.temp_gcode)

        # Run the conversion script with --add-md5 flag
        result = subprocess.run(
            [sys.executable, self.convert_script, self.temp_gcode, '--add-md5'],
            capture_output=True,
            text=True
        )

        self.assertEqual(result.returncode, 0, f"Script failed: {result.stderr}")

        # Read the converted content
        with open(self.temp_gcode, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')

        # Find positions of key blocks (skip first line which is MD5)
        header_start = None
        config_start = None
        thumbnail_start = None

        for i, line in enumerate(lines):
            if '; HEADER_BLOCK_START' in line:
                header_start = i
            elif '; CONFIG_BLOCK_START' in line:
                config_start = i
            elif '; THUMBNAIL_BLOCK_START' in line:
                thumbnail_start = i

        # Verify that header comes after MD5 line
        self.assertIsNotNone(header_start, "Missing HEADER_BLOCK_START")
        self.assertGreater(header_start, 0, "Header should come after MD5 line")

        # Verify the structure is preserved
        self.assertIsNotNone(config_start, "Missing CONFIG_BLOCK_START")
        self.assertIsNotNone(thumbnail_start, "Missing THUMBNAIL_BLOCK_START")
        self.assertLess(header_start, config_start, "Header should come before config")
        self.assertLess(config_start, thumbnail_start, "Config should come before thumbnail")


def run_tests():
    """Run the test suite."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestOrcaToFlashForgeConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestMD5Checksum))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())

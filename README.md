<div align="center">
  <h1>orca2flashforge</h1>
  <p>A universal post-process script for OrcaSlicer, which restores FlashForge specific metadata</p>
</div>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.6+-blue?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/github/stars/GhostTypes/orca2flashforge?style=for-the-badge">
  <img src="https://img.shields.io/github/forks/GhostTypes/orca2flashforge?style=for-the-badge">
</p>

---

<div align="center">
  <h2>What It Does</h2>
</div>

<div align="center">

This script restructures G-code files from OrcaSlicer to match the format expected by FlashForge printers and their API. Without this conversion, the printer won't display the information, and it won't populate in the HTTP API

</div>

---

<div align="center">
  <h2>Restored Information</h2>
</div>

<div align="center">

The conversion ensures the printer correctly recognizes the following info:

</div>

<div align="center">
<table>
  <tr>
    <th>Information Type</th>
    <th>Details</th>
  </tr>
  <tr>
    <td>Estimated Print Time (ETA)</td>
    <td>Time remaining and total print duration</td>
  </tr>
  <tr>
    <td>Filament Usage</td>
    <td>Amount used in mm, cm³, grams, and cost</td>
  </tr>
  <tr>
    <td>Layer Count</td>
    <td>Total layers and current layer progress</td>
  </tr>
  <tr>
    <td>Print Settings</td>
    <td>Infill percentage, print speeds, layer height</td>
  </tr>
  <tr>
    <td>Temperature Settings</td>
    <td>Nozzle and bed temperatures</td>
  </tr>
  <tr>
    <td>Printer Configuration</td>
    <td>All slicer settings and parameters</td>
  </tr>
</table>
</div>

---

<div align="center">
  <h2>Installation</h2>
</div>

<div align="center">
<table>
  <tr>
    <th>Step</th>
    <th>Action</th>
  </tr>
  <tr>
    <td>1</td>
    <td>Clone or download this repository</td>
  </tr>
  <tr>
    <td>2</td>
    <td>Ensure Python 3.6+ is installed</td>
  </tr>
</table>
</div>

---

<div align="center">
  <h2>Setup</h2>
</div>

<div align="center">

> OrcaSlicer documentation [here](https://github.com/SoftFever/OrcaSlicer/wiki/others_settings_post_processing_scripts)

</div>

<div align="center">

(path to python) (path to convert.py)

</div>

<div align="center">
<img width="608" height="582" alt="image" src="https://github.com/user-attachments/assets/9919c016-2519-42c0-8c43-81dd26662fb5" />
</div>

<div align="center">

Save settings. The script will automatically run after every slice.

</div>

---

<div align="center">
  <h2>Example</h2>
</div>

<div align="center">

This file was sliced by OrcaSlicer *without* the post-process script, and lacks filament usage, eta, and more

> The ETA shows as the current time

</div>

<div align="center">
<img width="340" height="239" alt="image" src="https://github.com/user-attachments/assets/7b580a56-6271-4311-bb9d-790f463b4b34" />
</div>

<div align="center">

This file was passed through the post-process script, allowing the printer and other programs to fetch/display the correct information

> The ETA is correctly calculated, and filament information is populated

</div>

<div align="center">
<img width="333" height="166" alt="image" src="https://github.com/user-attachments/assets/33a12f31-8b44-43e7-b5cc-cc854862d7eb" />
</div>

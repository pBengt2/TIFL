# Video example (sep, 2023): https://youtu.be/JzMcd8BWqy4

# Currently tested on Python 3.11
# Currently only supports learning Japanese as an English speaker
# This project was started entirely for personal use! It was made as quickly as possible to be functional.

# Before running:
#  - Install Japanese language to windows!
#    - win -> language settings -> Add a language -> Japanese
#  - Change windows default encoding to utf-8 (fix when adding japanese-verb-conjugator-v2)
#    - win -> region settings -> additional... -> region -> admin -> change system locale... -> Use Unicode UTF-8 for worldwide language support
#  - Manually download jamdict dictionary (https://jamdict.readthedocs.io/en/latest/install.html)
#    - This ideally should be replaced with pip install jamdict_data requirement / pip install jamdict_data, but that seems to not be functional for windows atm...
#  - (optional but helpful for using jp input) Change shift key to disable caps lock (often gets stuck on by accident)
#    - win -> advanced keyboard settings -> Input language hot keys -> (to turn off Caps Lock) Press the SHIFT key

# Info on converting epub->txt : /LN/convert_info.md

# (UI TODO:) If it seems to be taking a long time to launch, it's likely in the process of downloading news files from NHK (check output).

# Slack2TXT
Python script to turn exported Slack JSON into something more readable.

SlackToText: converts the JSON of Slack exports into a more readable format
 
It assumes the current working directory includes user.json. If it locates users.json, it will match ID's to real_name's.
- if a user is not included in users.json, it will use the User ID.
 
Information:
Usage: Slack2TXT <Optional Channel Name> <OUTPUTFILE NAME>
Ver: 1.0
Date: 12/8/2025
Python version: 3.14.1
Author: Alan Mullin
H/T: Joseph Oravec
MIT License

SAMPLE OUTPUT:
2025-11-10 15:16:40.512319: message - NO SUBTYPE Alan Mullin: It also involves a trash can. 
    Reaction name: rolling_on_the_floor_laughing
    Reaction Count: 1
2025-11-10 15:27:48.732199: message - NO SUBTYPE John Smith: Saturday Alex will get suffering 
    Reaction name: pray
    Reaction Count: 1
    Reaction name: 100
    Reaction Count: 1
Reply thread timestamp: 2025-11-10 15:18:02.010129
Reply Count: 3
    2025-11-10 15:19:15.847549 Alan Mullin: 
    2025-11-10 15:20:00.064099 John Smith: :joy:
    2025-11-10 15:27:48.732199 Alexander: :joy:

LIMITATIONS:
- for uploaded files, it only notes the user and timestamp of the upload, no filenames or other info
- it is run from the command line
- it always pints to screen and to the specified file

"""

  SlackToText: converts the JSON of Slack exports into a more readable format
 
  It assumes it is in the same folder as user.json. If it locates users.json, it will match ID's to real_name'same
  to convert daily output from a channel, you would run this program from the channel's folder
  Output format is [Timestamp]:[Type]-[Subtype][User]: [Text] 
  Replies  and reacts will be indented


  Information:
  Usage: Slack2TXT <Optional Channel Name> <OUTPUTFILE NAME>
  Ver: 1.0
  Date: 12/8/2025
  Python version: 3.14.1
  Author: Alan Mullin
  H/T: Joseph Oravec
  MIT License

  Copyright (c) 2025 Alan Mullin

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  SOFTWARE.
"""


import sys, argparse, ast, json, glob, os, datetime

bVerbose = False

#
# ConvertSlackTS takes a Slack time stamp and returns a datetime object
#
def ConvertSlackTS(timestamp):
    dt_object = datetime.datetime.fromtimestamp(float(timestamp))
    return(dt_object)

#
# GetMSGfromTS() returns message text by matching with the time stamp provided
#
def GetMSGfromTS(messages=None, ts=None):
    if not messages or not ts:
        print('\nGetMSGfromTS: Missing messages or time stamp.')
        exit(2)
        
    for msg in messages:
        if msg["ts"] == ts:
            return msg["text"]
            
    return '' # NULL String

#
# GetFileNames() returns a list of JSON filenames in the folder, but will omit users.json if present
#
def GetFileNames(folder_name=None):
    filenamelist = []
    cwd = os.getcwd()
    print('GetFileNames: cwd is ' + cwd)
    
    # No folder specified
    if folder_name:
        # Folder specified
        folder_name = "\\" + folder_name + "\\"
        pattern = f"{cwd + folder_name}*.json"
        print(pattern)
        filenamelist = glob.glob(pattern)
    else:
        filenamelist = glob.glob('*.json')
        if bVerbose:
            print(f'Files: ' + str(filenamelist))
    
    filenamelist = sorted(filenamelist) # ensure user.json is last
    try:
        filenamelist.pop() # remove users.json, becasue it is handled on its own        
    except IndexError:
        print(f'GetFileNames: Folder {folder_name} not found.')
        exit(3)
    return filenamelist

#
# InsertRealName() takes a message text string and replaces UID's with names if it can find them. It returns the new string.
#
def InsertRealName(text, userids):
    if not userids: # no user.json, nothing to do
        return text
    
    # See if any known UID appears in the text
    uid_keys = list(userids.keys())
    for key in uid_keys:
        str_key = str(key)
        if str_key in text: # one of our UIDS was found
            text = text.replace(str_key, userids[key])
    
    return text

#
# ProcessSlackJSONFile() walks through each JSON file in the folder and puts it in a list 
#
def ProcessSlackJSONFile(filename=None,userids=None):
    if not filename:
        print('ProcessSlackJSONFile: No file specified.')
        exit(1) # bail out with an error
        
    SlackJSONData = [] # empty array for the file date
    stringstowrite = []

        
    with open(filename, 'r',encoding='utf-8') as file: # Slack JSON's are UTF 8
        stringstowrite.append(str(filename)+'\n') #put file name at the top of the day
        print(f'{filename}\n')
        
        data = json.load(file)
        messages = [item for item in data if item['type'] == 'message'] # handler for "message"'s
        for message in messages:
            list_reactions = []
            reacts = []
            reply_outstr = []
            msg_subtype = 'NO SUBTYPE'
            ts = ConvertSlackTS(message["ts"])
            ts = str(ts)
            
            msg_type = message["type"]
            try:
                if message["subtype"]:
                    msg_subtype = message["subtype"]
            except KeyError:
                1+1 # continue on, I had to put valid code here

            msg_user = message["user"]            
            text = message["text"]
            try:
                if message["files"]:
                    msg_subtype = 'FILE UPLOAD'
                    text = text + ' <File upload>' # TODO: get filename and add it
            except KeyError:
                1+1
            # if the message has reactions, include them
            try:
                if message["reactions"]:
                    react_outstr = str()
                    react_stdoutstr = str()
                    list_reactions = message["reactions"]
                    
                    for x in list_reactions:
                        reacts_stdout = '\x1b[0m\n    Reaction name: \x1b[31m' + x["name"] + '\x1b[0m'
                        reacts_stdout += '\x1b[0m\n    Reaction Count: \x1b[31m' + str(x["count"]) + '\x1b[0m'
                        reacts = '\n    Reaction name: ' + x["name"]
                        reacts += '\n    Reaction Count: ' + str(x["count"])                        
                        # get user names if  can
                        for y in x["users"]:
                            current_name = InsertRealName(y,userids)
                            if not current_name:
                                current_name = y
                            reacts_stdout += '\n        \x1b[36m' + current_name + '\x1b[0m'
                        react_stdoutstr += reacts_stdout
                        react_outstr += reacts                      
            except KeyError:
                1+1
                
            # Handle any replies
            try:
                if message["replies"]:
                    reply_outstr = '\nReply thread timestamp: ' + str(ConvertSlackTS(message["thread_ts"])) + '\nReply Count: ' + str(message["reply_count"])
                    reply_stdoutstr = '\nReply thread timestamp: \x1b[1m\x1b[33m' + str(ConvertSlackTS(message["thread_ts"])) + '\x1b[0m\nReply Count: ' + str(message["reply_count"])
                    list_replies = message["replies"]
                    ts_str = str()
                    
                    for x in list_replies:
                        ts = x.get("ts")
                        ts = str(ConvertSlackTS(ts))
                        reply_stdoutstr += '\n    \x1b[1m\x1b[33m' + ts + '\x1b[0m '
                        reply_outstr += '\n    ' + ts + ' '
                        user = x.get("user")
                        reply_stdoutstr += '\x1b[36m' + user + '\x1b[0m: ' + GetMSGfromTS(messages, x.get("ts")) # reply text
                        reply_outstr += user + ': ' + GetMSGfromTS(messages, x.get("ts"))
                        
            except KeyError:
                1+1
            # format output
            out_str = ts + ': ' + msg_type + ' - ' + msg_subtype + ' ' + msg_user + ': ' + text
            if reacts:
                out_str += react_outstr
            if reply_outstr:
                out_str += reply_outstr
                
            stdout_str = '\x1b[1m\x1b[33m' + ts + '\x1b[0m: ' + msg_type + ' - ' + msg_subtype + ' \x1b[36m' + msg_user + '\x1b[0m: ' + text            
            if reacts:
                stdout_str += '\x1b[31m' + react_stdoutstr + '\x1b[0m'
            if reply_outstr:
                stdout_str += reply_stdoutstr
            
            out_str = InsertRealName(out_str, userids) # add names if known
            out_str += '\n'
            stdout_str = InsertRealName(stdout_str, userids)
            print(stdout_str)
            stringstowrite.append(out_str)
             
    file.close()
    return stringstowrite

#
# LoadUsers() process the users.json file if present
#
def LoadUsers():
    if bVerbose:
        print('\n\n\nLoadUsers()...\n')
    
    try:
        with open('users.json','r',encoding='utf-8') as userfile:
            data = json.load(userfile)
            userfile.close()
    except FileNotFoundError:
        print('users.json not found, continuing...\n')
        return
        
    return data

#
# BuildIDMatches() builds a JSON list of Slack User IDs and their real_name counterparts
#
def BuildIDMatches(dataset):
    print("\nBuilding ID and User Names object...")
    name_str = []
    id_str = []
    json_str = []
    
    # Nothing to do if users.json is not present
    if dataset == None:
        if bVerbose:
            print('BuildIDMatches: no users.json was found...')
        return None
    
    if bVerbose:
        print(dataset)
    
    IDList = []
    json_str = '{'
    
    for person in dataset:
       if person['deleted']:
           name_str = person['profile']['real_name']
           id_str = person['id']
           json_str += '"'+ id_str + '" : "' + name_str + '",'
       else:
           name_str = person['profile']['real_name']
           id_str = person['id']
           json_str += '"' + id_str + '" : "' + name_str + '",'
               
    json_str = json_str[:-1]
    json_str += '}'
    
    uid_dict = ast.literal_eval(json_str)
    
    return uid_dict

#
# isIDInSet() gets passed a user ID and data set, and returns a name if the ID is in the set. Otherwise, it returns False
#
def isIDInSet(id=None, dataset=None):
    if not id or not dataset: # missing an argument
        if bVerbose:
            print('isIDInSet: argument missing.')
        return False
        
    object = json.loads(dataset)
    try:
        if object[id]:
            return object[id]
    except KeyError:
        if bVerbose:
            print('isIDInSet(): ' + id + ' was not in set.')
        return False
    
   
#
# GetKeys() will build a list of JSON keys from the JSON data
#
def GetKeys(dataset):
    keys = set()
    
    return keys

def main():
 
    parser = argparse.ArgumentParser(description="Slack2TXT: convert JSON files from a Slack channel export into UTF-8 encoded ASCII text.")
 #  parser.add_argument("-v", "--verbose", help="Turn on verbose mode to get more output to the screen.", action="store_true")
    parser.add_argument("channel_folder",help='Folder for the JSON files to process.')
    parser.add_argument("output_file",help="File to save data into.")
    args = parser.parse_args()
 #   if args.verbose:
 #       bVerbose = True
 
    file_output = []
    original_working = os.getcwd()
    
    filenames = GetFileNames(args.channel_folder)
    
    userdata = LoadUsers() # userdata is the JSON
    userids = BuildIDMatches(userdata) # create the list of user IDs if users.json is present
    
    # Loop through each file and print to screen and output file
    for item in filenames:
        if bVerbose:
            print(f'Processing file {item}.')
        file_output.append(ProcessSlackJSONFile(item,userids))
    
    with open(args.output_file,'w',encoding='utf-8') as output:
        for line1 in file_output:
            for line2 in line1:
                output.write('%s' %line2)
        
    output.close()
    
    
main()

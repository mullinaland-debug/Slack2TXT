"""

  SlackToText: converts the JSON of Slack exports into a more readable format
 
  It assumes it is in the same folder as user.json. If it locates users.json, it will match ID's to real_name'same
  to convert daily output from a channel, you would run this program from the channel's folder
  Output format is [Timestamp]:[Type]-[Subtype][User]: [Text] 
  Replies  and reacts will be indented


  Information:
  Usage: Slack2TXT <Optional Channel Name> <OUTPUTFILE NAME>
  Ver: 1.0
  Date: 12/10/2025
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
# ConvertSlackTS takes a Slack time stamp and returns a datetime string
#
def ConvertSlackTS(timestamp):
    dt_object = datetime.datetime.fromtimestamp(float(timestamp)) # sometimes Slack exports a float, sometimes it's a string: "1744455814.517349" or 1744455814.517349
    ts = str(dt_object)
    return ts
    
#
# GetReplyfromTSfromTS() returns message text by matching with the time stamp provided
#
def GetReplyfromTS(messages=None, ts=None):
    if not messages or not ts:
        sys.exit('\nGetReplyfromTS: Missing messages or time stamp.')
        
    for msg in messages:
        if msg["ts"] == ts:
            return msg["text"]
            
    return '' # NULL String
    
#
# GetMessagefromTS() returns message obj by matching with the time stamp provided
#
def GetMessagefromTS(messages=None, ts=None):
    if not messages or not ts:
        sys.exit('\nGetReplyfromTS: Missing messages or time stamp.')
        
    for msg in messages:
        if msg["ts"] == ts:
            return msg
    
    return None            

#
# GetFileNames() returns a list of JSON filenames in the folder, but will omit users.json if present
#
def GetFileNames(folder_name=None):
    filenamelist = []
    cwd = os.getcwd()
    
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
    
    filenamelist = sorted(filenamelist) # ensure files are sorted by name

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
# FormatTSstr() sets the color control code for timestamps. It takes a timestamp as a string, output mode and returns a string
#
def FormatTSstr(timestamp=None, out='file'):
    if not timestamp:
        sys.exit("FormatTSstr(): No timestamp provided.")
        
    if out == 'screen':
        return '\x1b[1m\x1b[33m[' + timestamp + ']\x1b[0m: '
        
    return '[' + timestamp + ']'

#
# FormatUserstr() sets the color control code for user names. It takes a user name and returns a string
#
def FormatUserstr(user=None, out='file'):
    if not user:
        sys.exit("FormatUserstr(): No user name provided.")
    
    if out == 'screen':
        return ' \x1b[36m<' + user + '>\x1b[0m '
    
    return '<' + user + '>'
    
#
# FormatReactstr() sets the color control code for reactions. It takes a string and returns a string
#
def FormatReactstr(react=None):
    if not react:
        sys.exit("FormatReactstr(): No reaction provided.")
    
    return ' \x1b[31m' + react + '\x1b[0m'

#
# ProcessSlackJSONFile() walks through each JSON file in the folder and puts it in a list 
#
def ProcessSlackJSONFile(filename=None,userids=None):
    if not filename:
        sys.exit('ProcessSlackJSONFile: No file specified.')
        
    SlackJSONData = []
    stringstowrite = []

        
    with open(filename, 'r',encoding='utf-8') as file: # Slack JSON's are UTF 8
        stringstowrite.append(str(filename)+'\n') #put file name at the top of the day
        print(f'\n{filename}\n')
        
        data = json.load(file)
        messages = [item for item in data if item['type'] == 'message'] # handler for "message"'s
        for message in messages:
            list_reactions = [] # no reactions yet for this message
            reacts = [] # no reactions yet
            reply_outstr = [] # no replies yet
            files_outstr = str() # no files uploaded
            attach_outstr = str()
            msg_subtype = 'NO SUBTYPE' # not all messages have subtypes
            ts = ConvertSlackTS(message["ts"])
            ts = str(ts)
            
            msg_type = message['type']
            if 'subtype' in message:
                msg_subtype = message['subtype']

            msg_user = message['user']            
            text = message['text']
            
            # list file names if there are files attached
            if 'files' in message:
                msg_subtype = 'FILE UPLOAD'
                
                for f in message['files']:
                    if f['mode'] == 'tombstone':
                        files_outstr += '\n    File: DELETED'
                        continue
                        
                    files_outstr += '\n    File: ' + FormatTSstr(ConvertSlackTS(f['timestamp'])) + ' - ' + f['name'] + ' of type ' + f['pretty_type']

            # process attachments
            if 'attachments' in message:
                msg_subtype = 'ATTACHMENTS'                
                attach_outstr = '\n    Attachment: '
                
                for f in message['attachments']:
                    msg_keys = f.keys()
                    
                    if 'ts' in msg_keys:
                        attach_outstr += ConvertSlackTS(f.get('ts')) + ' - ' + FormatUserstr(f['author_name']) + ': ' + f['text']
                    if 'from_url' in msg_keys:
                        attach_outstr += 'URL' + ' - ' + f.get('from_url') + '\n    ' + f.get('fallback') + '\n    ' + f.get('text')
            
            # if the message has reactions, include them
            if 'reactions' in message:
                react_outstr = str()
                react_stdoutstr = str()
                list_reactions = message['reactions']
                    
                for x in list_reactions:
                    reacts_stdout = '\n    Reaction name: ' + FormatReactstr(x['name'])
                    reacts_stdout += '\n    Reaction Count: '+ FormatReactstr(str(x['count']))
                    reacts = '\n    Reaction name: ' + x['name']
                    reacts += '\n    Reaction Count: ' + str(x['count'])                        
                    
                    # get user names if  can
                    for y in x['users']:
                        current_name = InsertRealName(y,userids)
                        if not current_name:
                            current_name = y
                        reacts_stdout += '\n        ' + FormatUserstr(current_name, 'screen')
                        reacts += '\n        ' + FormatUserstr(current_name)
                        
                    react_stdoutstr += reacts_stdout
                    react_outstr += reacts                      
                
            # Handle any replies
            if 'replies' in message:
                reply_outstr = '\nReply thread timestamp: ' + FormatTSstr(ConvertSlackTS(message['thread_ts'])) + '\nReply Count: ' + str(message['reply_count'])
                reply_stdoutstr = '\nReply thread timestamp: ' + FormatTSstr(ConvertSlackTS(message['thread_ts']),'screen') + '\nReply Count: ' + str(message['reply_count'])
                list_replies = message['replies']
                ts_str = str()
                    
                for x in list_replies:
                    ts = x.get('ts')
                    ts = ConvertSlackTS(ts)
                    reply_stdoutstr += '\n    ' + FormatTSstr(ts,'screen')
                    reply_outstr += '\n    ' + FormatTSstr(ts)
                    user = x.get('user')
                    
                    reply_text = GetReplyfromTS(messages, x.get('ts'))
                    #remove to prevent duplicates
                    duplicate = GetMessagefromTS(messages, x.get('ts'))
                    if not duplicate:
                        print("No duplicate found for a reply\n")
                    
                    messages.remove(duplicate)
                    
                    reply_stdoutstr += FormatUserstr(user, 'screen') + reply_text
                    reply_outstr += user + ': ' + reply_text
                        
            # format output
            out_str = FormatTSstr(ts, 'file') + ': ' + msg_type + ' - ' + msg_subtype + ' ' + msg_user + ': ' + text
            if attach_outstr:
                out_str += attach_outstr
            if files_outstr:
                out_str += files_outstr
            if reacts:
                out_str += react_outstr
            if reply_outstr:
                out_str += reply_outstr
                
            stdout_str = FormatTSstr(ts, 'screen') + msg_type + ' - ' + msg_subtype + FormatUserstr(msg_user) + text            
            if attach_outstr:
                stdout_str += attach_outstr
            if files_outstr:
                stdout_str += files_outstr
            if reacts:
                stdout_str += react_stdoutstr
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
# BuildIDMatches() builds a JSON object of Slack User IDs and their real_name counterparts
#
def BuildIDMatches(dataset):
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
    parser.add_argument("channel_folder",help='Folder for the JSON files to process.')
    parser.add_argument("output_file",help="File to save data into.")
    args = parser.parse_args()
 
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

general_index = open("texts/general-index.txt", "r").read()
topical_index = open("texts/topical-index.txt", "r").read()
import re

general_index_lines = general_index.split("\n")
topical_index_lines = topical_index.split("\n")



#loop through the index lines and add the lines to their corresponding topic. 
#keep adding lines to the last topic until a new topic is found.

# List to store all entries
topical_entries = []

# Current topic being processed
current_topic = None

# Process each line
for line in topical_index_lines:
    line = line.strip()
    
    # Skip empty lines
    if not line:
        continue
    
    # Check if this is a topic header (starts with ** and ends with **)
    if line.startswith('**') and line.endswith('**'):
        # Extract topic name (remove the ** markers)
        current_topic = line[2:-2]
    else:
        # This is a song entry - add it with the current topic
        if current_topic:
            topical_entries.append({
                'topic': current_topic,
                'entry': line
            })

# Print results
for entry in topical_entries:
    if len(entry['entry'].split('>>')) < 2:
        continue
    print(f"Topic: {entry['topic']}, song: {entry['entry'].split('>>')[0]} ,song number: {entry['entry'].split('>>')[1]}")
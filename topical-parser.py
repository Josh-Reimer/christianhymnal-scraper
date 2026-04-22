topical_index = open("topical-index.txt", "r").read()
new_file = open("texts/topical-index-new.txt", "w")
import re

lines = topical_index.split("\n")
pattern = r'>>\s*\d+\s*$'

i = 0
for line in lines:
    if re.search(pattern, line):
        new_file.write(line + "\n")
        continue
    else:
        if any(char.isdigit() for char in line):
            fixed_line = re.sub(r'(.+?)>>\s*(.+?)\s+(\d+)\s*$', r'\1\2 >> \3', line)
            print(line)
            print(fixed_line)
            new_file.write(fixed_line + "\n")
            i += 1
        else:
            print(line)
            new_file.write(line + "\n")

print(f"Total matches: {i}")
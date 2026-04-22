ocr_text = open('texts/full_body.txt', 'r', encoding='utf-8').readlines()

import re

capital_letter_pattern = re.compile(r'[A-Z]')

for line in ocr_text:
    allcapsletters = []
    striped_line = line.strip().replace(" ", "")
    current_line = ""
    for l in striped_line:
        if l.isupper():
            allcapsletters.append(l)
        if len(allcapsletters) == len(striped_line) and len(striped_line) > 1:
            # Only print if not all letters are uppercase
            current_line = line.strip()
    if current_line != "":
        print(current_line)
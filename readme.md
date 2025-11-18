# Christian Hymnal text extraction

I accidently deleted the previous projects files, so I am publishing on github to prevent future losses.
This project aims to extract text from every song in the Christian Hymnal, which can be found here: https://archive.org/details/christianhymnalc00chur
OCR on sheet music with notes, staff, and lyrics all mixed up is very difficult. I have found that using PaddleOCR on the pages, and then feeding the messy text it produces into an llm, instructing it to clean up the text and fill in the fields of a json schema, works pretty well.
I would like to use the end result of this project to compare recording transcriptions with songs to compute what song is being sung. For that purpose, the text can be a little off 100 percent accurate since I could use an llm to do the comparing.

# ideas
what if i enforce a rule that only a-z characters are allowed. that would cut out all the junk text. also remove empty spaces and empty newlines before sending to llm. make rules about the start and end of songs; every song begins with a catagory, such as PRAISE, EVANGLISTIC, LOVE, a title in bold writing, and a large bold number. there is usually a bible verse under each song title. maybe look up the chunks of text in the index to see if they are a title, and therefore the beginning of a song.
You are an expert text formatter and extracter. You cleanup messy OCR text and format it into perfectly valid JSON. You copy text as directly as possible or as clearly implied. 
For the following text, output valid JSON with fields for song number, song title, and song lyrics.
Input: 

You are an expert text formatter and extractor specializing in cleaning up messy OCR-generated text. Your task is to transform the provided text into perfectly valid JSON, preserving the original content as closely as possible or as clearly implied. 

For the input text, output valid JSON with the following fields for each song:
- `song_number` (as a number, or null if not available/unclear)
- `page_numbers` (as a number or numbers - usually appears at the very end of the song) there is a page number for every song, although some songs might share a page number.
- `song_title` (as a string, or null if not available/unclear) 
- `song_author` or authors (as a string, or null if not available/unclear)
- `song_date` (as a string in format "YYYY" or "YYYY-MM-DD" if available, or null if not available/unclear)
- `song_dates` (as a string including all the dates mentioned, or null if not available)
- `song_bible_verse_reference` (as a string in standard biblical citation format, or null if not available/unclear)
- `song_bible_verse_text` (as a string exactly as written in the song with spacing and formatting as clearly implied or null if not available/unclear)
- `song_lyrics` (as a string, preserving line breaks and formatting where applicable, or null if not available/unclear)

## Instructions:
- Ensure the JSON is well-structured and handles edge cases (e.g., missing or ambiguous data)
- Include all songs present in the input text
- When any field cannot be determined from the input text, insert `null` as the value
- If the input is incomplete or unclear, make reasonable inferences to fill gaps while maintaining fidelity to the original text
- For biblical references, use standard abbreviations (e.g., "John 3:16", "Psalm 23:1-6", "Romans 8:28")
- Preserve original formatting in lyrics including line breaks, verse numbers, choruses, etc.
- If multiple authors are present, separate with commas
- For dates, prefer the most specific format available (full date > year only)

Provide only the JSON output unless otherwise specified.

**Input:**
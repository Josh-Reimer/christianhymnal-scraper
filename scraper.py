import os
import fitz
import numpy as np
from paddleocr import PaddleOCR
import pytesseract
from PIL import Image
import io


def pdf_to_images(pdf_path, max_pages=None):
    """Convert PDF pages to PIL images using PyMuPDF."""
    doc = fitz.open(pdf_path)
    images = []

    total_pages = len(doc)
    if max_pages:
        total_pages = min(total_pages, max_pages)

    print(f"Processing {total_pages} pages from PDF")

    for page_num in range(total_pages):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)

        if (page_num + 1) % 10 == 0:
            print(f"Converted {page_num + 1}/{total_pages} pages to images")

    doc.close()
    return images


def extract_text_with_paddleocr(images):
    """Extract text from images using PaddleOCR."""
    print("Initializing PaddleOCR...")
    try:
        ocr = PaddleOCR(lang='en')
        print("PaddleOCR initialized successfully")

        all_text = []

        for i, image in enumerate(images):
            print(f"Processing page {i+1}/{len(images)} with PaddleOCR...")
            try:
                # PaddleOCR needs numpy array
                np_img = np.array(image)

                result = ocr.ocr(np_img)

                page_text = []

                if result and result[0]:
                    for box, (text, conf) in result[0]:
                        # Filter out garbage: symbols, music artifacts
                        clean = text.strip()

                        # Skip obvious noise
                        if not clean:
                            continue
                        if len(clean) == 1 and not clean.isalpha():
                            continue
                        if any(c in clean for c in "♩♪♫♯♭·•"):
                            continue

                        page_text.append(clean)

                all_text.append("\n".join(page_text))

            except Exception as e:
                print(f"Error processing page {i+1} with PaddleOCR: {e}")
                all_text.append(f"Error processing page {i+1}")

        return all_text

    except Exception as e:
        print(f"Error initializing PaddleOCR: {e}")
        print("Falling back to Tesseract...")
        return extract_text_with_tesseract(images)


def extract_text_with_tesseract(images):
    """Fallback OCR using Tesseract."""
    print("Using Tesseract OCR as fallback...")
    all_text = []

    for i, image in enumerate(images):
        print(f"Processing page {i+1}/{len(images)} with Tesseract...")
        try:
            text = pytesseract.image_to_string(image, lang='eng')
            all_text.append(text.strip())
        except Exception as e:
            print(f"Error processing page {i+1}: {e}")
            all_text.append(f"Error processing page {i+1}")

    return all_text


def save_text_to_file(text_pages, output_path):
    """Write extracted text to disk."""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, text in enumerate(text_pages):
            f.write(f"--- Page {i+1} ---\n")
            f.write(text)
            f.write("\n\n")


def main():
    pdf_path = "christianhymnal.pdf"
    output_path = "christianhymnal.txt"

    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found!")
        return

    print("Starting PDF to text conversion...")
    print("Converting PDF to images...")

    images = pdf_to_images(pdf_path)
    print(f"Converted {len(images)} pages to images")

    print("Extracting text with OCR...")
    text_pages = extract_text_with_paddleocr(images)

    print(f"Saving text to {output_path}...")
    save_text_to_file(text_pages, output_path)

    print("Conversion completed!")
    print(f"Processed {len(images)} pages and saved text to {output_path}")


if __name__ == "__main__":
    main()

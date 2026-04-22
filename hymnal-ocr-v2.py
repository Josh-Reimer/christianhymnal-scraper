# High-Accuracy Hymnal OCR (Clean & Stable Version)
# -------------------------------------------------
# Automatically uses PaddleOCR's built-in model downloader.
# Includes preprocessing, high-DPI PDF rendering, and text extraction.

import fitz          # PyMuPDF
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import cv2
import io
import matplotlib.pyplot as plt


# ============================================================
# 1) PDF → HIGH-QUALITY IMAGES
# ============================================================

def pdf_to_images(pdf_path, dpi=350):
    """
    Convert PDF pages into high-DPI images (critical for accuracy).
    """
    pdf = fitz.open(pdf_path)
    images = []

    for i in range(pdf.page_count):
        page = pdf[i]
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat)

        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append(img)

    pdf.close()
    return images


# ============================================================
# 2) IMAGE PREPROCESSING PIPELINE (massive accuracy boost)
# ============================================================

def preprocess(img):
    """
    Grayscale → Adaptive threshold.
    Staff line removal is optional; off by default.
    """
    arr = np.array(img)

    # Convert to grayscale
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Adaptive threshold (handles old scans & uneven lighting)
    binary = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        25, 15
    )

    # OPTIONAL: Remove staff lines (use if your PDF has music pages)
    # kernel = np.ones((1, 35), np.uint8)
    # binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    return binary


# ============================================================
# 3) OCR ENGINE (AUTO-MODEL LOADING / PP-OCRv4)
# ============================================================

def init_ocr():
    """
    Use PaddleOCR's built-in model downloader.
    No manual model paths. No breakage.
    Always uses PP-OCRv4 English models.
    """
    return PaddleOCR(
        lang='en',
        ocr_version="PP-OCRv4",
        use_textline_orientation=True
    )


# ============================================================
# 4) RUN OCR ON ALL PAGES
# ============================================================

def process_pdf(pdf_path):
    ocr = init_ocr()
    pages = pdf_to_images(pdf_path)
    results = []

    for idx, img in enumerate(pages):
        print(f"Processing page {idx+1}/{len(pages)}...")

        cleaned = preprocess(img)
        result = ocr.predict(cleaned)

        results.append({
            "page": idx+1,
            "image": img,
            "ocr": result[0]   # The OCRResult object
        })

    return results


# ============================================================
# 5) EXTRACT TEXT FROM OCR RESULTS
# ============================================================

def extract_text(results):
    all_text = []

    for r in results:
        page = r["page"]
        ocr_obj = r["ocr"]

        print(f"\n--- Page {page} ---")

        for text, score in zip(ocr_obj.text, ocr_obj.scores):
            print(f"{text} (conf {score:.2f})")
            all_text.append(text)

    return "\n".join(all_text)


# ============================================================
# 6) OPTIONAL VISUALIZATION
# ============================================================

def visualize_result(result):
    """
    Draw bounding boxes and text on the original page image.
    """
    img = result["image"]
    ocr = result["ocr"]

    fig, ax = plt.subplots(figsize=(12, 15))
    ax.imshow(img)
    ax.axis('off')

    for box, t, sc in zip(ocr.boxes, ocr.text, ocr.scores):
        poly = plt.Polygon(box, fill=False, edgecolor='red', linewidth=1.5)
        ax.add_patch(poly)
        ax.text(
            box[0][0], box[0][1] - 5,
            f"{t} ({sc:.2f})",
            fontsize=8,
            color="yellow",
            bbox=dict(facecolor="black", alpha=0.5)
        )

    plt.show()


# ============================================================
# 7) MAIN
# ============================================================

if __name__ == "__main__":
    pdf_path = "christianhymnal.pdf"

    print("Starting high-accuracy OCR...")
    results = process_pdf(pdf_path)

    extracted = extract_text(results)

    with open("texts/hymnal-text-v2.txt", "w", encoding="utf-8") as f:
        f.write(extracted)

    print("\nOCR complete.")
    print(f"Processed {len(results)} pages.")
    print("Saved output to texts/extracted_text.txt")

    # visualize_result(results[0])  # enable if you want

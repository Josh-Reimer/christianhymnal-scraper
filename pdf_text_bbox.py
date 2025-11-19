"""
PDF Text Detection with PaddleOCR
Detects text in PDF pages and draws bounding boxes around detected text regions.

Requirements:
pip install paddlepaddle-gpu paddleocr pdf2image pillow opencv-python
Note: Also requires poppler-utils for pdf2image conversion
"""

import os
from paddleocr import PaddleOCR
from pdf2image import convert_from_path
import cv2
import numpy as np
from PIL import Image


def process_pdf_with_bounding_boxes(pdf_path, output_dir='output', dpi=200):
    """
    Process a PDF file and draw bounding boxes around detected text.
    
    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory to save output images
        dpi: Resolution for PDF to image conversion (default: 200)
    """
    # Initialize PaddleOCR
    # GPU will be used automatically if available
    ocr = PaddleOCR(use_textline_orientation=True, lang='en')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Converting PDF to images...")
    # Convert PDF pages to images
    pages = convert_from_path(pdf_path, dpi=dpi)
    
    print(f"Processing {len(pages)} page(s)...")
    
    for page_num, page_image in enumerate(pages, start=1):
        print(f"\nProcessing page {page_num}...")
        
        # Convert PIL Image to numpy array for OpenCV
        img_array = np.array(page_image)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Perform OCR
        result = ocr.predict(img_array)
        
        # The result is a list containing OCRResult objects (dict-like)
        if result and len(result) > 0:
            ocr_result = result[0]
            
            # Access the data as a dictionary
            # Keys: 'dt_polys', 'rec_texts', 'rec_scores'
            if 'dt_polys' in ocr_result and 'rec_texts' in ocr_result:
                boxes = ocr_result['dt_polys']
                texts = ocr_result['rec_texts']
                scores = ocr_result.get('rec_scores', [1.0] * len(texts))
                
                print(f"Processing {len(boxes)} text boxes...")
                
                for box, text, confidence in zip(boxes, texts, scores):
                    # Convert box coordinates to integers
                    pts = np.array(box, dtype=np.int32)
                    
                    # Draw polygon (bounding box)
                    cv2.polylines(img_bgr, [pts], True, (0, 255, 0), 2)
                    
                    # Optionally add text label with confidence
                    label = f"{confidence:.2f}"
                    cv2.putText(img_bgr, label, (int(box[0][0]), int(box[0][1]) - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    print(f"  Detected: '{text}' (confidence: {confidence:.2f})")
            else:
                print(f"  Available keys: {list(ocr_result.keys())}")
                print(f"  Unexpected result format")
        
        # Save output image
        output_path = os.path.join(output_dir, f'page_{page_num}_bbox.jpg')
        cv2.imwrite(output_path, img_bgr)
        print(f"Saved: {output_path}")
    
    print(f"\nProcessing complete! Output saved to '{output_dir}' directory.")


def process_pdf_simple(pdf_path, output_dir='output'):
    """
    Simplified version that just draws boxes without labels.
    
    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory to save output images
    """
    ocr = PaddleOCR(use_textline_orientation=True, lang='en')
    os.makedirs(output_dir, exist_ok=True)
    
    pages = convert_from_path(pdf_path, dpi=200)
    
    for page_num, page_image in enumerate(pages, start=1):
        img_array = np.array(page_image)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        result = ocr.predict(img_array)
        
        if result and len(result) > 0:
            ocr_result = result[0]
            if 'dt_polys' in ocr_result:
                for box in ocr_result['dt_polys']:
                    pts = np.array(box, dtype=np.int32)
                    cv2.polylines(img_bgr, [pts], True, (0, 255, 0), 2)
        
        output_path = os.path.join(output_dir, f'page_{page_num}_bbox.jpg')
        cv2.imwrite(output_path, img_bgr)
    
    print(f"Processing complete! {len(pages)} page(s) processed.")


if __name__ == "__main__":
    # Example usage
    pdf_file = "sample.pdf"  # Replace with your PDF file path
    
    if os.path.exists(pdf_file):
        # Use the detailed version
        process_pdf_with_bounding_boxes(pdf_file, output_dir='output_with_labels')
        
        # Or use the simple version
        # process_pdf_simple(pdf_file, output_dir='output_simple')
    else:
        print(f"Error: PDF file '{pdf_file}' not found.")
        print("Please update the pdf_file variable with your PDF path.")
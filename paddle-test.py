# Import paddle first to set the device
import paddle
paddle.set_device('gpu') # Enforce GPU usage

# Import the specific result type if needed for isinstance check
# from paddlex.inference.pipelines.ocr.result import OCRResult
# Note: Importing specific classes might not always be necessary or possible depending on the exact version's structure.
# Using duck typing or checking for attributes is often safer.

from paddleocr import PaddleOCR
import fitz  # PyMuPDF
from PIL import Image
import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon
import numpy as np
import cv2

def pdf_to_images(pdf_path, dpi=200):
    """
    Convert PDF pages to images
    Higher DPI = better quality but larger files
    """
    images = []
    pdf_document = fitz.open(pdf_path)
    
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        # Render page to image
        mat = fitz.Matrix(dpi/72, dpi/72)  # 72 is default DPI
        pix = page.get_pixmap(matrix=mat)
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        images.append(img)
    
    pdf_document.close()
    return images

def process_pdf_with_ocr(pdf_path, lang='en'):
    """
    Process PDF with OCR and return results for all pages
    """
    # Initialize PaddleOCR with updated parameters
    ocr = PaddleOCR(lang=lang, use_textline_orientation=True) 
    
    # Convert PDF to images
    images = pdf_to_images(pdf_path)
    results = []
    
    for i, img in enumerate(images):
        print(f"Processing page {i+1}/{len(images)}...")
        
        # Convert PIL image to numpy array for OCR
        img_array = np.array(img)
        if img_array.ndim == 3 and img_array.shape[-1] == 4:  # Handle RGBA images
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        elif img_array.ndim == 2:  # Handle grayscale images if necessary
            img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
        
        # Perform OCR using the new predict method
        result = ocr.predict(img_array)
        results.append({
            'page': i+1,
            'image': img,
            'ocr_result': result
        })
    
    return results

def visualize_pdf_results(results):
    """
    Visualize OCR results for all pages
    """
    for page_data in results:
        page_num = page_data['page']
        image = page_data['image']
        result = page_data['ocr_result']
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(12, 15))
        ax.imshow(image)
        ax.set_title(f'OCR Results - Page {page_num}')
        ax.axis('off')
        
        # Draw bounding boxes and text labels
        # The result is now an OCRResult object, not a list of [bbox, [text, conf]]
        # We need to access its attributes like rec_polys and rec_texts
        # This part is complex because the structure is different
        # Let's focus on text extraction for now, visualization needs adjustment
        # For now, just print the result type and attributes for visualization
        print(f"Page {page_num} result type for visualization: {type(result)}")
        if hasattr(result, 'rec_polys') and hasattr(result, 'rec_texts'):
             # This visualization logic needs adjustment for the new structure
             # It's more complex now as the relationship between polys and texts might be different
             # Or the 'boxes' attribute might be more direct
             if hasattr(result, 'rec_boxes') and hasattr(result, 'rec_texts'):
                 boxes = getattr(result, 'rec_boxes', [])
                 texts = getattr(result, 'rec_texts', [])
                 # boxes shape is (N, 4) -> [x1, y1, x2, y2]
                 # polys shape is (N, 4, 2) -> [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                 # Let's try using boxes first, fallback to polys if needed
                 if len(boxes) > 0 and len(texts) == len(boxes):
                     for box, text in zip(boxes, texts):
                         # Convert [x1, y1, x2, y2] to [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                         bbox = [[box[0], box[1]], [box[2], box[1]], [box[2], box[3]], [box[0], box[3]]]
                         poly = Polygon(bbox, fill=False, edgecolor='red', linewidth=2)
                         ax.add_patch(poly)
                         ax.text(
                             box[0],  # x coordinate
                             box[1] - 10,  # y coordinate (adjusted up)
                             f'{text}',
                             fontsize=8,
                             bbox=dict(facecolor='yellow', alpha=0.7, edgecolor='none')
                         )
                 elif hasattr(result, 'rec_polys') and len(getattr(result, 'rec_polys', [])) > 0 and len(texts) == len(getattr(result, 'rec_polys', [])):
                      # Use rec_polys if boxes are not available or don't match
                      polys = getattr(result, 'rec_polys', [])
                      for poly, text in zip(polys, texts):
                          poly_patch = Polygon(poly, fill=False, edgecolor='red', linewidth=2)
                          ax.add_patch(poly_patch)
                          ax.text(
                              poly[0][0],  # x coordinate
                              poly[0][1] - 10,  # y coordinate (adjusted up)
                              f'{text}',
                              fontsize=8,
                              bbox=dict(facecolor='yellow', alpha=0.7, edgecolor='none')
                          )

        plt.tight_layout()
        plt.show()

def extract_text_from_pdf_results(results):
    """
    Extract and print all detected text from PDF
    """
    full_text = []
    
    for page_data in results:
        page_num = page_data['page']
        result = page_data['ocr_result']
        
        print(f"\n--- Page {page_num} ---")
        page_text = []
        
        # Check if result has the expected OCRResult attributes
        if hasattr(result, 'rec_texts'):
            # rec_texts is a list of detected strings for the page
            rec_texts = getattr(result, 'rec_texts', [])
            
            # Optional: Get corresponding scores if available
            rec_scores = getattr(result, 'rec_scores', [None] * len(rec_texts))
            
            for text, score in zip(rec_texts, rec_scores):
                if score is not None:
                    print(f"Text: {text} (Conf: {score:.2f})")
                else:
                    print(f"Text: {text}") # Print without confidence if not available
                page_text.append(text)
        else:
            # If the structure is still unexpected, print it
            print(f"Result object on page {page_num} does not have 'rec_texts' attribute: {type(result)}, {result}")
            continue # Skip this page's text extraction

        full_text.extend(page_text)
    
    return '\n'.join(full_text)

# Main execution
if __name__ == "__main__":
    # Replace with your PDF file path
    pdf_path = 'sample.pdf'
    
    # Process PDF with OCR
    print("Starting PDF OCR processing...")
    results = process_pdf_with_ocr(pdf_path, lang='en')
    
    # Extract and print text
    full_text = extract_text_from_pdf_results(results)
    
    # Optional: Visualize results (comment out if not needed)
    # visualize_pdf_results(results)
    
    # Save extracted text to file
    with open('extracted_text.txt', 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    print("\nOCR processing complete!")
    print(f"Total pages processed: {len(results)}")
    print("Text saved to 'extracted_text.txt'")
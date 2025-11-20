# Note: GPU usage is handled by the installed paddlepaddle-gpu package if configured correctly
# We are not explicitly setting the device using paddle.set_device('gpu')

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
    # Note: use_gpu parameter is not used in this version of the API
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
        # The result is a list containing an OCRResult object (dict-like)
        result = ocr.predict(img_array)
        results.append({
            'page': i+1,
            'image': img,
            'ocr_result': result # Keep the full result list
        })
    
    return results

def visualize_pdf_results(results):
    """
    Visualize OCR results for all pages
    """
    for page_data in results:
        page_num = page_data['page']
        image = page_data['image']
        result_list = page_data['ocr_result']
        
        # Create matplotlib figure
        fig, ax = plt.subplots(figsize=(12, 15))
        ax.imshow(image)
        ax.set_title(f'OCR Results - Page {page_num}')
        ax.axis('off')
        
        # The result is a list, get the first element which is the OCRResult dict
        if result_list and len(result_list) > 0:
            ocr_result = result_list[0] # Extract the OCRResult object (dict-like)
            
            # Check if the required keys exist in the OCRResult
            if isinstance(ocr_result, dict) and 'dt_polys' in ocr_result and 'rec_texts' in ocr_result:
                boxes = ocr_result['dt_polys'] # List of polygons
                texts = ocr_result['rec_texts'] # List of detected texts
                scores = ocr_result.get('rec_scores', [1.0] * len(texts)) # List of confidences
                
                # Draw bounding boxes and text labels
                for box, text, confidence in zip(boxes, texts, scores):
                    # box is a list of 4 points [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
                    poly = Polygon(box, fill=False, edgecolor='red', linewidth=2)
                    ax.add_patch(poly)
                    
                    # Add text label
                    ax.text(
                        box[0][0],  # x coordinate of top-left
                        box[0][1] - 10,  # y coordinate of top-left (adjusted up)
                        f'{text} ({confidence:.2f})',
                        fontsize=8,
                        bbox=dict(facecolor='yellow', alpha=0.7, edgecolor='none')
                    )
            else:
                print(f"Page {page_num}: Result structure missing required keys or not a dict: {type(ocr_result)}, Keys: {list(ocr_result.keys()) if isinstance(ocr_result, dict) else 'N/A'}")

        plt.tight_layout()
        plt.show()

def extract_text_from_pdf_results(results):
    """
    Extract and print all detected text from PDF
    """
    full_text = []
    
    for page_data in results:
        page_num = page_data['page']
        result_list = page_data['ocr_result']
        
        print(f"\n--- Page {page_num} ---")
        page_text = []
        
        # The result is a list, get the first element which is the OCRResult dict
        if result_list and len(result_list) > 0:
            ocr_result = result_list[0] # Extract the OCRResult object (dict-like)
            
            # Check if the required key exists in the OCRResult
            if isinstance(ocr_result, dict) and 'rec_texts' in ocr_result:
                texts = ocr_result['rec_texts'] # List of detected texts
                scores = ocr_result.get('rec_scores', [1.0] * len(texts)) # List of confidences
                
                # Iterate through detected texts and scores
                for text, score in zip(texts, scores):
                    print(f"Text: {text} (Conf: {score:.2f})")
                    page_text.append(text)
            else:
                print(f"Page {page_num}: Result structure missing 'rec_texts' key or not a dict: {type(ocr_result)}, Keys: {list(ocr_result.keys()) if isinstance(ocr_result, dict) else 'N/A'}")
                # If the structure is unexpected, print it for debugging
                print(f"Full result: {ocr_result}")
        else:
            print(f"Page {page_num}: No result returned or result list is empty.")

        full_text.extend(page_text)
    
    return '\n'.join(full_text)

# Main execution
if __name__ == "__main__":
    # Replace with your PDF file path
    pdf_path = 'christianhymnal.pdf'
    
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
from flask import Flask, request, jsonify
import fitz
from PIL import Image
import pytesseract
import os

app = Flask(__name__)
# pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'  # your path may be different

@app.route('/process_pdf', methods=['POST'])
def process_pdf():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']

    # Check if the file has a PDF extension
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Invalid file format. Please upload a PDF file'}), 400

    # Create a directory to store the images
    image_dir = 'temp_images'
    os.makedirs(image_dir, exist_ok=True)

    # Save the uploaded file
    pdf_path = os.path.join(image_dir, file.filename)
    file.save(pdf_path)

    # Process the PDF
    try:
        convert_pdfs_to_images([pdf_path])
        text_data = []
        for filename in os.listdir(image_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(image_dir, filename), "r", encoding="utf-8") as txt_file:
                    text_data.append(txt_file.read())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up: remove uploaded PDF and temporary images
        os.remove(pdf_path)
        for filename in os.listdir(image_dir):
            os.remove(os.path.join(image_dir, filename))
        os.rmdir(image_dir)

    return jsonify({'text_data': text_data}), 200

def convert_pdfs_to_images(pdf_files, dpi=300):
    # The function remains the same as in the original script
    for pdf_file in pdf_files:
        # Get the base filename without extension
        base_filename = os.path.splitext(os.path.basename(pdf_file))[0]
        
        # Open the PDF file
        pdf_document = fitz.open(pdf_file)
        
        # Create a directory to store the images
        image_dir = f"{base_filename}_images"
        os.makedirs(image_dir, exist_ok=True)
        
        # List to store paths of intermediate images
        intermediate_images = []
        
        # Iterate through pages
        for page_number in range(len(pdf_document)):
            page = pdf_document[page_number]
            
            # Convert the PDF page to a PIL (Pillow) image
            image = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
            
            # Save the image with a filename including PDF name and page number (e.g., YourPDF_page_1.png)
            image_path = os.path.join(image_dir, f"{base_filename}page{page_number + 1}.png")
            image.save(image_path)
            
            # Append the image path to the list of intermediate images
            intermediate_images.append(image_path)

            # Perform OCR on the image and save the text as .txt
            my_config = r"--psm 6 --oem 3"
            text = pytesseract.image_to_string(Image.open(image_path), config=my_config)
            
            # Define the .txt file name based on the image name
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            txt_filename = os.path.join(image_dir, f"extracted_{image_name}.txt")
            
            # Save the extracted text as a .txt file
            with open(txt_filename, "w", encoding="utf-8") as txt_file:
                txt_file.write(text)

        # Close the PDF file
        pdf_document.close()

        # Delete the intermediate images
        for image_path in intermediate_images:
            os.remove(image_path)

# # Usage example with multiple PDFs:
# input_pdfs = ["word.pdf"]
# dpi_value = 300  # Set your desired DPI value here
# convert_pdfs_to_images(input_pdfs, dpi_value)

if __name__ == '__main__':
    app.run(debug=True)

import os
from llm.openai import GPT4oStrategy
from pypdf import PdfReader
from pdf2image import convert_from_path
from utils import encode_image

TMP_DIR = "tmp"

example_file_path = "samples\BenJoubert-BTech-IT-SoftwareDevelopment-2017-04-08_20240513_0001.pdf"
example_file = open(example_file_path, "rb")

example_image_path = "tmp\page_0.png"

def main():
    '''
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    images = convert_from_path(example_file_path)
    image_paths = []
    
    for i, image in enumerate(images):
        image_path = f"page_{i}.png"  # Saving as PNG
        image_path = os.path.join(TMP_DIR, image_path)
        image.save(image_path, "PNG")
        image_paths.append(image_path)
        print(f"Image saved as '{image_path}'")
        
    exit(0)
        
    read_pdf = PdfReader(example_file)
    number_of_pages = read_pdf.get_num_pages()
    print("number_of_pages", number_of_pages)
    page = read_pdf.pages[0]
    page_content = page.extract_text()
    print(page_content)
    print(len(page_content))
    file_content = ""
    for i in range(number_of_pages):
        page = read_pdf.pages[i]
        page_content = page.extract_text()
        file_content += page_content
    print(len(file_content))
    print(file_content)
    exit(0)
    
    strategy = GPT4oStrategy()
    prompt = "What is the certificate number given in the document?"
    response = strategy.generate_response_with_file(prompt, example_file)
    print('='*50)
    print(response)
    '''
    strategy = GPT4oStrategy()
    prompt = "What is the certificate number given in the document?"
    b64 = encode_image(example_image_path)
    response = strategy.generate_response_with_image(prompt, b64)
    
if __name__ == "__main__":
    main()
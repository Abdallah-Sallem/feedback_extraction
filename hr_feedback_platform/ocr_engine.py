import base64
import os
import requests
import mimetypes

def extract_text_from_file(file_path, api_key):
    """
    Extracts raw text from an image (png, jpg, jpeg, webp) or PDF file using Mistral OCR API.
    
    Args:
        file_path (str): Absolute or relative path to the local file.
        api_key (str): The Mistral API key.
        
    Returns:
        str: Extracted markdown text from the document.
    """
    if not api_key:
        raise ValueError("Mistral API key is required.")
        
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    url = "https://api.mistral.ai/v1/ocr"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Determine the MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            mime_type = 'application/pdf'
        elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
            mime_type = f'image/{ext.replace(".", "")}'
        else:
            mime_type = 'image/jpeg'
            
    # Read and base64-encode the file
    with open(file_path, "rb") as f:
        b64_data = base64.b64encode(f.read()).decode("utf-8")
        
    data_uri = f"data:{mime_type};base64,{b64_data}"
    
    # Use appropriate payload format depending on file type
    if mime_type == 'application/pdf':
        doc_payload = {
            "type": "document_url",
            "document_url": data_uri
        }
    else:
        doc_payload = {
            "type": "image_url",
            "image_url": data_uri
        }
        
    payload = {
        "model": "mistral-ocr-latest",
        "document": doc_payload,
        "include_image_base64": False
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        raise RuntimeError(f"Mistral OCR Request failed (HTTP {response.status_code}): {response.text}")
        
    res_json = response.json()
    
    # Process all pages and join their text
    pages = res_json.get("pages", [])
    if not pages:
        return ""
        
    pages_text = [page.get("markdown", "").strip() for page in pages]
    return "\n\n".join(pages_text).strip()

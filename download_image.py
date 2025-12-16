#!/usr/bin/env python
"""
Download T-shirt image and save to static/images/tshirt.png
"""
import requests
import os

# Create images directory if it doesn't exist
os.makedirs('static/images', exist_ok=True)

# Image URL
image_url = "https://www.buytshirtdesigns.net/wp-content/uploads/2020/05/NURSE-8JADI-980-788x800.png"
output_path = "static/images/tshirt.png"

print("Downloading T-shirt image...")
print(f"URL: {image_url}")
print(f"Save to: {output_path}")

try:
    # Download the image
    response = requests.get(image_url, timeout=10)
    response.raise_for_status()
    
    # Save to file
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    print(f"SUCCESS: Image downloaded successfully!")
    print(f"   Saved to: {output_path}")
    print(f"   Size: {len(response.content)} bytes")
    
except requests.exceptions.RequestException as e:
    print(f"ERROR: Error downloading image: {e}")
    print("\n📝 Alternative: Manual download")
    print("1. Open this URL in your browser:")
    print(f"   {image_url}")
    print("2. Right-click the image → Save As")
    print(f"3. Save as: {os.path.abspath(output_path)}")
    print("\nOr use a placeholder image for now.")


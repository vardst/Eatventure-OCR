import subprocess
import os
from PIL import Image, ImageOps
import pytesseract
import pandas as pd
import base64
import requests
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
full_img_path = r"cropped/cropped_screenshot.png"
button_img_path = r"cropped/cropped_button.png"

pytesseract.pytesseract.tesseract_cmd = r"C:/Program Files/Tesseract-OCR/tesseract.exe"

def take_android_screenshot(save_path):
    try:
        subprocess.run(["adb", "start-server"], check=True)
    except subprocess.CalledProcessError:
        print("ADB is not installed or not added to the PATH.")
        return

    device_path = r"/sdcard/screenshot.png"
    local_path = os.path.join(save_path, "screenshot.png")

    try:
        subprocess.run(["adb", "shell", f"screencap -p {device_path}"], check=True)
        # print("Screenshot taken successfully.")
    except subprocess.CalledProcessError:
        print("Failed to take screenshot on device.")
        return

    try:
        subprocess.run(["adb", "pull", device_path, local_path], check=True)
        # print(f"Screenshot saved to {local_path}")
    except subprocess.CalledProcessError:
        print("Failed to pull the screenshot from device.")
        return
def crop_image_full(image_path, save_path):
    try:
        with Image.open(image_path) as img:
            # Define the area to crop (left, top, right, bottom)
            crop_area = (305, 1104, 932, 1295)  # Adjust this as needed
            cropped_img = img.crop(crop_area)
            cropped_path = os.path.join(save_path, "cropped_screenshot.png")
            cropped_img.save(cropped_path)
            # print(f"Cropped image saved to {cropped_path}")
    except Exception as e:
        print(f"Failed to crop the image: {str(e)}")
def crop_image_full_button(image_path, save_path):
    try:
        with Image.open(image_path) as img:
            # Define the area to crop (left, top, right, bottom)
            crop_area = (1010, 1140, 1250, 1250)  # Adjust this as needed
            cropped_img = img.crop(crop_area)
            inverted_img = Image.eval(cropped_img, lambda x: 255 - x)
            bw_img = inverted_img.convert("L")
            threshold = 60
            white_img = bw_img.point(lambda x:255 if x > threshold else x)
            cropped_path = os.path.join(save_path, "cropped_button.png")

            white_img.save(cropped_path)
            # print(f"Cropped image saved to {cropped_path}")
    except Exception as e:
        print(f"Failed to crop the image: {str(e)}")
def read_text_from_image(image_path):
    try:
        # Open an image file
        with Image.open(image_path) as img:
            config = '--oem 3 --psm 6'
            text = pytesseract.image_to_string(img, config=config)
            return text.strip().split('\n')
    except Exception as e:
        print(f"Failed to process the image: {str(e)}")
        return None
def buy_slot():
    cmd = f"adb shell input tap 1140 1214"
    subprocess.run(cmd, shell = True)
def img_to_vision(image_path):
    with open(image_path, "rb") as image_file:
        img_b64 = base64.b64encode(image_file.read()).decode('utf-8')
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }

    payload = {
    "model": "gpt-4o",
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "What’s in this image?, provide only text"
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img_b64}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    final_text  = response.json()["choices"][0]["message"]["content"]
    return final_text
def mainloop():
    directory = r"F:/python/Eatventure OCR/images"
    take_android_screenshot(directory)
    crop_image_full(r"images\screenshot.png",r"cropped")
    crop_image_full_button(r"images\screenshot.png",r"cropped")
    price = img_to_vision(button_img_path)
    perk_names = img_to_vision(full_img_path).split("\n")
    perk_name = perk_names[0]
    perk_description = perk_names[1]
    if perk_description.startswith("The image is completely black"):
        raise "Just closing the app"
    new_data = {
        "perk name": perk_name,
        "Perk description": perk_description,
        "price": price
    }
    new_row = pd.DataFrame([new_data])
    buy_slot()
    return new_row
def save_df(df, directory="."):
    prefix = "Data"
    suffix = ".csv"
    max_index = -1
    
    # Scan the directory for existing files with the pattern "Data<number>.csv"
    for filename in os.listdir(directory):
        if filename.startswith(prefix) and filename.endswith(suffix):
            # Extract the number from the filename
            file_index = filename[len(prefix):-len(suffix)]
            if file_index.isdigit():
                max_index = max(max_index, int(file_index))
    
    # Next index is the maximum found index plus one
    next_index = max_index + 1
    new_filename = f"{prefix}{next_index}{suffix}"
    
    # Save DataFrame to CSV with the new filename
    df.to_csv(os.path.join(directory, new_filename), index=False)
    print(f"DataFrame saved as {new_filename}")

if __name__ == "__main__":
    columns = ["perk name", "Perk description", "price"]
    df = pd.DataFrame(columns=columns)

    while True:
        try:
            df = pd.concat([df, mainloop()],ignore_index=True)
        except:
            break
        finally:
            if df.iloc[-1].isin([""]).any():
                break
    save_df(df)
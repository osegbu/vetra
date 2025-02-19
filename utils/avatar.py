from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFont
import random
import os

def avatar(text, image_size=(200, 200), font_size=150, output_path="profile_image.png"):
    try:
        bg_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        image = Image.new('RGB', image_size, bg_color)
        draw = ImageDraw.Draw(image)

        font_path = "font/Roboto-Bold.ttf"
        if not os.path.exists(font_path):
            font = ImageFont.load_default()
        else:
            font = ImageFont.truetype(font_path, font_size)

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (image_size[0] - text_width) // 2
        y = (image_size[1] - (text_height + 60)) // 2

        text_color = (255, 255, 255)
        draw.text((x, y), text, font=font, fill=text_color)

        image.save(output_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating avatar: {str(e)}")

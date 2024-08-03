import os
import json
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap


def calculate_age(year):
    current_year = 2024  # Update this if needed
    return current_year - year


def generate_random_years(age):
    percentage = random.uniform(0.10, 0.25)
    extra_years = int(age * percentage) + 3
    return age + extra_years


def create_watermark(text, font_path='impact.ttf', font_size=50):
    # Create a transparent image for the watermark
    watermark_image = Image.new('RGBA', (500, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_image)
    font = ImageFont.truetype(font_path, font_size)

    # Draw the watermark text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = ((watermark_image.width - text_width) // 2, (watermark_image.height - text_height) // 2)
    draw.text(text_position, text, font=font, fill=(255, 255, 255, 180))  # White text with 70% transparency

    return watermark_image


def create_birthday_image(input_image_path, output_image_path, name, age, font_path='impact.ttf',
                          initial_font_size=100, quality=85):
    # Load the image
    original_image = Image.open(input_image_path)

    # Define the dimensions for the final image (4:3 aspect ratio)
    output_width = 1200
    output_height = 900

    # Create a blurred background
    blurred_background = original_image.resize((output_width, output_height), Image.LANCZOS)
    blurred_background = blurred_background.filter(ImageFilter.GaussianBlur(20))

    # Calculate dimensions to resize the original image
    width, height = original_image.size
    aspect_ratio = width / height
    if aspect_ratio > output_width / output_height:
        new_width = output_width
        new_height = int(output_width / aspect_ratio)
    else:
        new_height = output_height
        new_width = int(output_height * aspect_ratio)

    # Resize the original image
    resized_image = original_image.resize((new_width, new_height), Image.LANCZOS)

    # Create a new image with the specified dimensions
    final_image = Image.new('RGB', (output_width, output_height))

    # Paste the blurred background
    final_image.paste(blurred_background, (0, 0))

    # Paste the resized image on top, centered
    final_image.paste(resized_image, ((output_width - new_width) // 2, (output_height - new_height) // 2))

    # Draw the text
    draw = ImageDraw.Draw(final_image)

    # Function to wrap text and adjust font size
    def fit_text_to_image(draw, text, font_path, max_width, max_height, initial_font_size):
        font_size = initial_font_size
        wrapped_text = text
        while font_size > 0:
            font = ImageFont.truetype(font_path, font_size)
            lines = textwrap.wrap(wrapped_text, width=40)
            line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
            total_height = sum(line_heights) + (len(lines) - 1) * 10
            if total_height <= max_height and all(
                    draw.textbbox((0, 0), line, font=font)[2] <= max_width for line in lines):
                return '\n'.join(lines), font
            font_size -= 1
        raise ValueError("Text cannot be fit into the image")

    # Create the text string
    text = f"Did you know that {name} came out {age} years ago today!"

    # Fit text to image
    max_text_width = output_width - 40
    max_text_height = output_height // 3
    wrapped_text, font = fit_text_to_image(draw, text, font_path, max_text_width, max_text_height, initial_font_size)

    # Calculate text size and position
    lines = wrapped_text.split('\n')
    total_text_height = sum([draw.textbbox((0, 0), line, font=font)[3] for line in lines]) + (len(lines) - 1) * 10
    current_height = (output_height - total_text_height) // 2

    # Draw the text with a white outline for better readability
    outline_width = 2
    for line in lines:
        text_width = draw.textbbox((0, 0), line, font=font)[2]
        text_position = ((output_width - text_width) // 2, current_height)
        for x in range(-outline_width, outline_width + 1):
            for y in range(-outline_width, outline_width + 1):
                if x != 0 or y != 0:
                    draw.text((text_position[0] + x, text_position[1] + y), line, font=font, fill='black')
        draw.text(text_position, line, font=font, fill='white')
        current_height += draw.textbbox((0, 0), line, font=font)[3] + 10

    # Create and add watermark
    watermark = create_watermark("feel-old-yet.com", font_path)
    watermark_position = (10, 10)  # Top-left corner
    final_image.paste(watermark, watermark_position, watermark)  # Paste watermark with transparency

    # Save the final image with compression
    final_image.save(output_image_path, quality=quality, optimize=True, format="JPEG")


def process_images(input_folder='images', output_folder='output', font_path='impact.ttf', quality=85):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_list = []

    for filename in os.listdir(input_folder):
        if filename.endswith('.png'):
            # Extract name and year from the filename
            basename = os.path.splitext(filename)[0]
            try:
                name, year = basename.split(',')
                year = int(year)
                age = calculate_age(year)
                final_age = generate_random_years(age)
                input_image_path = os.path.join(input_folder, filename)
                output_filename = f"{name}.jpg"
                output_image_path = os.path.join(output_folder, output_filename)

                # Create the output image
                create_birthday_image(input_image_path, output_image_path, name, final_age, font_path, quality=quality)
                image_list.append(output_filename)
                print(f"Processed {filename}")
            except ValueError:
                print(f"Skipping invalid file: {filename}")

    # Save the manifest.json
    manifest_path = os.path.join(output_folder, 'manifest.json')
    with open(manifest_path, 'w') as manifest_file:
        json.dump({"images": image_list}, manifest_file, indent=4)


# Example usage
process_images('images', 'output', 'impact.ttf', quality=85)

import os
import json
import uuid
import requests
from PIL import Image, ImageDraw, ImageFont
import base64
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_cors import cross_origin

load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://python-poster-bot.vercel.app"}})

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://python-poster-bot.vercel.app'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


# Define directories
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
TEMPLATES_FOLDER = "templates"
TEXT_POSITIONS_FILE = "text_positions.json"
FONT_PATH = "Arial.ttf"  # Ensure this font file exists

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Read API key from environment variable
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Predefined templates and positions
TEMPLATES = [
    {"path": "templates/template1-Photoroom.png", "position": (74, 126, 286, 399)},
    {"path": "templates/template2-Photoroom.png", "position": (365, 24, 680, 952)},
    {"path": "templates/template3-Photoroom.png", "position": (502, 72, 322, 449)},
    {"path": "templates/template4-Photoroom.png", "position": (140, 152, 691, 970)},
    {"path": "templates/template5-Photoroom.png", "position": (86, 235, 470, 655)},
    {"path": "templates/template6-Photoroom.png", "position": (1594, 183, 583, 818)},
    {"path": "templates/template7-Photoroom.png", "position": (954, 202, 478, 668)},
    {"path": "templates/template8-Photoroom.png", "position": (410, 363, 518, 728)},
    {"path": "templates/template9-Photoroom.png", "position": (643, 363, 275, 384)},
    {"path": "templates/template10-Photoroom.png", "position": (1862, 418, 388, 544)},
    {"path": "templates/template11-Photoroom.png", "position": (214, 318, 400, 562)},
    {"path": "templates/template12-Photoroom.png", "position": (263, 208, 604, 842)},
    {"path": "templates/template13-Photoroom.png", "position": (334, 582, 338, 476)},
    {"path": "templates/template14-Photoroom.png", "position": (1066, 386, 455, 638)},
    {"path": "templates/template15-Photoroom.png", "position": (336, 550, 410, 570)},
    {"path": "templates/template16-Photoroom.png", "position": (168, 366, 514, 720)}
]



def analyze_book_image(image_path):
    """Send the book cover image to GPT-4 Vision for title & description generation"""
    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    prompt = """
You are an AI trained to analyze book covers and generate a short title and tagline.
- **Title Format:** "[Two short, simple words based on the book]" (Avoid long words or complex terms)
- **Description:** A **short, engaging tagline** with two concise sentences.
  - Each sentence should be brief, straightforward, and easy to understand.
  - Use simple words and keep the sentences clear and impactful.
  - Avoid long or complex words (maximum 5 letters per word).
  - Don't include any kind of Commas or Apostrophe in the title only.
  - Limit each sentence to no more than 12 words.
  - Limit the title to not be more than two words and 5 letters each
  - Each sentence should be compelling and evoke curiosity, while remaining compact (avoid excessive details).
  - Ensure that the description does not feel too long or complex, similar to the example provided below.

**Example Output Format:**
Title: Lost Key
Description: A gripping tale filled with mystery. A world waiting to be explored.

**Now, analyze the provided book cover and generate a similar title and description.**
"""




    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
            ]}
        ],
        "max_tokens": 100
    }

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
        response_data = response.json()
        print("Full API Response:", response_data)

        if "choices" in response_data and response_data["choices"]:
            generated_text = response_data["choices"][0]["message"]["content"]
            lines = generated_text.split("\n")

            # Extract title & description from the response
            title = next((line.replace("Title: ", "").strip() for line in lines if line.startswith("Title:")), "Untitled")
            description = next((line.replace("Description: ", "").strip() for line in lines if line.startswith("Description:")), "No description available.")

            return title, description
    except Exception as e:
        print(f"OpenAI API Error: {e}")

    return "Untitled", "No description available."


def overlay_text_on_template(template, output_path, text_data, text_positions, template_path):
    """Overlay title and description text on the template with per-template word breaking"""
    try:
        draw = ImageDraw.Draw(template)

        if template_path not in text_positions:
            print(f"Warning: No text positions found for {template_path}")
            return

        for key, value in text_data.items():
            if key in text_positions[template_path]:
                font_path = text_positions[template_path][key].get("font_path", FONT_PATH)  # Use default if not provided
                
                # Ensure the font file exists
                if not os.path.exists(font_path):
                    print(f"Warning: Font file {font_path} not found! Using default.")
                    font_path = FONT_PATH  # Fall back to default

                font = ImageFont.truetype(font_path, text_positions[template_path][key]["font_size"])
                color = text_positions[template_path][key]["font_color"]
                words_per_line = text_positions[template_path][key].get("words_per_line", 5)

                # Debugging: Print what text is being placed and where
                print(f"Placing '{value}' on {template_path} at ({text_positions[template_path][key]['x']}, {text_positions[template_path][key]['y']}) with font {font_path}")

                # Auto-break text based on words_per_line per template
                wrapped_text = break_text_by_words(value, words_per_line)

                y_offset = text_positions[template_path][key]["y"]
                line_spacing = text_positions[template_path][key].get("line_spacing", 10)

                for line in wrapped_text:
                    text_height = draw.textbbox((0, 0), line, font=font)[3]  # Ensure this works in your Pillow version
                    draw.text((text_positions[template_path][key]["x"], y_offset), line, fill=color, font=font)
                    y_offset += text_height + line_spacing  # Move down for the next line

        print(f"Text successfully placed on {template_path}")

        # Debugging: Save a test image to see if text appears
        template.save(output_path, format="PNG")
    except Exception as e:
        print(f"Error in text overlay: {e}")





def break_text_by_words(text, words_per_line):
    """Breaks text into multiple lines based on the number of words per line"""
    words = text.split()
    lines = []
    
    for i in range(0, len(words), words_per_line):
        lines.append(" ".join(words[i:i + words_per_line]))

    return lines

def wrap_text(draw, text, font, max_width):
    """Wrap text into multiple lines based on width constraints"""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        
        # Use textbbox() instead of deprecated methods
        text_width = draw.textbbox((0, 0), test_line, font=font)[2]  

        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def overlay_image_on_template(template_path, input_image_path, output_path, position):
    """Overlay the book cover image onto the template"""
    try:
        template = Image.open(template_path).convert("RGBA")
        input_image = Image.open(input_image_path).convert("RGBA")

        x, y, width, height = position
        resized_image = input_image.resize((width, height), Image.LANCZOS)

        merged = Image.new("RGBA", template.size, (0, 0, 0, 0))
        merged.paste(template, (0, 0))
        merged.paste(resized_image, (x, y), resized_image)

        return merged
    except Exception as e:
        print(f"Error processing image overlay: {e}")
    return None

@app.route("/generate_posters", methods=["POST"])
@cross_origin(origins="https://python-poster-bot.vercel.app")
def generate_posters():
    """Main function to handle poster generation"""
    try:
        input_image_path = "uploads/image1.jpg"  # Replace with your image path
        
        book_title, book_description = analyze_book_image(input_image_path)
        output_files = []

        with open(TEXT_POSITIONS_FILE, "r") as f:
            text_positions_data = json.load(f)

        os.makedirs(OUTPUT_FOLDER, exist_ok=True)  # Ensure the output folder exists

        for index, template in enumerate(TEMPLATES):
            try:
                output_filename = f"output{index + 1}.png"
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)

# Delete the existing file before writing new content
                if os.path.exists(output_path):
                    os.remove(output_path)

                output_path = os.path.join(OUTPUT_FOLDER, output_filename)

                print(f"Processing template {index + 1}: {template['path']}")

                processed_template = overlay_image_on_template(template["path"], input_image_path, output_path, template["position"])
                
                if not processed_template:
                    print(f"Error: No template generated for {template['path']}")
                    continue

                if template["path"] in text_positions_data:
                    text_data = {"title": book_title, "description": book_description}
                    overlay_text_on_template(processed_template, output_path, text_data, text_positions_data, template["path"])
                
                try:
                    processed_template.save(output_path, format="PNG")
                    print(f"Successfully saved: {output_path}")
                except Exception as e:
                    print(f"Failed to save {output_path}: {e}")
                
                output_files.append(output_filename)
            except Exception as e:
                print(f"Error processing template {index + 1}: {e}")

        return jsonify({
            "message": "Posters generated successfully",
            "generated_count": len(output_files),
            "output_files": output_files
        }), 200
    except Exception as e:
        print(f"Error generating posters: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)

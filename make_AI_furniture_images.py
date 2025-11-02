import os
import json
import re
import pandas as pd
import requests
from openai import OpenAI
from keys import OpenAI_key

# Use OPENAI_API_KEY env var (do not hardcode)
client = OpenAI(api_key=OpenAI_key)


# Simple price map (USD per image). UPDATE these values to match the
# official OpenAI image-generation pricing for the model & size you use.
# Keys: (model_name, size). Values: price per image in USD.
DEFAULT_PRICE_MAP = {
# DALL-E 3 pricing - HD quality
    ("dall-e-3-hd", "1024x1024"): 0.080,    # HD quality
    ("dall-e-3-hd", "1024x1536"): 0.120,    # HD quality
    ("dall-e-3-hd", "1536x1024"): 0.120,    # HD quality
}
# Allowed image sizes (only these are accepted by the API)
ALLOWED_SIZES = {"1024x1024", "1024x1536", "1536x1024", "auto"}

def estimate_image_cost(model, size, n=1, price_map=None):
    """Return estimated USD cost for an image-generation request."""
    if size not in ALLOWED_SIZES:
        raise ValueError(f"size must be one of {sorted(ALLOWED_SIZES)}")
    pm = price_map or DEFAULT_PRICE_MAP
    unit = pm.get((model, size))
    if unit is None:
        # fallback: try model-only key or map 'auto' -> default size
        unit = pm.get((model, None))
        if unit is None and size == "auto":
            unit = pm.get((model, "1024x1024"))
    if unit is None:
        # unknown price: return 0.0 and caller should supply prices
        return 0.0
    return float(unit) * int(n)

# Allowed location and season choices
ALLOWED_LOCATIONS = {"rural", "urban", "suburban"}
ALLOWED_SEASONS = {"spring", "summer", "autumn", "winter"}  # accept 'fall' -> 'autumn'

def prompt_from_params(category, material, color, series=None, style=None, attributes=None,
                       location=None, season=None):
    #(category, material, color, location=None, season=None, style="photorealistic")
    """
    Build a prompt that includes optional location and season to influence the
    furniture's appearance only (no props, staging, or background elements).
    Location and season adjust finishes, materials, and color accents on the
    furniture itself.
    """
    loc_phrase = ""
    sea_phrase = ""

    if location:
        loc_norm = str(location).strip().lower()
        if loc_norm not in ALLOWED_LOCATIONS:
            raise ValueError(f"location must be one of {sorted(ALLOWED_LOCATIONS)}")
        if loc_norm == "rural":
            loc_phrase = "rustic finish with visible wood grain and subtly distressed details on the furniture"
        elif loc_norm == "urban":
            loc_phrase = "sleek contemporary finish with matte metal or concrete-inspired details on the furniture"
        elif loc_norm == "suburban":
            loc_phrase = "classic home-style finish with soft upholstery and comfortable proportions"

    if season and pd.notna(season):
        sea_norm = season.strip().lower()
        if sea_norm == "fall":
            sea_norm = "autumn"
        if sea_norm not in ALLOWED_SEASONS:
            raise ValueError(f"season must be one of {sorted(ALLOWED_SEASONS)} (accepts 'Fall' -> 'Autumn')")
        if sea_norm == "spring":
            sea_phrase = "light, fresh color palette and lightweight fabrics applied to the furniture"
        elif sea_norm == "summer":
            sea_phrase = "bright warm accents and breathable materials used on the furniture"
        elif sea_norm == "autumn":
            sea_phrase = "warm, muted tones and textured upholstery on the furniture"
        elif sea_norm == "winter":
            sea_phrase = "cool desaturated tones and plush fabrics on seating surfaces"
    
    full_category = f"{series} {category}" if series and pd.notna(series) else category
    final_style = style if style and pd.notna(style) else "photorealistic"
    attributes_part = f", {attributes}" if attributes and pd.notna(attributes) else ""
    extras = ", ".join([p for p in (loc_phrase, sea_phrase) if p])
    extras_part = f", featuring {extras}" if extras else ""
    '''
    return (
        #f"A {color} {material} {category}, {style}{extras_part}, product-style photo on a clean white background, "
        #"studio lighting, high detail, high resolution."
        f"You are a furniture designer."
        f"Create an image for a {color} {material} {full_category}, {final_style}{extras_part}, commercial product photography, on a seamless light gray background, "
        f"with soft studio lighting and subtle shadows{attributes_part}, high detail, high resolution."
    )'''
    return (
        f"You are a modern furniture product designer creating clean product photography. "
        f"Create a product photography of a single piece of a {color} {material} {full_category}, {final_style} style{extras_part}{attributes_part}. "
        f"Clean white studio background, professional lighting, high resolution, minimalist composition, no other furniture or props. "
        f"Remove all text, remove all words, remove all letters, remove all typography, remove all branding items, "
        f"remove all labels and graphic design elements completely from the image."
        f"IMPORTANT: Do not include any text, labels, words, letters, or typography in the image."
    )


def _safe(s):
    s = "" if s is None else str(s)
    s = s.strip().lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    return s.strip('_') or 'none'

def generate_and_save_image(row_id, category, material, color, series=None, style=None, 
                           attributes=None, location=None, season=None,
                            out_folder="Pictures", size="1024x1024", 
                            model="dall-e-3", price_map=None):
    """Generate a single image and save it into out_folder folder. Filename derived from inputs."""
    if size not in ALLOWED_SIZES:
        raise ValueError(f"size must be one of {sorted(ALLOWED_SIZES)}")

    prompt = prompt_from_params(category, material, color, series=series, style=style, 
                               attributes=attributes, location=location, season=season)
    
    print(f"DEBUG: Prompt for row {row_id} is: {prompt}")
    
    # Request image with URL response format instead of base64
    resp = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        response_format="url"  # This tells OpenAI to return a URL instead of base64
    )
    
    # Get the image URL from the response
    image_url = resp.data[0].url
    print(f"DEBUG: Image URL for row {row_id}: {image_url}")
    
    # Download the image from the URL
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        image_bytes = response.content
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from URL: {e}")
        raise

    # Ensure output folder exists (out_folder is treated as a folder)
    os.makedirs(out_folder or ".", exist_ok=True)

    # Build a safe filename from provided fields
    row_s = _safe(row_id)
    cat_s = _safe(category)
    mat_s = _safe(material)
    col_s = _safe(color)
    loc_s = _safe(location)
    sea_s = _safe(season)
    base = f"{row_s}_{cat_s}_{mat_s}_{col_s}_{loc_s}_{sea_s}"
    filename = base + ".png"
    full_path = os.path.join(out_folder, filename)

    # Save the image file
    with open(full_path, "wb") as f:
        f.write(image_bytes)
    print(f"DEBUG: Saved image to: {full_path}")

    # Create JSON metadata file path (same base name, but .json extension)
    json_filename = base + ".json"
    json_full_path = os.path.join(out_folder, json_filename)

    # Save a small JSON sidecar with parameters and prompt for traceability
    #estimated_cost = estimate_image_cost("dall-e-3", size, price_map=price_map)
    meta = {
        "row_id": row_id,
        "category": category,
        "series": series,
        "style": style,
        "material": material,
        "color": color,
        "attributes": attributes,
        "location": location,
        "season": season,
        "prompt": prompt,
        "size": size,
        "model": model,
        "image_file": full_path,
        "json_file": json_full_path,
    }
    
    # Save JSON metadata file
    try:
        with open(json_full_path, "w", encoding="utf-8") as jf:
            json.dump(meta, jf, indent=2)
        print(f"DEBUG: Saved JSON metadata to: {json_full_path}")
    except Exception as e:
        print(f"ERROR: Could not save JSON metadata to {json_full_path}: {e}")
        raise

    return full_path, meta

# Example usage (Windows path shown)
if __name__ == "__main__":

    # read in furniture_data_generated.csv into a dataframe
    df = pd.read_csv("furniture_data_generated.csv")
    
    # Add img column if it doesn't exist
    if 'img' not in df.columns:
        df['img'] = ''

    GENERATION_LIMIT = 100 # max number of images to generate in one run
    generated_count = 0

    # iterate over rows and generate images
    for idx, row in df.iterrows():
        # skip if img column is already populated
        if pd.notna(row.get('img')) and row.get('img') != '':
            print(f"Skipping row {idx} (img already exists)")
            continue    

        print("working on row", idx)
        image_path, meta = generate_and_save_image(
            row_id=idx,
            category=row['category'],
            series=row.get('series'),
            style=row.get('style'),
            attributes=row.get('attributes'),
            material=row['material'],
            color=row['color'],
            location=row.get('location'),
            season=row.get('season'),
            out_folder="Pictures", # output folder
        )
        
        # print all input values used to generate the image
        print(f"Row ID: {idx}")
        print(f"Category: {row['category']}")
        print(f"Series: {row.get('series')}")
        print(f"Style: {row.get('style')}")
        print(f"Material: {row['material']}")
        print(f"Color: {row['color']}")
        print(f"Attributes: {row.get('attributes')}")
        print(f"Location: {row.get('location')}")
        print(f"Season: {row.get('season')}")   
        print("Saved:", image_path)
        print("Metadata:", meta)

        # insert image path into img column of dataframe
        df.at[idx, 'img'] = os.path.basename(image_path)
        # save updated dataframe 
        df.to_csv("furniture_data_generated.csv", index=False) 
        #break # test one row only
        generated_count += 1
        if generated_count >= GENERATION_LIMIT:
            print(f"Reached generation limit of {GENERATION_LIMIT}, stopping.")
            break
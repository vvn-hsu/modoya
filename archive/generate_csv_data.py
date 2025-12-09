import pandas as pd
import random
from collections import Counter
import numpy as np

def calculate_similarity(row1, row2):
    """Calculate similarity between two rows (0 = identical, 1 = completely different)"""
    matches = sum(1 for a, b in zip(row1, row2) if a == b and a != '' and b != '')
    non_empty_pairs = sum(1 for a, b in zip(row1, row2) if a != '' and b != '')
    if non_empty_pairs == 0:
        return 0
    return matches / non_empty_pairs

def analyze_dataframe_randomness(df):
    """Analyze the randomness and diversity of the generated dataframe"""
    print("\n" + "="*50)
    print("RANDOMNESS ANALYSIS")
    print("="*50)
    
    # 1. Check for exact duplicates
    duplicates = df.duplicated().sum()
    print(f"Exact duplicate rows: {duplicates}")
    
    # 2. Check combination frequency
    print(f"Unique combinations: {df.drop_duplicates().shape[0]} out of {df.shape[0]} total rows")
    
    # 3. Find most similar pairs
    print("\nMost similar row pairs (similarity > 0.6):")
    similar_pairs = []
    
    for i in range(len(df)):
        for j in range(i+1, len(df)):
            similarity = calculate_similarity(df.iloc[i].values, df.iloc[j].values)
            if similarity > 0.6:  # More than 60% similar
                similar_pairs.append((i, j, similarity))
    
    # Sort by similarity and show top 5
    similar_pairs.sort(key=lambda x: x[2], reverse=True)
    
    if similar_pairs:
        print(f"Found {len(similar_pairs)} pairs with >60% similarity")
        for i, (row1_idx, row2_idx, sim) in enumerate(similar_pairs[:5]):
            print(f"\nPair {i+1} (Rows {row1_idx} & {row2_idx}, {sim:.2%} similar):")
            print(f"  Row {row1_idx}: {df.iloc[row1_idx].values}")
            print(f"  Row {row2_idx}: {df.iloc[row2_idx].values}")
    else:
        print("No highly similar pairs found (good diversity!)")
    
    # 4. Column distribution analysis
    print(f"\nColumn value distributions:")
    for col in df.columns:
        non_empty = df[df[col] != ''][col]
        if len(non_empty) > 0:
            value_counts = non_empty.value_counts()
            entropy = -sum((p := count/len(non_empty)) * np.log2(p) for count in value_counts)
            max_entropy = np.log2(len(value_counts))
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            print(f"  {col}: {len(value_counts)} unique values, entropy: {normalized_entropy:.3f}")
            
            # Show most/least frequent values
            most_common = value_counts.iloc[0]
            least_common = value_counts.iloc[-1]
            print(f"    Most frequent: '{value_counts.index[0]}' ({most_common}x, {most_common/len(non_empty):.1%})")
            if len(value_counts) > 1:
                print(f"    Least frequent: '{value_counts.index[-1]}' ({least_common}x, {least_common/len(non_empty):.1%})")
    
    return similar_pairs

def is_dataframe_random_enough(df, verbose=True):
    """
    Determine if the dataframe has acceptable randomness/diversity
    Returns True if random enough, False if needs regeneration
    """
    if verbose:
        print("\n" + "="*50)
        print("RANDOMNESS ANALYSIS")
        print("="*50)
    
    # Heuristic 1: No exact duplicates allowed
    duplicates = df.duplicated().sum()
    duplicate_rate = duplicates / len(df)
    
    # Heuristic 2: At least 90% unique combinations
    unique_combinations = df.drop_duplicates().shape[0]
    uniqueness_rate = unique_combinations / len(df)
    
    # Heuristic 3: No pairs should be more than 70% similar
    high_similarity_pairs = 0
    max_similarity = 0
    
    for i in range(len(df)):
        for j in range(i+1, len(df)):
            similarity = calculate_similarity(df.iloc[i].values, df.iloc[j].values)
            if similarity > max_similarity:
                max_similarity = similarity
            if similarity > 0.7:  # 70% similarity threshold
                high_similarity_pairs += 1
    
    # Heuristic 4: Each column should have reasonable entropy (> 0.7 for diverse data)
    low_entropy_columns = 0
    min_entropy = 1.0
    
    for col in df.columns:
        non_empty = df[df[col] != ''][col]
        if len(non_empty) > 0:
            value_counts = non_empty.value_counts()
            if len(value_counts) > 1:  # Only calculate if there's variety
                entropy = -sum((p := count/len(non_empty)) * np.log2(p) for count in value_counts)
                max_entropy = np.log2(len(value_counts))
                normalized_entropy = entropy / max_entropy
                
                if normalized_entropy < min_entropy:
                    min_entropy = normalized_entropy
                    
                if normalized_entropy < 0.7:  # Low entropy threshold
                    low_entropy_columns += 1
    
    # Define our randomness criteria
    criteria = {
        'no_duplicates': duplicate_rate == 0,
        'high_uniqueness': uniqueness_rate >= 0.90,
        'low_similarity': high_similarity_pairs == 0,
        'good_entropy': low_entropy_columns <= 1  # Allow 1 column to have low entropy
    }
    
    # Overall assessment
    passes_all_criteria = all(criteria.values())
    
    if verbose:
        print(f"Exact duplicates: {duplicates} ({duplicate_rate:.1%}) - {'✓' if criteria['no_duplicates'] else '✗'}")
        print(f"Unique combinations: {unique_combinations}/{len(df)} ({uniqueness_rate:.1%}) - {'✓' if criteria['high_uniqueness'] else '✗'}")
        print(f"High similarity pairs (>70%): {high_similarity_pairs} - {'✓' if criteria['low_similarity'] else '✗'}")
        print(f"Maximum similarity found: {max_similarity:.1%}")
        print(f"Low entropy columns (<0.7): {low_entropy_columns} - {'✓' if criteria['good_entropy'] else '✗'}")
        print(f"Minimum column entropy: {min_entropy:.3f}")
        
        print(f"\nOVERALL ASSESSMENT: {'✓ RANDOM ENOUGH' if passes_all_criteria else '✗ NEEDS REGENERATION'}")
        
        if not passes_all_criteria:
            print("Failed criteria:", [k for k, v in criteria.items() if not v])
    
    return passes_all_criteria

def generate_furniture_columns_with_validation(num_rows=100, max_attempts=10):
    """Generate furniture data with validation, regenerating until random enough"""
    
    styles = [
        'Mid-Century Modern', 'Minimalist', 'Scandinavian', 'Bauhaus', 'Traditional', 
        'Farmhouse', 'Rustic', 'Art Deco', 'Bohemian (Bojo)', 'Japandi', 
        'Wabi-Sabi', 'Coastal', 'Industrial', 'Retro'
    ]
    category_series_map = {
        'Chair': ['Eames Lounge Chair', 'Wassily Chair', 'Barcelona Chair', 'Womb Chair', 'Egg Chair', 'Wishbone Chair (Y-Chair)', 'Adirondack Chair', 'Panton Chair'],
        'Sofa': ['Chesterfield Sofa', 'Togo Sofa', 'LC2 Sofa', 'Noguchi Freeform Sofa', 'Sectional Sofa', 'Loveseat'],
        'Table': ['Noguchi Coffee Table', 'Saarinen Tulip Table', 'Parsons Table', 'Dining Table', 'Side Table', 'Coffee Table'],
        'Lamp': ['Arco Floor Lamp', 'PH Artichoke Lamp', 'Nesso Table Lamp', 'Floor Lamp', 'Desk Lamp'],
        'Storage': ['Bookshelf', 'Dresser', 'Sideboard', 'TV Stand', 'Cabinet']
    }
    materials_map = {
        'Chair': ['Walnut Wood', 'Light Oak', 'Bouclé Fabric', 'Velvet', 'Tweed', 'Linen', 'Black Leather', 'Brown Leather', 'Polished Chrome', 'Brushed Brass', 'Matte Black Steel', 'Rattan'],
        'Sofa': ['Bouclé Fabric', 'Velvet', 'Tweed', 'Linen', 'Black Leather', 'Brown Leather', 'Vegan Leather', 'Suede', 'Walnut Wood base'],
        'Table': ['Walnut Wood', 'Light Oak', 'Teak', 'Bent Plywood', 'Carrara Marble', 'Terrazzo', 'Smoked Glass', 'Polished Chrome', 'Matte Black Steel'],
        'Lamp': ['Brushed Brass', 'Matte Black Steel', 'Copper', 'Carrara Marble base', 'Smoked Glass', 'Acrylic', 'Linen shade'],
        'Storage': ['Walnut Wood', 'Light Oak', 'Teak', 'Bent Plywood', 'Matte Black Steel', 'Rattan', 'Cane']
    }
    colors = [
        'Beige', 'Off-white', 'Light Gray', 'Charcoal Gray', 'Warm Taupe', 'Terracotta', 
        'Olive Green', 'Mustard Yellow', 'Walnut Brown', 'Deep Teal', 'Emerald Green', 
        'Burnt Orange', 'Navy Blue', 'Black', 'White', 'Natural Wood'
        # Removed '' empty string
    ]
    attributes = [
        'Plush', 'Soft', 'Textured', 'Distressed', 'High-gloss', 'Matte finish', 
        'Curvy', 'Geometric', 'Organic shape', 'Modular', 'Elegant', 
        'Playful', 'Statement piece', 'Airy', 'Vintage look'
        # Removed '' empty string
    ]
    locations = ['rural', 'urban', 'suburban']  # Removed '' empty string
    seasons = ['spring', 'summer', 'autumn', 'winter']  # Removed '' empty string

    categories_keys = list(category_series_map.keys())
    
    for attempt in range(max_attempts):
        print(f"\nGeneration attempt {attempt + 1}...")
        
        # Generate data
        categories_list = []
        series_list = []
        styles_list = []
        materials_list = []
        colors_list = []
        attributes_list = []
        locations_list = []
        seasons_list = []

        for _ in range(num_rows):
            category = random.choice(categories_keys)
            series = random.choice(category_series_map[category])
            material = random.choice(materials_map[category])
            style = random.choice(styles)
            color = random.choice(colors)
            attribute = random.choice(attributes)
            location = random.choice(locations)
            season = random.choice(seasons)

            categories_list.append(category)
            series_list.append(series)
            styles_list.append(style)
            materials_list.append(material)
            colors_list.append(color)
            attributes_list.append(attribute)
            locations_list.append(location)
            seasons_list.append(season)

        # Create DataFrame
        df = pd.DataFrame({
            'category': categories_list,
            'series': series_list,
            'style': styles_list,
            'material': materials_list,
            'color': colors_list,
            'attributes': attributes_list,
            'location': locations_list,
            'season': seasons_list
        })
        
        # Check if random enough
        if is_dataframe_random_enough(df, verbose=(attempt == 0 or attempt == max_attempts-1)):
            print(f"✓ Successfully generated random data on attempt {attempt + 1}")
            break
        else:
            print(f"✗ Attempt {attempt + 1} failed randomness test, regenerating...")
    else:
        print(f"⚠ Warning: Could not generate sufficiently random data in {max_attempts} attempts")
        print("Using last generated dataset (may have some similarity issues)")
    
    # Save to CSV file
    csv_filename = 'furniture_data_generated.csv'
    df.to_csv(csv_filename, index=False)
    
    print(f"\nGenerated {num_rows} rows of furniture data")
    print(f"Data saved to: {csv_filename}")
    print("\nFirst 5 rows of the generated data:")
    print(df.head())
    
    return df

if __name__ == "__main__":
    df = generate_furniture_columns_with_validation(100, max_attempts=100)
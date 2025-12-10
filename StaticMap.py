import pandas as pd
import numpy as np
import arc_classifier
import grc_classifier
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
import os
import zipfile
import xml.etree.ElementTree as ET

# 1. STREAMING & PROCESSING
def read_kmz_polygon(file_path):
    """
    Extracts polygon coordinates from a KMZ file.
    Assumes the KMZ contains a KML with a Polygon/LinearRing structure.
    """
    print(f"Reading KMZ file: {file_path}")
    
    with zipfile.ZipFile(file_path, 'r') as kmz:
        # Find the first .kml file in the archive
        kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
        if not kml_files:
            raise ValueError("No KML file found inside the KMZ archive.")
        
        kml_filename = kml_files[0]
        with kmz.open(kml_filename, 'r') as kml_file:
            # Parse XML
            tree = ET.parse(kml_file)
            root = tree.getroot()
            
            # XML namespaces can be tricky in KML (e.g., {http://www.opengis.net/kml/2.2})
            # We search for 'coordinates' tag by ignoring namespace prefix
            coords_text = None
            for elem in root.iter():
                if elem.tag.endswith('coordinates'):
                    coords_text = elem.text
                    break
            
            if not coords_text:
                raise ValueError("No 'coordinates' tag found in KML.")
            
            # Parse coordinate string
            # Format usually: lon,lat,alt lon,lat,alt ...
            coords_list = []
            for coord in coords_text.strip().split():
                parts = coord.split(',')
                if len(parts) >= 2:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    coords_list.append((lat, lon)) # Store as (lat, lon) for our logic
            
            return coords_list

def stream_grid_points(poly_coords, acc):
    """
    Generator that streams (yields) lat/lon points within a polygon.
    
    Args:
        poly_coords (list): List of (lat, lon) tuples.
        acc (float): Step size in degrees.
    
    Yields:
        tuple: (lat, lon)
    """
    # Create a Shapely polygon
    # Note: Shapely uses (x, y) -> (lon, lat). We must be careful with order.
    # Input is (lat, lon), so we swap for shapely: (lon, lat)
    shapely_poly_coords = [(lon, lat) for lat, lon in poly_coords]
    poly = Polygon(shapely_poly_coords)
    
    # Get the bounding box of the polygon to limit iteration
    min_lon, min_lat, max_lon, max_lat = poly.bounds
    
    # Generate ranges
    # We use numpy arange for float steps
    lats = np.arange(min_lat, max_lat, acc)
    lons = np.arange(min_lon, max_lon, acc)
    
    print(f"Scanning bounding box: Lat[{min_lat:.4f}-{max_lat:.4f}], Lon[{min_lon:.4f}-{max_lon:.4f}]")
    
    for lat in lats:
        for lon in lons:
            # Check if point is inside the polygon
            if poly.contains(Point(lon, lat)):
                yield lat, lon

def process_grid_data(poly_coords, acc, alt, output_file="GRC.csv"):
    """
    Consumes the stream, classifies data, saves to CSV, and returns a DataFrame.
    """
    data_buffer = []
    
    print("Starting stream processing...")
    
    # Iterate through the generator (Stream)
    for lat, lon in stream_grid_points(poly_coords, acc):
        
        # 1. Call GRC Classifier
        grc = grc_classifier.final_grc(lat, lon)
        
        if grc is None:
            # Option A: Skip this point entirely (Recommended)
            # print(f"Skipping point {lat}, {lon}: GRC returned None")
            continue 
            
            # Option B: Assign a default value (e.g., 0)
            # grc = 0 
        
        # 2. Call ARC Classifier
        in_ctrl, arc_label, arc, reason = arc_classifier.air_risk(
            lat, lon, alt, grc)
        
        # 3. Append to buffer
        data_buffer.append({
            'lat': lat,
            'lon': lon,
            'alt': alt,
            'grc': grc,
            'arc': arc
        })
    
    if not data_buffer:
        print("No points found within the polygon. Try increasing accuracy (smaller step size).")
        return pd.DataFrame()

    # Create DataFrame
    df = pd.DataFrame(data_buffer)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"Data processed and saved to {output_file}. Total points: {len(df)}")
    
    return df

# 2. VISUALIZATION
def plot_heatmap(df, value_column='arc'):
    """
    Plots a scattered heatmap of the grid cells.
    """
    if df.empty:
        print("DataFrame is empty, cannot plot.")
        return

    plt.figure(figsize=(10, 8))
    
    # We use a scatter plot with square markers to simulate grid cells.
    # s=marker_size can be adjusted based on density.
    sc = plt.scatter(
        df['lon'], 
        df['lat'], 
        c=df[value_column], 
        cmap='viridis', 
        marker='s', 
        s=50, 
        alpha=0.9,
        edgecolors='none'
    )
    
    plt.colorbar(sc, label=f'{value_column.upper()} Value')
    plt.title(f'Grid Cell Heatmap: {value_column.upper()} Distribution')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # Ensure aspect ratio represents geographical reality reasonably well
    plt.axis('equal')
    
    plt.tight_layout()
    plt.show()

# ==========================================
# 4. MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    # --- INPUTS ---
    USE_KMZ = True # Set to True if you have a .kmz file
    KMZ_PATH = "StaticMap1.kmz"
    input_poly = []

    if USE_KMZ and os.path.exists(KMZ_PATH):
        try:
            input_poly = read_kmz_polygon(KMZ_PATH)
            print(f"Successfully loaded polygon with {len(input_poly)} points from KMZ.")
        except Exception as e:
            print(f"Error reading KMZ: {e}")
            exit()
    else:
        # Fallback: Manual Example Polygon (Roughly NYC area)
        # (Lat, Lon)
        print("Using manual fallback polygon coordinates.")
        input_poly = [
            (40.7128, -74.0060), # Point 1
            (40.7228, -74.0060), # Point 2
            (40.7228, -73.9900), # Point 3
            (40.7128, -73.9960)  # Point 4
        ]
    
    input_acc = 0.001  # Preferred Accuracy (Step size in degrees)
    # Note: 0.001 degrees is approx 111 meters. 0.0001 is approx 11 meters.

    input_alt = 140.0  # Altitude Input in meter
    
    # Run the generator, classify, and save
    df_result = process_grid_data(input_poly, input_acc, input_alt)
    
    # Plotting the 'arc' column as requested
    plot_heatmap(df_result, value_column='grc')
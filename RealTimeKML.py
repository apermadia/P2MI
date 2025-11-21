import simplekml
import os
from datetime import datetime

class RealTimeKML:
    def __init__(self):
        self.coordinates = []
        
    def add_point(self, lat, lon, alt):
        """
        Input: lat, lon, alt (meter)
        """
        # Format simplekml: (Longitude, Latitude, Altitude)
        self.coordinates.append((lon, lat, alt))

    def save_kml(self, save_folder="flight_path"):
        """
        Saving KML into folder.
        """
        if not self.coordinates:
            print("Data kosong.")
            return

        # Format: flight_path_20251121_143000.kml
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"flight_path_{timestamp}.kml" 
        
        # Cross-platform safe
        full_output_path = os.path.join(save_folder, filename)

        # Object KML
        kml = simplekml.Kml(name=f"Log {timestamp}")
        linestring = kml.newlinestring(name="Flight Path")
        linestring.coords = self.coordinates
        
        # Styling
        linestring.extrude = 1
        linestring.altitudemode = simplekml.AltitudeMode.absolute
        linestring.style.linestyle.width = 4
        linestring.style.linestyle.color = simplekml.Color.cyan
        
        # Save
        try:
            kml.save(full_output_path)
            print(f"[SUKSES] KML saved in: {full_output_path}")
        except Exception as e:
            print(f"[ERROR] KML failed to save: {e}")


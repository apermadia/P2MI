import rasterio
import numpy as np
from pyproj import Transformer

GEOTIFF_FILE_PATH = r'c:\Users\bevan\OneDrive - Institut Teknologi Bandung\S2-1\P2MI\GRC_IDN.tif'


class _GRC_Engine:
    """
    Class for loading Ground Risk Class (GRC) dari GeoTIFF.
    GeoTIFF, from CRS ESRI:54009 (Mollweide) into lat/lon convert first to CRS before indexing raster.
    """

    def __init__(self, geotiff_path):
        self.grc_map_array = None
        self.transform = None
        self.crs = None
        self.transformer = None

        try:
            with rasterio.open(geotiff_path) as src:
                # Load raster data
                self.grc_map_array = src.read(1)
                self.transform = src.transform
                self.crs = src.crs

                # Transformer WGS84 (EPSG:4326) → CRS raster (ESRI:54009)
                self.transformer = Transformer.from_crs(
                    "EPSG:4326",
                    src.crs,
                    always_xy=True  # ensures using x=lon, y=lat
                )

            print("GRC loaded.")

        except Exception as e:
            print(
                f"ERROR: Failed to load file GeoTIFF '{geotiff_path}'. Error: {e}")

    def _map_to_final_grc(self, igrc_value):
        """
        Classifying iGRC (0–6) to Final GRC based on SORA.
        """
        grc_map = {
            0: 1,
            1: 3,
            2: 4,
            3: 5,
            4: 6,
            5: 7,
            6: 8
        }
        return grc_map.get(igrc_value, None)

    def get_grc(self, lat, lon):
        """
        get Final GRC value based on lat/lon (derajat).
        Convert to CRS raster (ESRI:54009) before indexing.
        """

        if self.grc_map_array is None:
            print("Error: Raster GRC didn't load.")
            return None

        try:
            # 1. Convert lon/lat from EPSG:4326 → Mollweide (meter)
            x, y = self.transformer.transform(lon, lat)

            # 2. Convert Mollweide → index pixel raster
            col, row = ~self.transform * (x, y)
            row, col = int(row), int(col)

            # print(f"Pixel location → Row: {row}, Col: {col}")

            # 3. Check bounds raster
            if row < 0 or col < 0 or row >= self.grc_map_array.shape[0] or col >= self.grc_map_array.shape[1]:
                print(f"Warning: Position ({lat}, {lon}) is out of bound.")
                return None

            # 4. iGRC value
            igrc_raw = int(self.grc_map_array[row, col])

            # 5. Mapping iGRC → Final GRC
            return self._map_to_final_grc(igrc_raw)

        except Exception as e:
            print(f"ERROR saat membaca GRC untuk ({lat}, {lon}): {e}")
            return None


# ========================================================================
# Inisialisasi mesin GRC
grc_engine = _GRC_Engine(GEOTIFF_FILE_PATH)


# ========================================================================
# Fungsi wrapper agar lebih mudah dipanggil
def final_grc(lat, lon):
    if grc_engine:
        return grc_engine.get_grc(lat, lon)

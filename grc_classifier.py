import rasterio
import numpy as np

GEOTIFF_FILE_PATH = r'C:\Users\rtldd\Documents\P2MI\GRC.tif' 

class _GRC_Engine:
    """
    Class untuk load dan save data population density GRC
    """
    def __init__(self, geotiff_path):
        self.grc_map_array = None
        self.transform = None
        
        try:

            with rasterio.open(geotiff_path) as src:
                self.grc_map_array = src.read(1) # Baca data (GRC 0-6)
                self.transform = src.transform   # Save konversi
            print("GRC loaded.")
        
        except Exception as e:
            print(f"ERROR: Gagal memuat file GeoTIFF '{geotiff_path}'.")

    def _map_to_final_grc(self, igrc_value):
        """
        Memetakan nilai iGRC (0-6) ke Final GRC berdasarkan
        kolom kecepatan < 35 m/s (27.78 m/s) pada tabel SORA.
        """
        # Dictionary pemetaan sesuai permintaan Anda
        grc_map = {
            0: 1,  # iGRC 0 -> Final GRC 1
            1: 3,  # iGRC 1 -> Final GRC 3
            2: 4,  # iGRC 2 -> Final GRC 4
            3: 5,  # iGRC 3 -> Final GRC 5
            4: 6,  # iGRC 4 -> Final GRC 6
            5: 7,  # iGRC 5 -> Final GRC 7
            6: 8   # iGRC 6 -> Final GRC 8
        }
        return grc_map.get(igrc_value, None) # Kembalikan None jika nilai tidak ada di map

    def get_grc(self, lat, lon):
        """
        Ambil (lat, lon) dan return Final GRC.
        """
        # 1. Cek inisialisasi
        if self.grc_map_array is None:
            print("Error: GRC tidak dimuat.")
            return None

        try:
            # 2. Konversi (Lat, Lon) -> (baris, kolom)
            row, col = ~self.transform * (lat, lon)
            row, col = int(row), int(col)
            print(row, col)
            
            # 3. Ambil nilai iGRC (0-6) mentah dari peta
            igrc_raw = int(self.grc_map_array[row, col])
            
            # 4. Petakan ke Final GRC
            final_grc = self._map_to_final_grc(igrc_raw)
            
            return final_grc

        except Exception as e:
            # Error ini biasanya terjadi jika (lat, lon) berada di luar jangkauan (boundaries) file GeoTIFF.
            print(f"Warning: Posisi ({lat}, {lon}) di luar jangkauan peta. {e}")
            return None

# ==============================================================================
# 1. INISIALISASI MESIN GRC (Dijalankan satu kali saat file di-import)
grc_engine = _GRC_Engine(GEOTIFF_FILE_PATH)


# ==============================================================================
# 2. Ambil koordinat, return Final GRC
def final_grc(lat, lon):
    if grc_engine:
        return grc_engine.get_grc(lat, lon)
    return None

# ==============================================================================
# 3. TEST CASE
if __name__ == "__main__":
    # Gunakan koordinat yang Anda tahu pasti ada di dalam peta Anda.
    test_lat_1 = -6.917464 # Ganti dengan Lat Anda
    test_lon_1 = 107.619125 # Ganti dengan Lon Anda (misal, area iGRC 3)

    test_lat_2 = -6.258351632715808 # Ganti dengan Lat Anda
    test_lon_2 = 106.83125543446322 # Ganti dengan Lon Anda (misal, area iGRC 6)

    test_lat_luar_peta = 0
    test_lon_luar_peta = 0
    # ----------------------------------------
    
    # Tes 1
    final_grc_1 = final_grc(test_lat_1, test_lon_1)
    print(f"Tes Posisi 1 ({test_lat_1}, {test_lon_1}) -> Final GRC: {final_grc_1}")

    # Tes 2
    final_grc_2 = final_grc(test_lat_2, test_lon_2)
    print(f"Tes Posisi 2 ({test_lat_2}, {test_lon_2}) -> Final GRC: {final_grc_2}")

    # Tes 3 (Di luar Peta)
    final_grc_3 = final_grc(test_lat_luar_peta, test_lon_luar_peta)
    print(f"Tes Posisi 3 ({test_lat_luar_peta}, {test_lon_luar_peta}) -> Final GRC: {final_grc_3}")
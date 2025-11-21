import time
import csv
import xpc
import arc_classifier
from datetime import datetime
import grc_classifier
import plotting as plt
import os
import RealTimeKML

# Folder name
save_folder = "logs"

# Create folder if not exists
os.makedirs(save_folder, exist_ok=True)


UPDATE_RATE_HZ = 2
PERIOD = 1 / UPDATE_RATE_HZ

client = xpc.XPlaneConnect(xpHost='localhost', xpPort=49009)
print("Connected to X-Plane")

filename = os.path.join(
    save_folder, f"flight_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

csv_file = open(filename, "w", newline="", encoding="utf-8")
writer = csv.writer(csv_file)
writer.writerow(["t_sec", "lat", "lon", "alt_m", "hdg_deg",
                "spd_mps", "grc", "arc_label", "arc", "arc_rule"])

print(f"Logging to {filename}")
kml = RealTimeKML.RealTimeKML()

# --- Start time reference (t=0) ---
t0 = time.time()

try:
    while True:
        lat = client.getDREF("sim/flightmodel/position/latitude")[0]
        lon = client.getDREF("sim/flightmodel/position/longitude")[0]
        alt = client.getDREF("sim/flightmodel/position/elevation")[0]
        hdg = client.getDREF("sim/flightmodel/position/psi")[0]
        spd = client.getDREF("sim/flightmodel/position/groundspeed")[0]

        grc_final = grc_classifier.final_grc(lat, lon)
        in_ctrl, arc_label, arc, reason = arc_classifier.air_risk(
            lat, lon, alt, grc_final)

        kml.add_point(lat, lon, alt)


        # --- Time starts from zero ---
        t_now = time.time() - t0

        writer.writerow([t_now, lat, lon, alt, hdg,
                        spd, grc_final, arc_label, arc, reason["rule"]])
        csv_file.flush()



        print(f"t={t_now:6.2f}s | {lat:.6f}, {lon:.6f}, {alt:.1f} m, grc={grc_final}, "
              f"{hdg:.1f}°, {spd:.1f} m/s, {arc_label} ({reason['rule']})",
              end='\r', flush=True)
        plt.update_dashboard(t_now, arc, grc_final, reason['rule'], arc_label)
        time.sleep(PERIOD)

except KeyboardInterrupt:
    print("\nStopped by user.")

except Exception as e:
    print(f"\nERROR: {e}\nSaving CSV before exiting...")

finally:
    try:
        csv_file.close()
        kml.save_kml()
    except:
        pass

    try:
        client.close()
        kml.save_kml()
    except:
        pass

    print(f"CSV saved as {filename}")

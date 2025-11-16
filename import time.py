import time
import xpc
import arc_classifier

UPDATE_RATE_HZ = 2          # 10 times per second
PERIOD = 1/10 / UPDATE_RATE_HZ

client = xpc.XPlaneConnect(xpHost='192.168.10.2', xpPort=49009)
print("Connected to X-Plane")

try:
    while True:
        # --- Read position data from X-Plane ---
        lat = client.getDREF("sim/flightmodel/position/latitude")
        lon = client.getDREF("sim/flightmodel/position/longitude")
        alt = client.getDREF("sim/flightmodel/position/elevation")
        hdg = client.getDREF("sim/flightmodel/position/psi")
        spd = client.getDREF("sim/flightmodel/position/groundspeed")

        # --- Print or forward to BlueSky / network ---
        arc_label, reason = arc_classifier.air_risk(lat[0], lon[0], alt[0])
        print(f"{lat[0]:.6f}, {lon[0]:.6f}, {alt[0]:.1f} m, {hdg[0]:.1f}°, {spd[0]:.1f} m/s, {arc_label} ({reason['rule']})",
              end='\r', flush=True)

        # --- Keep the loop period constant ---
        time.sleep(PERIOD)

except KeyboardInterrupt:
    print("\nStopped by user.")
finally:
    client.close()
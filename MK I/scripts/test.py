# Script to read the output of an attached BME680 and trigger different relays depending on certain conditions.
# Max Young 4/24/24

import bme680
import time

sensor = bme680.BME680()
channel = 21

try:
    sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
except (RuntimeError, IOError):
    sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)
except ():
    print("Sensor not detected at primary for secondary address!")


# Obtain readings from sensors
sensor.set_humidity_oversample(bme680.OS_2X)
sensor.set_pressure_oversample(bme680.OS_4X)
sensor.set_temperature_oversample(bme680.OS_8X)
sensor.set_filter(bme680.FILTER_SIZE_3)
sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)

sensor.set_gas_heater_temperature(320)
sensor.set_gas_heater_duration(150)
sensor.select_gas_heater_profile(0)

# Get current time and instantiate a start time for tracking.
start_time = time.time()
curr_time = time.time()
# Time to run sensor burn-in
burn_in_time = 300
burn_in_data = []

try:
    while curr_time - start_time < burn_in_time:
        curr_time = time.time()
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            burn_in_data.append(gas)
            print("Gas: {0} Ohms".format(gas))
            time.sleep(1)

    gas_baseline = sum(burn_in_data[-50:]) / 50.0

    # Set the humidity baseline to 40%, an optimal indoor humidity.
    hum_baseline = 40.0

    # This sets the balance between humidity and gas reading in the
    # calculation of air_quality_score (25:75, humidity:gas)
    hum_weighting = 0.25

    while True:
        if sensor.get_sensor_data() and sensor.data.heat_stable:
            gas = sensor.data.gas_resistance
            gas_offset = gas_baseline - gas

            hum = sensor.data.humidity
            hum_offset = hum - hum_baseline

            # Calculate hum_score as the distance from the hum_baseline.
            if hum_offset > 0:
                hum_score = 100 - hum_baseline - hum_offset
                hum_score /= 100 - hum_baseline
                hum_score *= hum_weighting * 100

            else:
                hum_score = hum_baseline + hum_offset
                hum_score /= hum_baseline
                hum_score *= hum_weighting * 100

            # Calculate gas_score as the distance from the gas_baseline.
            if gas_offset > 0:
                gas_score = gas / gas_baseline
                gas_score *= 100 - (hum_weighting * 100)

            else:
                gas_score = 100 - (hum_weighting * 100)

            # Calculate air_quality_score.
            air_quality_score = hum_score + gas_score

            print(
                "Gas: {0:.2f} Ohms,humidity: {1:.2f} %RH,air quality: {2:.2f}".format(
                    gas, hum, air_quality_score
                )
            )

            time.sleep(1)

except KeyboardInterrupt:
    pass

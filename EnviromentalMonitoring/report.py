from influxdb import InfluxDBClient
from datetime import datetime, timedelta, timezone
from collections import Counter
import pytz



def create_report(delta):
        
    # Setting up a database connection
    client = InfluxDBClient(
        host='ec2-13-60-226-124.eu-north-1.compute.amazonaws.com',
        port=8086,
        database='mydb'
    )

    print("📡 Connected to InfluxDB")

    italy_tz = pytz.timezone('Europe/Rome')
    now = datetime.now(italy_tz)

    
    since = now - delta
    print(f"📅 Generating report since {since.isoformat()}")

    # ---------------------
    # Data collection
    # ---------------------
    def get_total_duration(measurement):
        query = f'SELECT sum("duration") FROM "{measurement}" WHERE time > \'{since.isoformat()}\''
        result = client.query(query)
        for point in result.get_points():
            return point.get('sum', 0.0)
        return 0.0

    light_duration = get_total_duration("ActLightTime")
    fan_duration = get_total_duration("ActTempTime")
    total_duration = light_duration + fan_duration

    lightWattage = 10  # Hypothetical wattage for light
    fanWattage = 50  # Hypothetical wattage for fan

    total_kwh = (lightWattage+fanWattage)*(total_duration / 3600.0)  # 1 kW = 3600 sec hypothetical

    # ---------------------
    # Calculate energy cost
    # ---------------------
    COST_PER_KWH = 0.2  # Euros per second
    total_cost =  total_kwh * COST_PER_KWH


    # ---------------------
    # Temperatures and lighting
    # ---------------------
    def get_max_min(measurement, field):
        query = f'SELECT max("{field}"), min("{field}") FROM "{measurement}" WHERE time > \'{since.isoformat()}\''
        result = client.query(query)
        for point in result.get_points():
            return point.get('max'), point.get('min')
        return None, None

    max_temp, min_temp = get_max_min("Temperatura", "temperature")
    max_lux, min_lux = get_max_min("Luminosità", "brightness")

    # ---------------------
    # Activities
    # ---------------------
    query = f'SELECT "activity" FROM "Activities" WHERE time > \'{since.isoformat()}\''
    result = client.query(query)
    activity_list = [point['activity'] for point in result.get_points()]
    activity_counter = Counter(activity_list)

    most_common = activity_counter.most_common(1)[0][0] if activity_counter else "N/A"
    least_common = activity_counter.most_common()[-1][0] if activity_counter else "N/A"
    sitting_count = activity_counter.get("sitting", 0)

    # ---------------------
    # Generate report
    # ---------------------
    report_lines = [
        "Report\n",
        f"Starting from: {since.strftime('%B %d, %Y %H:%M:%S')}",
        "1. Total Energy Usage",
        f"The total energy consumption was {total_kwh:.2f} kWh",
        "",
        "2. Energy Cost",
        f"   Total energy cost: €{total_cost:.4f}",
        "",
        "3. Peak Temperature & Peak Luminosity",
        f"   Max Temperature: {max_temp if max_temp is not None else 'N/A'} °C",
        f"   Max Brightness: {max_lux if max_lux is not None else 'N/A'}",
        "",
        "4. Min Temperature & Min Luminosity",
        f"   Min Temperature: {min_temp if min_temp is not None else 'N/A'} °C",
        f"   Min Brightness: {min_lux if min_lux is not None else 'N/A'}",
        "",
        "5. Activities Performed",
        f"   {', '.join(sorted(set(activity_list))) if activity_list else 'No activity data available.'}",
        "",
        "6. Most Performed Activity",
        f"   {most_common}",
        "",
        "7. Least Performed Activity",
        f"   {least_common}",
        "",
        "8. Sitting Time",
        f"   Seconds of sitting detected: {sitting_count}",
        "",
        "Prepared by: Ibrahim & Alessandro",
        f"Date: {now.strftime('%B %d, %Y %H:%M:%S')}"
    ]

    return report_lines

import urllib.request
import json
import requests
from socket import *
import time
from datetime import datetime

# Function to convert Celsius to Fahrenheit
def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

# Function to convert meters per second to miles per hour
def mps_to_mph(mps):
    return mps * 2.23694  # 1 m/s is approximately 2.23694 mph

def format_obs_time(obs_time_utc):
    # Convert string to datetime object from ODOT referenced time.
    #obs_time = datetime.strptime(obs_time_utc, "%Y-%m-%dT%H:%M:%S.%fZ")
    #formatted_obs_time = obs_time.strftime("%H%M%S")
    
    #Use system time
    utc_now = datetime.utcnow()

    # Format as desired (remove colons and 'Z')
    formatted_obs_time = utc_now.strftime("%H%M%S") #obs_time.strftime("%H%M%S")
    
    return formatted_obs_time
    
def inHg_to_mbar(pressure_inHg):
    return pressure_inHg * 33.8639
    
def aprs(formatted_time, wind_direction, wind_speed, temp, humidity, pressure, wind_gust):

    if humidity == 100:
        humidity = '00'

    # APRS-IS login info
    serverHost = 'rotate.aprs2.net'
    serverPort = 14580
    aprsUser = 'CALLSIGN'
    aprsPass = '000000'

    lat = '4610.25N'
    lon = '12326.37W'
    comment = 'ODOT WX - Location Name - CALLSIGN'

    # APRS packet
    callsign = 'CALLSIGN'
    btext = '@{}z{}/{}_{:03d}/{:03d}g{:03d}t{:03d}h{}b{:05d}{}'.format(formatted_time, lat, lon, int(wind_direction), int(wind_speed), int(wind_gust), int(temp), humidity, pressure, comment)
    print("@{}z{}/{}_{:03d}/{:03d}g{:03d}t{:03d}h{}b{:05d}{}".format(formatted_time, lat, lon, int(wind_direction), int(wind_speed), int(wind_gust), int(temp), humidity, pressure, comment))

    # create socket & connect to server
    sSock = socket(AF_INET, SOCK_STREAM)
    sSock.connect((serverHost, serverPort))
    # logon
    sSock.send(('user %s pass %s vers ODOTWX \n' % (aprsUser, aprsPass)).encode())
    sSock.send(('%s>APRS:%s\n' % (callsign, btext)).encode())

    sSock.shutdown(0)
    sSock.close()

try:
    url = "http://api.odot.state.or.us/tripcheck/v2/Rwis/Status?StationId=STATION_ID" #v2 WX stations

    headers = {
        'Cache-Control': 'no-cache',
        'Ocp-Apim-Subscription-Key': 'API_KEY'
    }

    req = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(req) as response:
        # Read the response content and decode it as UTF-8
        response_content = response.read().decode('utf-8')

        # Load the JSON response
        response_data = json.loads(response_content)

        # Print the entire formatted JSON response
        formatted_response = json.dumps(response_data, indent=4)
        print("Formatted Response content:")
        print(formatted_response)

        # Organization Information
        org_info = response_data["organization-information"]
        print("\nOrganization Information:")
        print("Last Update Time: {}".format(org_info['last-update-time']))
        print("Organization ID: {}".format(org_info['organization-id']))
        print("Organization Name: {}\n".format(org_info['organization-name']))

        # Weather Station Information
        weather_station = response_data["WeatherStations"][0]
        road_weather = weather_station["RoadWeather"]
        surface_condition = weather_station["SurfaceCondition"]
        humidity = road_weather.get('relative-humidity', 0)

        # Road Weather Information
        print("Road Weather Information:")
        print("Relative Humidity: {}%".format(humidity))
        print("Avg Wind Gust Speed: {:.0f} mph".format(mps_to_mph(road_weather['avg-wind-gust-speed'] / 10)))
        print("Avg Wind Speed: {:.0f} mph".format(mps_to_mph(road_weather['avg-wind-speed'] / 10)))
        print("Avg Wind Direction: {} Deg".format(road_weather['avg-wind-direction']))

        # Calculate Fahrenheit values for air temperature and dewpoint temperature
        air_temp_celsius = road_weather.get('air-temperature', 0) / 10
        dewpoint_temp_celsius = road_weather.get('dewpoint-temp', 0) / 10

        air_temp_fahrenheit = celsius_to_fahrenheit(air_temp_celsius)
        dewpoint_temp_fahrenheit = celsius_to_fahrenheit(dewpoint_temp_celsius)
        atmospheric_pressure = road_weather.get('atmospheric-pressure', 0) #creates 0 when not found. modify all to this.

        print("Air Temperature (C): {:.0f}C".format(air_temp_celsius))
        print("Dewpoint Temperature (C): {:.0f}C".format(dewpoint_temp_celsius))
        print("Air Temperature (F): {:.0f}F".format(air_temp_fahrenheit))
        print("Dewpoint Temperature (F): {:.0f}F".format(dewpoint_temp_fahrenheit))
        print("Pressure: {:.0f}mbar".format(atmospheric_pressure))


        # Surface Condition Information
        print("\nSurface Condition Information:")
        surface_temps = surface_condition["surface-temperatures"]
        for sensor in surface_temps:
            print("Sensor {} Surface Temperature: {:.0f}C".format(sensor['sensor-id'], sensor['surface-temperature']))
        #print("Water Depth: {}".format(surface_condition['water-depth']))
        print("Surface Freeze Point: {:.0f}C".format(surface_condition['surface-freeze-point']))
        print("Surface Salinity: {}".format(surface_condition['surface-salinity']))
        
        formatted_time = format_obs_time(org_info['last-update-time'])
                
        aprs(formatted_time, road_weather['avg-wind-direction'], mps_to_mph(road_weather['avg-wind-speed'] / 10), air_temp_fahrenheit, humidity, atmospheric_pressure, mps_to_mph(road_weather['avg-wind-gust-speed'] / 10))

except Exception as e:
    print("An error occurred:", str(e))

import datetime
import time
import os
import paho.mqtt.client as mqtt
from timeseries_get import TemperatureSimulator
import json

sensor_topic_status = os.getenv("SENSOR_TOPIC_STATUS")
sensor_topic_data = os.getenv("SENSOR_TOPIC_DATA")
mqtt_host = os.getenv("MQTT_HOST")
heatpump_status = 0

def heatpump_status_change(c, userdata, message):
    global heatpump_status
    v = json.loads(message.payload.decode("utf-8"))
    try:
        heatpump_status = int(v["status"])
        print(message.payload.decode("utf-8"))
    except:
        pass
client = mqtt.Client()
client.connect(mqtt_host, 1883, 60)
client.on_message = heatpump_status_change
client.subscribe(sensor_topic_status)
client.loop_start()
ts_gen = TemperatureSimulator(datetime.datetime.now())
while True:
    reading = ts_gen.get_temperature(datetime.datetime.now(), heatpump_status)
    to_send = json.dumps({"timestamp": reading[0].isoformat(), "value": reading[1]})
    client.publish(sensor_topic_data, to_send)
    time.sleep(1)





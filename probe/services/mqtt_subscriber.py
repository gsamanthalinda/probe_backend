import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import session
from probe.services.sensor_reading import SensorReadingService
from probe.schemas.sensor_reading import SensorReadingCreate

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mqtt-subscriber")

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "probe/telemetry/+")
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_KEEPALIVE = int(os.getenv("MQTT_KEEPALIVE", 60))

db_worker_pool = ThreadPoolExecutor(max_workers=5)


def process_and_save_reading(topic: str, payload_str: str):
    try:
        data = json.loads(payload_str)
        device_id = data.get("device_id")
        battery_id = data.get("battery_id")
        temp = float(data.get("temp", 0.0))
        current = float(data.get("current", 0.0))
        v_rest = float(data.get("v_rest", 0.0))
        v_load = float(data.get("v_load", 0.0))

        if not device_id or not battery_id:
            logger.warning("Missing identity keys in payload from topic %s", topic)
            return

        db = session()
        try:
            reading_data = SensorReadingCreate(
                device_id=device_id,
                battery_id=battery_id,
                temp=temp,
                current=current,
                v_rest=v_rest,
                v_load=v_load,
            )
            reading = SensorReadingService.create_sensor_reading(db, reading_data)
            logger.info(
                "Saved data -> ID: %s | channel=%s | SoH=%.1f%% | cat=%s",
                reading.sensor_reading_id,
                topic.split("/")[-1],
                reading.state_of_health,
                reading.category,
            )
        except Exception as e:
            logger.error("DB Write Exception on channel topic %s: %s", topic, e)
        finally:
            db.close()

    except json.JSONDecodeError:
        logger.error("Corrupt or invalid payload array skipped on %s", topic)
    except Exception as e:
        logger.error("Unexpected worker loop exception on %s: %s", topic, e)


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("Connected securely to MQTT broker %s:%d", MQTT_BROKER, MQTT_PORT)
        client.subscribe(MQTT_TOPIC, qos=1)
        logger.info("Active subscription link established: %s", MQTT_TOPIC)
    else:
        logger.error("MQTT subscription sequence rejected with error code %d", rc)


def on_disconnect(client, userdata, rc, properties=None):
    logger.warning("Broker pipe dropped (rc=%d). Initializing automatic fallback loop...", rc)


def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode("utf-8")
        db_worker_pool.submit(process_and_save_reading, msg.topic, payload_str)
    except Exception as e:
        logger.error("Failed to forward telemetry frame packet: %s", e)


def main():
    callback_api_version = mqtt.CallbackAPIVersion.VERSION2
    client = mqtt.Client(
        callback_api_version=callback_api_version,
        client_id="probe-backend-subscriber",
        clean_session=False
    )
    
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    if MQTT_USER and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    logger.info("Attempting handshake connection with HiveMQ endpoint %s:%d", MQTT_BROKER, MQTT_PORT)
    client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)

    logger.info("Subscriber loop online.")
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Graceful execution shutdown initialized by terminal command.")
    finally:
        client.disconnect()
        db_worker_pool.shutdown(wait=True)
        sys.exit(0)


if __name__ == "__main__":
    main()

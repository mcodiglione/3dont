import boto3
import json
import os
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import os
from pathlib import Path
import datetime
import time
import csv

################################################ TODO
# TODO
#DA SISTEMARE PER GESTIONE DI SENSORI MULTI-PROPRIETA E PER ELASTICITà SULLE KEY CON CUI ACCEDERE AL JSON DI OUTPUT:
#- [ ] sistemare di modo da gestire più prop in tutte le mie funzioni
#- [ ] in fase di setup del sensore chiedere all’utente i nomi delle prop da misurare:
#    - [ ] nomi nell’ontologia
#    - [ ] nomi come chiavi nel json
#- [ ] storare i nomi delle chiavi nel dict di config associati alle varie prop della ont con una struttura a dizionari innestati
################################################ TODO

# ---------- CONFIGURATION ----------

IOT_REGION = "eu-west-1"
IOT_POLICY_NAME = "AllowAllIoTPolicy"
MQTT_TOPIC = "sensors/+/data"


# ---------- AWS LOCAL CREDENTIAL SETTING ---------
# ONLY ONCE PER MACHINE
def set_aws_credentials(
    access_key_id: str,
    secret_access_key: str,
    region: str = "eu-west-1",
    profile: str = "default",
):
    """
    Saves AWS credentials to ~/.aws/credentials and ~/.aws/config

    Args:
        access_key_id (str): Your AWS Access Key ID
        secret_access_key (str): Your AWS Secret Access Key
        region (str): Default AWS region (e.g., 'eu-west-1')
        profile (str): AWS profile name (default is 'default')
    """

    aws_dir = Path.home() / ".aws"
    credentials_path = aws_dir / "credentials"
    config_path = aws_dir / "config"

    aws_dir.mkdir(exist_ok=True)

    # Write credentials
    credentials_content = f"""[{profile}]
aws_access_key_id = {access_key_id}
aws_secret_access_key = {secret_access_key}
"""
    with open(credentials_path, "a") as cred_file:
        cred_file.write(credentials_content)

    # Write config
    config_content = f"""[profile {profile}]
region = {region}
output = json
"""
    with open(config_path, "a") as cfg_file:
        cfg_file.write(config_content)

    print(f"✅ AWS credentials saved for profile '{profile}' at {aws_dir}")


# ---------- UTILITY FUNCTIONS ----------


def _create_iot_client():
    return boto3.client("iot", region_name=IOT_REGION)


def _attach_policy(iot, cert_arn):
    try:
        iot.create_policy(
            policyName=IOT_POLICY_NAME,
            policyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {"Effect": "Allow", "Action": "iot:*", "Resource": "*"}
                    ],
                }
            ),
        )
    except iot.exceptions.ResourceAlreadyExistsException:
        pass
    iot.attach_policy(policyName=IOT_POLICY_NAME, target=cert_arn)


# ---------- MAIN FUNCTIONs 1: ADD SENSOR ----------


def setup_sensor_connection(SensorMetadata):
    iot = _create_iot_client()

    print(f"🛠 Creating IoT Thing '{SensorMetadata.name}'...")
    try:
        iot.create_thing(thingName=SensorMetadata.name)
        print(f"✅ Thing created: {SensorMetadata.name}")
    except iot.exceptions.ResourceAlreadyExistsException:
        print(f"ℹ️ Thing '{SensorMetadata.name}' already exists")

    print("🔐 Registering provided certificate...")
    cert_response = iot.register_certificate_without_ca(
        certificatePem=SensorMetadata.CertBundle.cert_pem, status="ACTIVE"
    )
    cert_arn = cert_response["certificateArn"]
    cert_id = cert_response["certificateId"]
    print(f"🔐 Certificate registered: {cert_arn}")

    print("🔗 Attaching certificate to Thing...")
    iot.attach_thing_principal(thingName=SensorMetadata.name, principal=cert_arn)

    print("🛡️ Attaching policy...")
    _attach_policy(iot, cert_arn)

    # Get AWS endpoint
    endpoint = iot.describe_endpoint(endpointType="iot:Data-ATS")["endpointAddress"]

    sensor_dir = Path(f"sensors/")
    sensor_dir.mkdir(exist_ok=True)

    # save cert file
    cert_dir = Path(f"certs/{SensorMetadata.name}")
    cert_dir.mkdir(parents=True, exist_ok=True)

    # Save the cert files
    with open(cert_dir / "cert.pem", "w") as f:
        f.write(SensorMetadata.CertBundle.cert_pem)
    with open(cert_dir / "private.key", "w") as f:
        f.write(SensorMetadata.CertBundle.private_key)
    with open(cert_dir / "AmazonRootCA1.pem", "w") as f:
        f.write(SensorMetadata.CertBundle.AmazonRootCA1_pem)

    # create historic file
    historic_dir = Path(f"historics/")
    historic_dir.mkdir(exist_ok=True)
    historic_path = os.path.join(historic_dir, f"{SensorMetadata.name}.csv")

    with open(historic_path, newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["value", "time"])
        writer.writeheader()

    # Save the config file
    config = {
        "endpoint": endpoint,
        "cert_path": os.path.join(cert_dir, "cert.pem"),
        "key_path": os.path.join(cert_dir, "private.key"),
        "root_ca_path": os.path.join(cert_dir, "AmazonRootCA1.pem"),
        "client_id": SensorMetadata.CertBundle.client_id,
        "topic": SensorMetadata.CertBundle.mqtttopic,
        "sensor_name": SensorMetadata.name,
        "description": SensorMetadata.description,
        "property": SensorMetadata.property,
        "DescribedObject": SensorMetadata.DescribedObject,
        "encoding": SensorMetadata.encoding,
        "historic_path": historic_path,
    }
    with open(sensor_dir / f"{SensorMetadata.name}.json", "w") as f:
        json.dump(config, f, indent=2)

    print(f"📦 Setup complete. Config and certs saved in: {sensor_dir.resolve()}")
    return


# ---------- MAIN FUNCTIONs 2: RETRIEVE DATA ----------


def update_historic(sensor_name: str, value, time):
    historic_path = Path(f"historics/{sensor_name}.csv")
    historic_path.parent.mkdir(
        parents=True, exist_ok=True
    )  # Ensure 'historics/' directory exists
    write_header = not historic_path.exists()
    with historic_path.open(mode="a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["value", "time"])
        if write_header:
            writer.writeheader()
        writer.writerow({"value": value, "time": time})
    return


def get_sensor_data_from_name(sensor_name: str):

    config_path = Path(f"sensors/{sensor_name}.json")
    # Load configuration
    with open(config_path, "r") as f:
        cfg = json.load(f)

    client_id = cfg["client_id"]
    endpoint = cfg["endpoint"]
    topic = cfg["topic"]
    cert_path = cfg["cert_path"]
    key_path = cfg["key_path"]
    root_ca_path = cfg["root_ca_path"]

    message_dict = {
        "Property": cfg["property"],
        "DescribedObject": cfg["DescribedObject"],
        "SensorName": cfg["sensor_name"],
    }

    # Initialize MQTT client
    mqtt_client = AWSIoTMQTTClient(client_id)
    mqtt_client.configureEndpoint(endpoint, 8883)
    mqtt_client.configureCredentials(root_ca_path, key_path, cert_path)

    # Optional configurations
    mqtt_client.configureOfflinePublishQueueing(0)
    mqtt_client.configureDrainingFrequency(0)
    mqtt_client.configureConnectDisconnectTimeout(10)
    mqtt_client.configureMQTTOperationTimeout(5)

    # Connect and subscribe
    mqtt_client.connect()
    print(f"📡 Connected to AWS IoT Core endpoint: {endpoint}")
    print(f"📥 Subscribing to topic: {topic}")

    def handle_message(client, userdata, message):
        try:
            decoded = json.loads(message.payload.decode("utf-8"))
            message_dict["Value"] = decoded["value"]
            message_dict["AcquisitionTime"] = decoded["timestamp"]
        except Exception as e:
            print(f"❌ Failed to decode or parse message: {e}")

    mqtt_client.subscribe(topic, 1, handle_message)
    print(f"📡 Waiting for message on topic '{topic}'...")

    for _ in range(2000):
        if message_dict["Value"] is not None:
            break
        time.sleep(0.1)

    mqtt_client.disconnect()

    message_dict["ImportTime"] = (
        datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    )
    update_historic(sensor_name, message_dict["Value"], message_dict["AcquisitionTime"])

    return message_dict


def get_sensors_data_from_object(Object_name: str):
    sensors_dir = Path(f"sensors/")
    sensor_list = os.listdir(sensors_dir)
    obj_list = []
    for sensor_config in sensor_list:
        with open(sensor_config, "r") as f:
            cfg = json.load(f)
            object_name = cfg["DescribedObject"]
            sensor_name = cfg["sensor_name"]
        if object_name == Object_name:
            obj_list.append(sensor_name)
    messages_dict = {
        sensor_name: message_dict
        for (sensor_name, message_dict) in [
            (sensor_name, get_sensor_data_from_name(sensor_name))
            for sensor_name in obj_list
        ]
    }
    return messages_dict


def get_sensors_data_from_property(Property_name: str):
    sensors_dir = Path(f"sensors/")
    sensor_list = os.listdir(sensors_dir)
    prop_list = []
    for sensor_config in sensor_list:
        with open(sensor_config, "r") as f:
            cfg = json.load(f)
            prop_name = cfg["property"]
            sensor_name = cfg["sensor_name"]
        if prop_name == Property_name:
            prop_list.append(sensor_name)
    messages_dict = {
        sensor_name: message_dict
        for (sensor_name, message_dict) in [
            (sensor_name, get_sensor_data_from_name(sensor_name))
            for sensor_name in prop_list
        ]
    }
    return messages_dict

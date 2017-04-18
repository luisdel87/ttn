#! /usr/bin/env python
import json
import logs
import base64
import requests
import yaml
import traceback
import sys


def map_notification_from_ttn(json_from_ttn, notification_uuid):
    logs.logger.debug("Received TTN Json [ %s ] UUID [ %s ]" % (json.dumps(json_from_ttn), notification_uuid))
    entity_data = {}
    entity_data["entity_name"] = json_from_ttn["dev_id"]
    entity_data["app_id"] = json_from_ttn["app_id"]
    entity_data["downlink_url"] = json_from_ttn["downlink_url"]
    entity_data["attributes"], entity_data["cb_endpoint"], entity_data["fiware_service"], entity_data["fiware_service_path"] \
        = apply_application_mapping(json_from_ttn["app_id"], base64.b64decode(json_from_ttn["payload_raw"]),notification_uuid)

    entity_data["timestamp"] = json_from_ttn["metadata"]["time"]

    logs.logger.info("Mapped device from  TTN for entity [ %s ] with timestamp [ %s ] UUID [ %s ] "
                     % (entity_data["entity_name"], entity_data["timestamp"], notification_uuid))
    logs.logger.debug("Entity mapped as [ %s ]  UUID [ %s ]" % (entity_data, notification_uuid))
    return entity_data


def payload_for_context_broker(entity_data, notification_uuid):
    attributes = []

    try:
        json_attributes = entity_data["attributes"]

        for key in json_attributes:
            attributes.append({
                "name": key,
                "type": "float",
                "value": json_attributes[key]
            })

        cb_payload = {
            "attributes": attributes
        }
        logs.logger.debug("Entity payload [ %s ] for entity [ %s ]  UUID [ %s ]"
                          % (cb_payload, entity_data["entity_name"], notification_uuid))
        return cb_payload

    except:

        logs.logger.error("Malformed Json")


def send_to_context_broker(entity_data, cb_payload, notification_uuid):

    url = "%s/v1/contextEntities/type/device/id/%s" % (entity_data["cb_endpoint"], entity_data["entity_name"])

    headers = {
        'content-type': "application/json",
        'accept': "application/json",
        'fiware-service': entity_data["fiware_service"],
        'fiware-servicepath': entity_data["fiware_service_path"]
    }
    logs.logger.debug("Headers [ %s ] UUID [ %s ]"%(headers, notification_uuid))
    cb_response = requests.request("POST", url, data=json.dumps(cb_payload), headers=headers)
    # print cb_response.text
    logs.logger.debug("Context Broker response [ %s ] for UUID [ %s ]" % (cb_response.text, notification_uuid))
    try:
        cb_status_code = json.loads(cb_response.text)["contextResponses"][0]["statusCode"]["code"]
        logs.logger.info("Context Broker response [ %s ]  UUID [ %s ]" % (cb_status_code, notification_uuid))
        return (cb_status_code)

    except:
        logs.logger.error("Context Broker response [ %s ]  UUID [ %s ]" % (cb_response.text, notification_uuid))
        return 500


def apply_application_mapping(app_id, received_attributes, notification_uuid):
    received_attributes = json.loads(received_attributes)
    try:
        with open("./TTN_apps/%s.yaml" % app_id, 'r') as config_app:
            configuration = yaml.load(config_app)
        config_app.close()
        cb_endpoint = configuration[0]["app_configuration"]["contextbroker_endpoint"]
        fiware_service = configuration[0]["app_configuration"]["fiware_service"]
        fiware_service_path = configuration[0]["app_configuration"]["fiware_service_path"]
    except:
        logs.logger.error(
            "Fail getting configuration file. Check yaml file linked to service UUID [ %s ]" % notification_uuid)
    try:
        for attribute in received_attributes.keys():
            if attribute in configuration[1]["mapping"].keys() :
                received_attributes[configuration[1]["mapping"]["%s" % attribute]] = received_attributes.pop(attribute)
                logs.logger.info(
                    "Attributes mapped to [ %s ] UUID [ %s ]" % (received_attributes.keys(), notification_uuid))
            else:
                logs.logger.warning(
                    "Mapping not found for  attribute [ %s ] for UUID [ %s ]" % (attribute, notification_uuid))

    except:
        logs.logger.error("Error mapping the attributes. Check yaml file linked to service UUID [ %s ] [ %s ]" % (
        traceback.print_exc(), notification_uuid))

    return received_attributes, cb_endpoint,fiware_service,fiware_service_path

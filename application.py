#! /usr/bin/env python
#########################################################################
#
# Author:
# Luis Peña
# __________________
#
#  Bristol is Open
#  All Rights Reserved.
#
# NOTICE:  All information contained herein is, and remains
# the property of ABristol is Open and its suppliers,
# if any.  The intellectual and technical concepts contained
# herein are proprietary to Bristol is Open
# and its suppliers and may be covered by U.K. and Foreign Patents,
# patents in process, and are protected by trade secret or copyright law.
# Dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from Bristol is Open.
#

from flask import Flask, request, Response
import logs
import json
import uuid
import processTtnNotification


logs.config_log()
application = Flask(__name__)


@application.route('/notify/ttn', methods=['POST'])
def the_things_network_handler():
    notification_uuid=uuid.uuid1()
    logs.logger.info("Notication from TTN UUID [ %s ]"%(notification_uuid))
    json_from_ttn = request.get_json()
    entity_data=processTtnNotification.map_notification_from_ttn(json_from_ttn, notification_uuid)
    cb_payload = processTtnNotification.payload_for_context_broker(entity_data, notification_uuid)
    cb_code=processTtnNotification.send_to_context_broker(entity_data, cb_payload, notification_uuid)
    return Response(json.dumps("Processed"),int(cb_code),content_type='application/json')


if __name__ == '__main__':
    application.run()
#!/usr/bin/env python

from __future__ import print_function
import pywbem
import datetime
import boto.ses
import sys
import json
from slacker import Slacker

sns_conn = boto.ses.connect_to_region('<AWS_REGION>')
now = datetime.datetime.today().strftime('%Y-%m-%d')
esxi_host = '<ESXI_HOST_URL>'
esxi_user = '<ESXI_USER>'
esxi_pass = '<ESXI_PASSWORD>'
slack_token = '<SLACK_API_TOKEN>'
slack = Slacker(slack_token)
slack_channel = '<SLACK_CHANNEL>'
header = "Hi!\n\nHere is storage status from ESXi host.\n\n"

def send_mail(subject, email):
  sns_conn.send_email('<FROM_EMAIL>', subject, email, ['TO_EMAIL'])

try:
  conn = pywbem.WBEMConnection(esxi_host, (esxi_user, esxi_pass), no_verification=True)
  conntest = conn.EnumerateInstances('CIM_Chassis')
except:
  subject = "There was a problem getting CIM data from ESXi host"
  email = "Couldn't get CMI info, sorry."
  send_mail(subject, email)
  slack.chat.post_message(slack_channel, subject)
else:
  virtual_storage = conn.EnumerateInstances('VMware_StorageVolume')
  physical_storage = conn.EnumerateInstances('VMware_StorageExtent')

  mail_body = []

  for disk in virtual_storage:
    element_name = disk['ElementName']
    if disk['HealthState'] == 5:
      health_status = "  Healthy (%s)" % disk['HealthState']
      raid_healthy = True
    else:
      health_status = "  PROBLEM (%s)" % disk['HealthState']
      raid_healthy = False
    mail_body.extend([element_name + health_status])

  for disk in physical_storage:
    element_name = disk['ElementName']
    if disk['HealthState'] == 5:
      health_status = "  Healthy (%s)" % disk['HealthState']
      hdd_healthy = True
    else:
      health_status = "  PROBLEM (%s)" % disk['HealthState']
      hdd_healthy = False
      break
    mail_body.extend([element_name + health_status])

  if (raid_healthy and hdd_healthy):
    subject = 'ESXi storage is HEALTHY  %s' % now
    slack.chat.post_message(slack_channel, subject)
  else:
    subject = 'ESXi storage is NOT HEALTHY!!  %s' % now
    slack.chat.post_message(slack_channel, subject)
    email = header + '\n'.join(mail_body)
    send_mail(subject, email)

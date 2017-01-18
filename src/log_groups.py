#!/usr/bin/env python
import re
import logging
import boto3
from functools import partial
import sys, os
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')
sys.path.append(vendor_dir)
from cfn_lambda_handler import Handler

# set handler as the entry point for Lambda
handler = Handler()

# Configure logging
log = logging.getLogger()
log.setLevel(logging.INFO)

# Logs client
client = boto3.client('logs')

# Handles paginated responses
def paginated_response(func, result_key, next_token=None):
  args=dict()
  if next_token:
      args['NextToken'] = next_token
  response = func(**args)
  result = response.get(result_key)
  next_token = response.get('NextToken')
  if not next_token:
     return result
  return result + paginated_response(func, result_key, next_token)

def get_or_create_log_group(name):
  arn = log_group_arn(name)
  if not arn:
    client.create_log_group(logGroupName=name)
    arn = log_group_arn(name)
  return arn

def log_group_arn(name):
  func = partial(client.describe_log_groups,logGroupNamePrefix=name)
  log_groups = paginated_response(func, 'logGroups')
  return next((log_group.get('arn') for log_group in log_groups if log_group.get('logGroupName') == name),None)

def validate_input(name, retention):
  if not name:
    raise Exception("You must specify a log group name")
  if not re.match("^[a-zA-Z0-9_./-]*$", name):
    raise Exception("Invalid log group name.  Allowed characters are a-z, A-Z, 0-9, '_' (underscore), '-' (hyphen), '/' (forward slash), and '.'")
  if not retention.isdigit() or int(retention) not in [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]:
    raise Exception("Invalid retention period.  Valid values are 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653 days")

def update_subscription(name, subscription, existing_subscription):
  filter_name = subscription.get('FilterName') or 'default'
  filter_pattern = subscription.get('FilterPattern') or ''
  destination_arn = subscription.get('DestinationArn')
  if not subscription.get('DestinationArn'):
    raise Exception("Invalid Subscription configuration.  You must specify the DestinationArn property.")
  if not existing_subscription:
    # Create new subscription
    client.put_subscription_filter(
      logGroupName=name,
      filterName=filter_name,
      filterPattern=filter_pattern,
      destinationArn=destination_arn
    )
    return
  existing_filter_name = existing_subscription[0].get('filterName')
  update = (
    existing_filter_name != filter_name or 
    existing_subscription[0].get('filterPattern') != filter_pattern or 
    existing_subscription[0].get('destinationArn') != destination_arn 
  )
  if update:
    # Delete existing subcription and create new subscription
    client.delete_subscription_filter(logGroupName=name, filterName=existing_filter_name)
    client.put_subscription_filter(
      logGroupName=name,
      filterName=filter_name,
      filterPattern=filter_pattern,
      destinationArn=destination_arn
    )

def create_or_update_subscription(name, subscription):
  response = client.describe_subscription_filters(logGroupName=name)
  existing_subscription = response.get('subscriptionFilters')
  if not existing_subscription and not subscription:
    return
  if existing_subscription and not subscription:
    # Delete existing subscription
    client.delete_subscription_filter(logGroupName=name, filterName=existing_subscription[0].get('filterName'))
  else:
    # Update subscription
    update_subscription(name, subscription, existing_subscription)
  
# Event handlers
@handler.create
@handler.update
def handle(event, context):
  log.info('Received event %s' % str(event))

  # Get event properties
  resource_properties = event.get('ResourceProperties')
  name = resource_properties.get('Name')
  retention = resource_properties.get('Retention') or "30"
  destroy = (resource_properties.get('Destroy') or 'false').lower() == 'true'
  subscription = resource_properties.get('Subscription')
  validate_input(name, retention)

  # Get old properties for update requests
  old_resource_properties = event.get('OldResourceProperties') or dict()
  old_name = old_resource_properties.get('Name') or name
  
  # Create log group if required
  arn = get_or_create_log_group(name)

  # Set retention policy
  client.put_retention_policy(logGroupName=name, retentionInDays=int(retention))

  # Set subscription policy
  create_or_update_subscription(name, subscription)

  # Delete old log group if name changed
  if destroy and name != old_name:
    client.delete_log_group(logGroupName=old_name)

  return { "PhysicalResourceId": name, "Data": { "Arn": arn } }

@handler.delete
def handle_delete(event, context):
  log.info('Received event %s' % str(event))

  # Get event properties
  resource_properties = event.get('ResourceProperties')
  name = resource_properties.get('Name')
  destroy_value = resource_properties.get('Destroy') or 'false'
  destroy = destroy_value.lower() in ['true', 'yes']

  # Delete if retain property set to false or no
  if destroy and log_group_arn(name):
    client.delete_log_group(logGroupName=name)

  return { "PhysicalResourceId": event.get('PhysicalResourceId') }
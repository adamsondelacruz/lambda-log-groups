import pytest
import test_fixtures
from test_fixtures import context
from test_fixtures import log_groups
from test_fixtures import update_event

def test_update_no_existing(log_groups, update_event, context):
  return_value = log_groups.client.describe_log_groups.return_value
  log_groups.client.describe_log_groups.side_effect = [{'logGroups': []},test_fixtures.DESCRIBE_LOG_GROUPS]
  response = log_groups.handle(update_event,context)
  assert log_groups.client.create_log_group.called
  log_groups.client.put_retention_policy.assert_called_with(logGroupName=test_fixtures.LOG_GROUP_NAME, retentionInDays=30)
  assert log_groups.client.describe_subscription_filters.called
  assert not log_groups.client.delete_subscription_filter.called
  assert response == { 
    'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME,
    'Data': { 'Arn': test_fixtures.FUNCTION_ARN }
  }

def test_update_retention(log_groups, update_event, context):
  update_event['ResourceProperties']['Retention'] = '7'
  response = log_groups.handle(update_event,context)
  assert not log_groups.client.create_log_group.called
  log_groups.client.put_retention_policy.assert_called_with(logGroupName=test_fixtures.LOG_GROUP_NAME, retentionInDays=7)
  assert log_groups.client.describe_subscription_filters.called
  assert not log_groups.client.delete_subscription_filter.called
  assert not log_groups.client.put_subscription_filter.called
  assert response == { 
    'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME,
    'Data': { 'Arn': test_fixtures.FUNCTION_ARN }
  }

def test_update_new_subscription(log_groups, update_event, context):
  update_event['ResourceProperties']['Subscription'] = {
    'FilterName': 'Default',
    'FilterPattern': '',
    'DestinationArn': test_fixtures.SUBSCRIPTION_ARN
  }
  response = log_groups.handle(update_event,context)
  assert not log_groups.client.create_log_group.called
  log_groups.client.put_retention_policy.assert_called_with(logGroupName=test_fixtures.LOG_GROUP_NAME, retentionInDays=30)
  assert log_groups.client.describe_subscription_filters.called
  assert not log_groups.client.delete_subscription_filter.called
  assert log_groups.client.put_subscription_filter.called
  assert response == { 
    'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME,
    'Data': { 'Arn': test_fixtures.FUNCTION_ARN }
  }

def test_update_existing_subscription(log_groups, update_event, context):
  update_event['ResourceProperties']['Subscription'] = {
    'FilterName': 'Default',
    'FilterPattern': '[filter]',
    'DestinationArn': test_fixtures.SUBSCRIPTION_ARN
  }
  log_groups.client.describe_subscription_filters.return_value = test_fixtures.DESCRIBE_SUBSCRIPTION_FILTERS
  response = log_groups.handle(update_event,context)
  assert not log_groups.client.create_log_group.called
  log_groups.client.put_retention_policy.assert_called_with(logGroupName=test_fixtures.LOG_GROUP_NAME, retentionInDays=30)
  assert log_groups.client.describe_subscription_filters.called
  assert log_groups.client.delete_subscription_filter.called
  assert log_groups.client.put_subscription_filter.called
  assert response == { 
    'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME,
    'Data': { 'Arn': test_fixtures.FUNCTION_ARN }
  }

def test_update_existing_subscription_no_changes(log_groups, update_event, context):
  update_event['ResourceProperties']['Subscription'] = {
    'FilterName': 'Default',
    'FilterPattern': '',
    'DestinationArn': test_fixtures.SUBSCRIPTION_ARN
  }
  log_groups.client.describe_subscription_filters.return_value = test_fixtures.DESCRIBE_SUBSCRIPTION_FILTERS
  response = log_groups.handle(update_event,context)
  assert not log_groups.client.create_log_group.called
  log_groups.client.put_retention_policy.assert_called_with(logGroupName=test_fixtures.LOG_GROUP_NAME, retentionInDays=30)
  assert log_groups.client.describe_subscription_filters.called
  assert not log_groups.client.delete_subscription_filter.called
  assert not log_groups.client.put_subscription_filter.called
  assert response == { 
    'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME,
    'Data': { 'Arn': test_fixtures.FUNCTION_ARN }
  }

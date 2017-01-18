import pytest
import test_fixtures
from test_fixtures import context
from test_fixtures import log_groups
from test_fixtures import create_event

def test_missing_name(log_groups, create_event, context):
  del create_event['ResourceProperties']['Name']
  with pytest.raises(Exception) as e:
    response = log_groups.handle(create_event,context)
  assert "You must specify a log group name" in str(e)

def test_invalid_name(log_groups, create_event, context):
  create_event['ResourceProperties']['Name'] = "my:log:group"
  with pytest.raises(Exception) as e:
    response = log_groups.handle(create_event,context)
  assert "Invalid log group name" in str(e)

def test_invalid_retention(log_groups, create_event, context):
  create_event['ResourceProperties']['Retention'] = '555'
  with pytest.raises(Exception) as e:
    response = log_groups.handle(create_event,context)
  assert "Invalid retention period" in str(e)

def test_invalid_subscription(log_groups, create_event, context):
  create_event['ResourceProperties']['Subscription'] = {
    'FilterName': 'Default',
    'FilterPattern': '',
  }
  with pytest.raises(Exception) as e:
    response = log_groups.handle(create_event,context)
  assert "Invalid Subscription configuration" in str(e)

def test_create_new_group(log_groups, create_event, context):
  return_value = log_groups.client.describe_log_groups.return_value
  log_groups.client.describe_log_groups.side_effect = [{'logGroups': []},test_fixtures.DESCRIBE_LOG_GROUPS]
  response = log_groups.handle(create_event,context)
  assert log_groups.client.create_log_group.called
  log_groups.client.put_retention_policy.assert_called_with(logGroupName=test_fixtures.LOG_GROUP_NAME, retentionInDays=30)
  assert log_groups.client.describe_subscription_filters.called
  assert not log_groups.client.delete_subscription_filter.called
  assert response == { 
    'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME,
    'Data': { 'Arn': test_fixtures.FUNCTION_ARN }
  }

def test_create_existing_group(log_groups, create_event, context):
  response = log_groups.handle(create_event,context)
  assert not log_groups.client.create_log_group.called
  log_groups.client.put_retention_policy.assert_called_with(logGroupName=test_fixtures.LOG_GROUP_NAME, retentionInDays=30)
  assert log_groups.client.describe_subscription_filters.called
  assert not log_groups.client.delete_subscription_filter.called
  assert response == { 
    'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME,
    'Data': { 'Arn': test_fixtures.FUNCTION_ARN }
  }

def test_create_with_subscription(log_groups, create_event, context):
  create_event['ResourceProperties']['Subscription'] = {
    'FilterName': 'Default',
    'FilterPattern': '',
    'DestinationArn': test_fixtures.SUBSCRIPTION_ARN
  }
  response = log_groups.handle(create_event,context)
  assert not log_groups.client.create_log_group.called
  log_groups.client.put_retention_policy.assert_called_with(logGroupName=test_fixtures.LOG_GROUP_NAME, retentionInDays=30)
  assert log_groups.client.describe_subscription_filters.called
  assert not log_groups.client.delete_subscription_filter.called
  assert log_groups.client.put_subscription_filter.called
  assert response == { 
    'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME,
    'Data': { 'Arn': test_fixtures.FUNCTION_ARN }
  }

def test_create_existing_group_subscription_with_new_subscription(log_groups, create_event, context):
  create_event['ResourceProperties']['Subscription'] = {
    'FilterName': 'Default',
    'FilterPattern': '[filter]',
    'DestinationArn': test_fixtures.SUBSCRIPTION_ARN
  }
  log_groups.client.describe_subscription_filters.return_value = test_fixtures.DESCRIBE_SUBSCRIPTION_FILTERS
  response = log_groups.handle(create_event,context)
  assert not log_groups.client.create_log_group.called
  log_groups.client.put_retention_policy.assert_called_with(logGroupName=test_fixtures.LOG_GROUP_NAME, retentionInDays=30)
  assert log_groups.client.describe_subscription_filters.called
  assert log_groups.client.delete_subscription_filter.called
  assert log_groups.client.put_subscription_filter.called
  assert response == { 
    'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME,
    'Data': { 'Arn': test_fixtures.FUNCTION_ARN }
  }
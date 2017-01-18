import pytest
import test_fixtures
from test_fixtures import context
from test_fixtures import log_groups
from test_fixtures import delete_event

def test_delete_destroy_false(log_groups, delete_event, context):
  response = log_groups.handle_delete(delete_event,context)
  assert not log_groups.client.delete_log_group.called
  assert response == { 'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME }

def test_delete_destroy_true_not_exist(log_groups, delete_event, context):
  delete_event['ResourceProperties']['Destroy'] = 'true'
  log_groups.client.describe_log_groups.return_value = {'logGroups': []}
  response = log_groups.handle_delete(delete_event,context)
  assert log_groups.client.describe_log_groups.called
  assert not log_groups.client.delete_log_group.called
  assert response == { 'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME }

def test_delete_destroy_true(log_groups, delete_event, context):
  delete_event['ResourceProperties']['Destroy'] = 'true'
  response = log_groups.handle_delete(delete_event,context)
  assert log_groups.client.describe_log_groups.called
  assert log_groups.client.delete_log_group.called
  assert response == { 'PhysicalResourceId': test_fixtures.LOG_GROUP_NAME }
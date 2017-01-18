import pytest
import mock
import time
from datetime import datetime
from uuid import uuid4

AWS_ACCOUNT_ID = 123456789012
AWS_REGION = 'us-west-2'
STACK_NAME = 'my-stack'
REQUEST_ID = str(uuid4())
RESOURCE_TYPE = 'Custom::LogGroup'
FUNCTION_NAME = 'cfnLogGroups'
FUNCTION_ARN = 'arn:aws:lambda:%s:%s:function:%s-%s' % (AWS_REGION, AWS_ACCOUNT_ID, STACK_NAME, FUNCTION_NAME)
SUBSCRIPTION_ARN = 'arn:aws:lambda:%s:%s:function:logSubscriber' % (AWS_REGION, AWS_ACCOUNT_ID)
MEMORY_LIMIT = '128'
STACK_ID = 'arn:aws:cloudformation:%s:%s:stack/%s/%s' % (AWS_REGION, AWS_ACCOUNT_ID, STACK_NAME, str(uuid4()))
LOGICAL_RESOURCE_ID = 'MyLogGroup'
UTC = datetime.utcnow()
NOW = int(time.time())
LOG_GROUP_NAME = '/aws/lambda/my-log-group'
LOG_STREAM_NAME = '%s/[$LATEST]%s' % (UTC.strftime('%Y/%m/%d'), uuid4().hex)
DESCRIBE_LOG_GROUPS = {
  'logGroups': [{
    'logGroupName': LOG_GROUP_NAME,
    'creationTime': NOW,
    'retentionInDays': 30,
    'metricFilterCount': 0,
    'arn': FUNCTION_ARN,
    'storedBytes': 1024
  }]
}
DESCRIBE_SUBSCRIPTION_FILTERS = { 
  'subscriptionFilters': [{
    'filterName': 'Default',
    'logGroupName': LOG_GROUP_NAME,
    'filterPattern': '',
    'destinationArn': SUBSCRIPTION_ARN,
    'creationTime': NOW
  }] 
}

class LambdaContext:
  def __init__(self):
    self.aws_request_id = REQUEST_ID
    self.log_group_name = LOG_GROUP_NAME
    self.log_stream_name = LOG_STREAM_NAME
    self.invoked_function_arn = FUNCTION_ARN
    self.client_context = None
    self.identity = None
    self.function_name = FUNCTION_NAME
    self.function_version = u'$LATEST'
    self.memory_limit_in_mb = MEMORY_LIMIT

@pytest.fixture
def context():
  return LambdaContext()

@pytest.fixture
def log_groups():
  with mock.patch('boto3.client') as client:
    import log_groups
    log_groups.client = client
    client.describe_log_groups.return_value = DESCRIBE_LOG_GROUPS
    client.describe_subscription_filters.return_value = { 'subscriptionFilters': [] }
    yield log_groups

@pytest.fixture
def create_event():
  return {
    u'StackId': unicode(STACK_ID),
    u'ResponseURL': u'https://cloudformation-custom-resource-response-uswest2.s3-us-west-2.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-west-2%3A429614120872%3Astack/intake-accelerator-dev/12947b30-d31a-11e6-93df-503acbd4dc61%7CMyLogGroup%7C720958cb-c5b7-4225-b12f-e7c5ab6c499b?AWSAccessKeyId=AKIAI4KYMPPRGIACET5Q&Expires=1483789136&Signature=GoZZ7Leg5xRsKq1hjU%2FO81oeJmw%3D',
    u'ResourceProperties': {
      u'Destroy': u'false',
      u'ServiceToken': unicode(FUNCTION_ARN),
      u'Name': unicode(LOG_GROUP_NAME),
      u'Retention': u'30'
    },
    u'ResourceType': unicode(RESOURCE_TYPE),
    u'RequestType': u'Create',
    'CreationTime': NOW,
    u'ServiceToken': unicode(FUNCTION_ARN),
    u'RequestId': unicode(REQUEST_ID),
    u'LogicalResourceId': unicode(LOGICAL_RESOURCE_ID)
  }

@pytest.fixture
def update_event():
  event = create_event()
  event[u'RequestType'] = u'Update'
  event[u'PhysicalResourceId'] = unicode(LOG_GROUP_NAME)
  event[u'OldResourceProperties'] = {
    u'Destroy': u'false', 
    u'ServiceToken': unicode(FUNCTION_ARN),
    u'Name': unicode(LOG_GROUP_NAME),
    u'Retention': u'30'
  }
  return event

@pytest.fixture
def delete_event():
  event = create_event()
  event[u'RequestType'] = u'Delete'
  event[u'PhysicalResourceId'] = unicode(LOG_GROUP_NAME)
  return event
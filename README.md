# CloudFormation Log Groups Lambda Function

This repository defines the Lamdba function `cfnLogGroups`.

This function supports the following features:

- Creation/Modification and Deletion of CloudWatch log groups
- Retain CloudWatch log groups even if the log group resource is deleted via CloudFormation (this is the default behaviour)

## Build Instructions

Any dependencies need to defined in `src/requirements.txt`.  Note that you do not need to include `boto3`, as this is provided by AWS for Python Lambda functions.

To build the function and its dependencies:

`make build`

This will create the necessary dependencies in the `src` folder and create a ZIP package in the `target` folder.  This file is suitable for upload to the AWS Lambda service to create a Lambda function.

```
$ make build
=> Building cfnLogGroups.zip...
Collecting cfn_resource (from -r requirements.txt (line 1))
Installing collected packages: cfn-resource
Successfully installed cfn-resource-0.2.2
updating: cfn_resource-0.2.2.dist-info/ (stored 0%)
updating: cfn_resource.py (deflated 67%)
updating: cfn_resource.pyc (deflated 62%)
updating: requirements.txt (stored 0%)
updating: setup.cfg (stored 0%)
updating: stack_resources.py (deflated 63%)
=> Built target/cfnLogGroups.zip
```

### Function Naming

The default name for this function is `cfnLogGroups` and the corresponding ZIP package that is generated is called `cfnLogGroups.zip`.

If you want to change the function name, set the `FUNCTION_NAME` environment variable to the custom function name.

## Publishing the Function

When you publish the function, you are simply copying the built ZIP package to an S3 bucket.  Before you can do this, you must ensure your environment is configured correctly with appropriate AWS credentials.

To deploy the built ZIP package:

`make publish`

This will upload the built ZIP package to an appropriate S3 bucket as defined via the `S3_BUCKET` Makefile/Environment variable.

### Publish Example

```
$ export AWS_PROFILE=caintake-admin
$ make publish
=> Publishing cfnLogGroups.zip to s3://429614120872-cfn-lambda...
=> Published to S3 URL: https://s3-us-west-2.amazonaws.com/429614120872-cfn-lambda/cfnLogGroups.zip
=> S3 Object Version: DDB7tb7QDEReC3r9bf7PgOSsEm7soplc
```

## CloudFormation Usage

This function is designed to be called from a CloudFormation template as a custom resource.

The following custom resource calls this Lambda function when the resource is created, updated or deleted:

```
  StackResources:
    Type: "Custom::LogGroup"
    Properties:
      ServiceToken: "arn:aws:lambda:us-west-2:429614120872:function:my-product-dev-cfnLogGroups"
      Name: my-log-group
      Retention: 30
      Destroy: false
      Subscription:
      - FilterName: Default
        FilterPattern: ""
        DestinationArn:
          Fn::Sub: ${SomeLogSource.Arn}
```

The following table describes the various properties:

| Property     | Description                                                                                                                                                                                                                              | Required | Default Value |
|--------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|---------------|
| ServiceToken | The ARN of the Lambda function                                                                                                                                                                                                           | Yes      |               |
| Name         | The name of the CloudWatch logs group                                                                                                                                                                                                    | Yes      |               |
| Retention    | The log retention in days for the logs group.  See [AWS documentation](http://docs.aws.amazon.com/AmazonCloudWatchLogs/latest/APIReference/API_PutRetentionPolicy.html#CWL-PutRetentionPolicy-request-retentionInDays) for valid values | No       | 30            |
| Destroy      | Specifies if the CloudWatch logs group should be destroyed in the event a CloudWatch DELETE event is received for the resource.                                                                                                          | No       | false         |
| Subscription | Defines a subscription to the CloudWatch logs group.  See the subscription options table below for further details                                                                                                                       | No       |               |
| Triggers     | List of triggers that can be used to trigger updates to this resource, based upon changes to other resources.  This property is ignored by the Lambda function.                                                                          | No       |               |

The following table describes Subscription properties:

| Property       | Description                                                                                                                                                               | Required | Default Value  |
|----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|----------------|
| DestinationArn | The Amazon Resource Name (ARN) that log events will be streamed to                                                                                                        | Yes      |                |
| FilterName     | A name for the filter                                                                                                                                                     | No       | default        |
| FilterPattern  | The CloudWatch logs [filter pattern](http://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html) to apply to events streamed to the subscription | No       | <empty-string> |
### Return Values

This function will return the following properties to CloudFormation:

| Property           | Description                                                 |
|--------------------|-------------------------------------------------------------|
| PhysicalResourceId | The name of the CloudWatch logs group                       |
| Arn                | The Amazon Resource Name (ARN) of the CloudWatch logs group |

For example, you can obtain the ARN of a CloudWatch logs group resource in your CloudFormation templates as shown:

```
Fn::Sub: ${MyCustomLogGroup.Arn}
```
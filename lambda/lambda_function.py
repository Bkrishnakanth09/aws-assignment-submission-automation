import json
import os
import urllib.parse
import boto3

# Connect to AWS services
dynamodb = boto3.resource("dynamodb")
sns = boto3.client("sns")

# Read environment variables
table = dynamodb.Table(os.environ["TABLE_NAME"])
sns_topic_arn = os.environ["SNS_TOPIC_ARN"]


def lambda_handler(event, context):

    print("Assignment upload event received")

    # Process each uploaded file
    for record in event["Records"]:

        # Get S3 information
        s3_data = record["s3"]
        bucket_name = s3_data["bucket"]["name"]

        # Decode the uploaded file name
        object_key = urllib.parse.unquote_plus(
            s3_data["object"]["key"]
        )

        # Extract student ID from folder structure
        # Example: incoming/student-001/file.pdf
        parts = object_key.split("/")

        if len(parts) < 3 or parts[0] != "incoming":
            raise ValueError("Invalid assignment folder structure")

        student_id = parts[1]

        # Get file information
        file_name = parts[-1]
        file_size = s3_data["object"].get("size", 0)
        event_time = record.get("eventTime", "Unknown")

        # Create a unique submission ID
        submission_id = (
            f"{bucket_name}#{object_key}#{event_time}"
        )

        # Prepare assignment details
        item = {
            "submissionId": submission_id,
            "studentId": student_id,
            "bucket": bucket_name,
            "fileName": file_name,
            "objectKey": object_key,
            "fileSize": file_size,
            "uploadTime": event_time,
            "status": "Submitted"
        }

        # Save details in DynamoDB
        table.put_item(Item=item)

        print("Assignment details saved in DynamoDB")

        # Prepare email notification
        message = {
            "studentId": student_id,
            "fileName": file_name,
            "uploadTime": event_time,
            "bucket": bucket_name,
            "objectKey": object_key
        }

        # Send notification using SNS
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject="New Assignment Submission",
            Message=json.dumps(message, indent=4)
        )

        print("Email notification sent successfully")

    return {
        "statusCode": 200,
        "body": json.dumps(
            "Assignment processed successfully"
        )
    }


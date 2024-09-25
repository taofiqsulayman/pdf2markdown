import json
import boto3
import os
import time

# Initialize clients
batch_client = boto3.client('batch')
sqs_client = boto3.client('sqs')

# The environment variables for your batch job queue, job definition, and results bucket
BATCH_JOB_QUEUE = os.environ['BATCH_JOB_QUEUE']
BATCH_JOB_DEFINITION = os.environ['BATCH_JOB_DEFINITION']
RESULTS_BUCKET = os.environ['RESULTS_BUCKET']

# Function to trigger the AWS Batch job
def submit_batch_job(files):
    try:
        # Prepare job parameters
        job_name = f"file-processing-job-{int(time.time())}"
        
        # Pass the files and results bucket as environment variables to the Batch job
        container_overrides = {
            'environment': [
                {'name': 'FILES', 'value': json.dumps(files)},
                {'name': 'RESULTS_BUCKET', 'value': RESULTS_BUCKET}
            ]
        }

        # Submit the job to AWS Batch
        response = batch_client.submit_job(
            jobName=job_name,
            jobQueue=BATCH_JOB_QUEUE,
            jobDefinition=BATCH_JOB_DEFINITION,
            containerOverrides=container_overrides
        )
        
        print(f"Batch job submitted successfully: {response}")
        return response
    except Exception as e:
        print(f"Error submitting batch job: {str(e)}")
        raise

# Main Lambda handler
def lambda_handler(event, context):
    try:
        # Extract messages from SQS event
        records = event.get('Records', [])
        files = []

        for record in records:
            # Extract S3 event data from the message body
            body = json.loads(record['body'])
            s3_event = json.loads(body['Message'])
            s3_bucket = s3_event['Records'][0]['s3']['bucket']['name']
            s3_key = s3_event['Records'][0]['s3']['object']['key']

            # Append each file's bucket and key to the list
            files.append({
                'bucket': s3_bucket,
                'key': s3_key
            })
        
        if files:
            # Trigger AWS Batch job with the list of files
            submit_batch_job(files)
        else:
            print("No valid files found in the SQS event.")

        return {
            'statusCode': 200,
            'body': json.dumps('Batch job submitted successfully!')
        }

    except Exception as e:
        print(f"Error processing SQS event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }

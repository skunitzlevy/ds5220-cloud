import boto3
from botocore.exceptions import ClientError

sqs = boto3.client('sqs')

def create_queue(queue_name):
    try:
        print(f"Creating queue: {queue_name}")
        response = sqs.create_queue(
            QueueName=queue_name
        )
        print(f"Queue URL: {response['QueueUrl']}")
        return response['QueueUrl']
    except ClientError as e:
        if e.response['Error']['Code'] == 'QueueAlreadyExists':
            print(f"Queue already exists: {queue_name}")
            return None
        else:
            print(f"Error: {e}")
            return None
        return None

if __name__ == "__main__":
    queue_name = 'ds5220'
    create_queue(queue_name)
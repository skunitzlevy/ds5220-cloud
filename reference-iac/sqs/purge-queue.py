import boto3

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/440848399208/ds5220'

# empty the queue completely
def purge_queue():
    try:
        response = sqs.purge_queue(
            QueueUrl=queue_url
        )
        print(response)
        return response['ResponseMetadata']['RequestId']
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    purge_queue()
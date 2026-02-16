import boto3

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/440848399208/ds5220'

def check_queue():
    try:
        response = sqs.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['All']
        )

        # print(response)

        print(f"Approximate messages: {response['Attributes']['ApproximateNumberOfMessages']}")
        print(f"    Delayed messages: {response['Attributes']['ApproximateNumberOfMessagesDelayed']}")
        print(f"Not visible messages: {response['Attributes']['ApproximateNumberOfMessagesNotVisible']}")
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    check_queue()
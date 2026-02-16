import boto3

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/440848399208/ds5220'

# fetch a message from the queue
def fetch_message():
    try:  
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1
        )
        if response['Messages']:
            # do something with your logic here
            # . . .
            # . . .
            delete_message(response['Messages'][0]['ReceiptHandle'])
            return response['Messages'][0]['Body']
        else:
            print("No message found")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def delete_message(receipt_handle):
    try:
        response = sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        print("Message deleted")
        return response['ResponseMetadata']['RequestId']
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = fetch_message()
    print(f"Body: {result}")

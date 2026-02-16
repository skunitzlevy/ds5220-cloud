import boto3
import random

sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/440848399208/ds5220'
words = ['apples', 'bananas', 'cherries', 'dates', 'elderberries', 'figs', 'grapes', 'honeydew', 'kiwis', 'lemons', 'mangos', 'nectarines', 'oranges', 'peaches', 'plums', 'quinces', 'raspberries', 'strawberries', 'tangerines', 'uva', 'watermelons', 'xigua', 'yuzu', 'zucchini']

# send a message with a random word from the list as the message body
def send_message(message):
    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message
        )
        print(response)
        return response['MessageId']
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    random_word = random.choice(words)
    send_message(random_word)
#!/usr/bin/env python3

import boto3
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='s3_buckets.log'
    )
logger = logging.getLogger(__name__)

# global variable - can be called from anywhere in the code
s3 = boto3.client('s3')

def get_buckets():
    try:
        response = s3.list_buckets()
        logger.info(f"Fetching buckets:")
        for b in response['Buckets']:
            print(b['Name'])
            logger.info(f"Bucket: {b['Name']}")
    except Exception as e:
        logger.error(f"Error listing buckets: {e}")
        return None

if __name__ == "__main__":
    get_buckets()


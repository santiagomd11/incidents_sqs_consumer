import os
import boto3
import logging
import requests

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def ensure_envvars():
    """Ensure that these environment variables are provided at runtime"""
    required_envvars = [
        "AWS_REGION",
        "SQSCONSUMER_QUEUENAME",
        "URL_BASE_INCIDENTS"
    ]

    missing_envvars = []
    for required_envvar in required_envvars:
        if not os.environ.get(required_envvar, ''):
            missing_envvars.append(required_envvar)

    if missing_envvars:
        message = "Required environment variables are missing: " + \
            repr(missing_envvars)
        raise AssertionError(message)


def process_message(message_body, message_attributes):
    logger.info(f"Processing message: {message_body}")
    logger.info(f"Message attributes: {message_attributes}")
    
    response: object
    url: str = None  # Initialize url with a default value

    if message_attributes is not None:
        event: str = message_attributes.get('event').get('StringValue').lower()
        url = message_attributes.get('url_origin').get('StringValue')
        method: str = message_attributes.get('method').get('StringValue').lower()

        # Call incident API
        if event not in ['incident', 'incidents']:
            logger.error(f"Unhandled event type: {event}")
            return None

    if not url:
        logger.error("URL was not defined, skipping message")
        return None

    payload = message_body

    if method == 'post':
        response = requests.post(url, payload)
    elif method == 'delete':
        response = requests.delete(url, payload)
    elif method == 'put':
        response = requests.put(url, payload)

    logger.info(f"Response: {response.text}, status: {response.status_code}")
    return response


def main():
    logger.info("SQS Consumer starting ...")
    try:
        ensure_envvars()
    except AssertionError as e:
        logger.error(str(e))
        raise

    queue_name = os.environ["SQSCONSUMER_QUEUENAME"]
    logger.info(f"Subscribing to queue {queue_name}")

    sqs = boto3.resource('sqs', region_name=os.environ.get('AWS_REGION'))
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    while True:
        messages = queue.receive_messages(
            MaxNumberOfMessages=1,
            WaitTimeSeconds=1,
            MessageAttributeNames=['All']
        )
        for message in messages:
            try:
                process_message(message.body, message.message_attributes)
            except Exception as e:
                logger.error(f"Exception while processing message: {repr(e)}")
                continue

            message.delete()


if __name__ == "__main__":
    main()

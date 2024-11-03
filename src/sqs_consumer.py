import os
import boto3
import logging
import requests
import json
from email_client import send_email

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

def ensure_envvars():
    """Ensure that these environment variables are provided at runtime"""
    required_envvars = [
        "AWS_REGION",
        "SQSCONSUMER_QUEUENAME",
        "URL_BASE_INCIDENTS",
        "GMAIL_USER",
        "GMAIL_PASSWORD"
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

    payload = json.loads(message_body)

    headers = {
        'Content-Type': 'application/json'
    }

    if method == 'post':
        response = requests.post(url, json=payload, headers=headers)
    elif method == 'delete':
        response = requests.delete(url, json=payload, headers=headers)
    elif method == 'put':
        response = requests.put(url, json=payload, headers=headers)
    else:
        logger.error(f"Unhandled method: {method}")
        return None

    logger.info(f"Response: {response.text}, status: {response.status_code}")

    if response.status_code == 201:  # This checks for any 2xx status code
        response_data = response.json()
        incident_id = response_data.get('id', 'N/A')
        description = response_data.get('description', 'N/A')
        to_email = response_data.get('userEmail', 'N/A')
        
        subject = "do not reply abc-call"
        message = f"""
        Hola, soy el bot de ABC-CALL
        
        Tu incident:
        id: {incident_id}, 
        descripcion: {description}
        
        Gracias por elegir nuestros servicios!
        """
    else:
        # Handle unsuccessful response
        subject = "do not reply abc-call"
        to_email = payload.get('userEmail', 'N/A')  # Fallback to user's email in the original payload
        message = """
        Hola, soy el bot de ABC-CALL

        Tu incidente no pudo ser registrado, vuelve a intentarlo desde nuestra pagina de registro. Agradecemos tu comprension.

        Gracias por elegir nuestros servicios!
        """

    if to_email != 'N/A':
        # Send email via Gmail SMTP
        send_email(to_email, subject, message.strip())

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
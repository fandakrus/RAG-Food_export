import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

try:
    ses_client = boto3.client('ses', region_name='ap-southeast-1')  # Replace with your region
    response = ses_client.send_email(
        Source='register@foodprobot.com',
        Destination={
            'ToAddresses': ['fanda747@seznam.cz']
        },
        Message={
            'Subject': {'Data': 'Test Email'},
            'Body': {'Text': {'Data': 'This is a test email.'}}
        }
    )
    print("Email sent successfully")
except (NoCredentialsError, PartialCredentialsError) as e:
    print(f"Credentials error: {e}")
except Exception as e:
    print(f"Error sending email: {e}")
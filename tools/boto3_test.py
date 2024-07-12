import boto3

def send_verification_email(user, token):
    ses_client = boto3.client('ses', region_name='eu-central-1')
    verification_link = f"http://localhost:5000/verify_email/{token}"
    subject = "Verify your email address"
    body_text = f"""
    Hi {user},

    Please click the link below to verify your email address:

    {verification_link}

    If you did not request this, please ignore this email.

    Thank you,
    Your FOODBOT team
    """
    try:
        response = ses_client.send_email(
        Source='krus.frantisek@gmail.com',
        Destination={
            'ToAddresses': ["fanda747@seznam.cz"]
        },
        Message={
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body_text,
                    'Charset': 'UTF-8'
                }
            }
        }
    )   
        print(response)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
    
send_verification_email("Frantisek", "123")
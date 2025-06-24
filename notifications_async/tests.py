from django.test import TestCase

# Create your tests here.
from notifications.utils import notify_user

# Send to single user
notify_user(
    user_id=15,
    title='Order Shipped',
    message='Your order #1234 has been shipped',
    priority='medium',
    notification_type='order'
)


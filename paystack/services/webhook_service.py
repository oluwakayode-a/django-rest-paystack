import hashlib
import hmac

from django.conf import settings
from rest_framework.exceptions import ValidationError

from .customer_service import CustomerService
from .transaction_service import TransactionService


class WebhookService(object):
    def __init__(self, request) -> None:
        self.request = request

    def webhook_handler(self):
        try:
            secret = getattr(settings, "PAYSTACK_PRIVATE_KEY")
        except Exception as e:  # If user hasn't declared variable
            raise ValidationError(e)

        # Use self.request.body instead of self.request.data ==> according to Paystack docs.
        # DRF request.data is a bit different from the default request.body
        webhook_data = self.request.body

        # using the secret key without encoding throws an error.
        hash = hmac.new(secret.encode('utf-8'), webhook_data, digestmod=hashlib.sha512).hexdigest()

        if hash != self.request.headers["x-paystack-signature"]:
            raise ValidationError("MAC authentication failed")

        if webhook_data["event"] == "charge.success":
            paystack_service = TransactionService()
            paystack_service.log_transaction(webhook_data["data"])

            customer_service = CustomerService()
            customer_service.log_customer(webhook_data["data"])

        return webhook_data

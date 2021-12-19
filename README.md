<h1>
	django-rest-paystack: a minimal SDK for integrating Paystack into your django-rest API backend.
</h1>

![Github-A Build Status](https://github.com//Nyior/django-rest-paystack/actions/workflows/lint_and_test.yml/badge.svg)
[![PyPI version](https://badge.fury.io/py/django-rest-paystack.svg)](https://badge.fury.io/py/django-rest-paystack)


<p>
    Focus on your business logic. Leave all the mundane payment _serere_ to us.
    Our package will do all the heavy lifting for you :D
</p>

## Contents

* [What is django-rest-paystack?](#what-is-django-rest-paystack)
* [How do I use this package in my project?](#how-do-i-use-this-package-in-my-project)
* [Paying for an order](#paying-for-an-order)
* [How can I extend the webhook class?](#how-can-i-extend-the-webhook-class)
* [Limitations](#todo)
* [Contributing](#contributing)
* [Acknowledgements](#acknowledgements)
* [Wanna thank me? Just star this repo](#oh-okay-i-gerrit-thank-you-nyior)

## What is django-rest-paystack?

### Overview
Creating those payment endpoints for every single e-commerce project we work on could become
redundant and perharps somewhat boring overtime. While there are different approaches to integrating and processing payments with a gateway like Paystack(more on this later), in each approach, the flow doesn't really change. If it doesn't change then why repeat yourself? _you nor need stress  lol_

    DRY: Enter django-rest-paystack.
        when installed and configured, this package generates all the endpoints you'd need to start and
        complete a transaction. 

### Endpoints
* initialize a transaction: 
```python
        POST /api/v1/paystack/transaction/initiate

        minimal_payload = {
            "amount": 0,
            "email": "string",
            "metadata": dict/json, --Optional
        }

        # By default, this package always sends the user_id metadata to paystack
        # There lots of other optional parameters you could add to the payload --refer to paystack docs
```
* verify a transaction:  `GET /api/v1/paystack/transaction/verify/?transaction_ref="ref"`

* Get user authorization code: `GET /api/v1/paystack/paystack-customer/{user__id}/`

* charge an authorization: 
```python
        POST /api/v1/paystack/transaction/charge-customer`
        minimal_payload = {
            "amount": 0,
            "email": "string",
            "authorization_code": "string",
        }
```

* handle webhooks: ` api/v1/paystack/webook-handler`

* get all transactions: `/api/v1/paystack/transaction`

* retrieve a single transaction: `/api/v1/paystack/transaction/{uuid}`
* This package also logs some relevant data like the authorization_code in the db.

If you're not very familiar with how some of those endpoints work, don't worry, I will get to that in a bit.


## How do I use this package in my project?

### Quick Setup

Install package

    pip install django-rest-paystack
    
Add `paystack` app to INSTALLED_APPS in your django `settings.py`:

```python
INSTALLED_APPS = (
    ...,
    'rest_framework',
    'rest_framework.authtoken',
    ...,
    'paystack'
)
```

Load paystack credentials in your django `settings.py`:

```python
# Ideally, these values should be stored as environment variables, and loaded like so:

PAYSTACK_PUBLIC_KEY=os.environ.get('name-of-var')
PAYSTACK_PRIVATE_KEY=os.environ.get('name-of-var')

```

Add URL patterns

```python
urlpatterns = [
    path('paystack/', include('paystack.urls')),
]
```

Specify DEFAULT_AUTHENTICATION_CLASSES to be applied to the Paystack views(OPTIONAL)
in your `settings.py`like so:

```python
# Note: Specifying this is optional, and when you don't, 
# This package defaults to the TokenAuthentication class

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": "rest_framework.schemas.coreapi.AutoSchema"
}
```

Run migrations to create the `PaystackCustomer, TransactionLog` models that comes with this package

```python
manage migrate

# The created models are automically registered and made available to you in the admin view
```

## Paying for an order
While the checkout process could be handled in different ways with Paystack, the general flow is this:
* Payment is initialized from the frontend. Initializing a payment entails collecting the user details(email, name), and total amount and sending it to Paystack.
* A response is then returned to the frontend. The response usually contains useful data like the _access code_, and the _redirect url_.
* The frontend then charges the user's card
* Once the card is charged and the process completed, paystack then returns the _transaction_reference_(a unique identifier for each transaction) to the frontend
* The frontend could then use the _transaction_reference_ to verify(get the status) of the  transaction
* In addition, Once the card is charged and the process completed, paystack then sends an event to a specified webhook url

#### That's the general flow. Let's look at these specific ways...
There are about four ways of handling checkouts with Paystack. This package has been designed to cater for the three most common approaches.
Let's quickly go over the flow for each approach and how you could use this package to process an order in each scenario.

##### Paystack Popup: with Paystack inline Javascript
Here you'd import Paystack's inline Javascript using the _script_ tag. This will inturn insert the Paystack's pay button somewhere on your page. on click of the pay button, the popup for collecting a customer's card details is loaded and shown to the user. (oversimplified sha).

Follow the below steps to use this package to process an order in this scenario:
* Do all the necessary frontend setup. The initialization of payment happens entirely on the frontend.
* Once a card has been charged from the frontend. You could verify the transaction using the `GET /api/v1/paystack/transaction/verify/?transaction_ref="ref"` endpoint

##### Redirect: redirecting to a paystack page outside your website or mobile app
No imports required here. A user is redirected to paystack where they make payment.

Follow the below steps to use this package to process an order in this scenario:

* Make a call to the ` POST /api/v1/paystack/transaction/initiate ` with the expected payload from the frontend to initialize a transaction
* The endpoint then returns a response that contains the _redirect url_ and _access code_ to the frontend
* The frontend then redirects the customer to the _redirect url_ returned in the reponse. The customer is charged there.
* Make sure to add a CALL BACK URL on your paystack dashboard. Once the customer has been charged on the redirect page they'd be taken back to the CALL BACK URL you specify(usually a page on your site). When the users are taken back to the CALL BACK URL, the transaction reference for that transaction is appended to the URL. 
* Once a user is taken back to the CALL BACK URL on your site, You could then extract the _transaction reference_ appended to the URL and make a call to the  `GET /api/v1/paystack/transaction/verify/?transaction_ref="ref"` endpoint to verify the transaction.

##### Paystack mobile SDKs
No redirect here. It's the mobile version of the Paystack inline Javascript popup for web applications.

Follow the below steps to use this package to process an order in this scenario:
* Do all the necessary frontend setup. Essentially, you'd have to integrate some mobile SDK that allows users make payment within your mobile app without redirecting the user.
* Make a call to the ` POST /api/v1/paystack/transaction/initiate ` with the expected payload from the frontend to initialize a transaction
* The endpoint then returns a response that contains the _access code_ and _redirect url_ to the frontend
* The frontend could then use the access code to charge a card within the app using the mobile SDK integrated. 
* Once a card has been charged from the frontend using the mobile SDK a response is returned containing the transaction reference. You could then verify the transaction using the `GET /api/v1/paystack/transaction/verify/?transaction_ref="ref"` endpoint


In all scenarios, make sure to specify the `your-domain + api/v1/paystack/webook-handler` endpoint as your WEBHOOOK URL on your Paystack dashboard. It is important that you do this because, eventhough we have an endpoint where you could verify and get the status of a transaction, it is in the webhook that we are logging things like the transaction data as well as other things like the authorization_code that could be used to charge a customer that has already been charged in the past. See code snipet below:

```python
class WebhookService(object):
    def __init__(self, request) -> None:
        self.request = request

    def webhook_handler(self):
        secret = getattr(
            settings, ' PAYSTACK_PRIVATE_KEY', None
        )
        webhook_data = self.request.data
        hash = hmac.new(secret, webhook_data, digestmod=hashlib.sha512).hexdigest()

        if hash != self.request.headers["x-paystack-signature"]:
            raise ValidationError("MAC authentication failed")

        if webhook_data["event"] == "charge.success":
            paystack_service = TransactionService()
            paystack_service.log_transaction(webhook_data["data"])

            customer_service = CustomerService() # logs customer data like the auth_code here
            customer_service.log_customer(webhook_data["data"])

        return webhook_data
```

**NOTE:** Always offer value in the Webook. For exaxmple, if you want to create an instance of an
order for users after they've paid, it is advisable that you do that in the webhook. Paystack recommends that.

Keeping in mind that you might want to perform some custom actions in the webhook that we can't possibly 
predict, we made the webhook class extensible.

## How can I extend the webhook class?
If you wish to extend the webhook class, then here is how to:

### The WebhookFacadeView

```python
# First import the WebhookFacade
from paystack.views import WebhookFacadeView


# Then create your own view that extends the Facade
class WebhookView(WebhookFacadeView):
   
    def post(self, request):
        webhook_data = super().post(request)

        # do whatever you want with the webhook data
        # Then return a response to Paystack

```
## Oh okay, I gerrit. Thank you Nyior
You're welcome. If you like this repo, click the :star: I'd appreciate that.


## TODO:
* Add split payments feature
* Enable transfers
* Enable subscription based(recurring) payments
* Make tests more encompassing


## Contributing
* Create an Issue for the feature/bug you'd like to work on. Or just pick an existing issue.
* Setup project locally and write your code.
* We use isort, black, and flake8 as one of the measures taken to ensure high code quality(We still need more of these measures sha). We use a precommit hook to run isort, black and flake8 each time we make a commit. We advice that you do thesame.
* Each time you're done making your changes, run the test suite locally, and ensure they're all passing.
* Also write tests for your new changes.
* If all test are passing, you can then open a PR targeted on main.
**Note:** A workflow will be executed on your PR. So if you don't follow the instructions above. The build will fail and your PR won't be reviewed. 

## Acknowledgements
In building this, I found the following repositories really helpful
* [laravel-paystack](https://github.com/unicodeveloper/laravel-paystack)
* [popoola/pypaystack](https://github.com/edwardpopoola/pypaystack)
* [gbozee/pypaystack](https://github.com/gbozee/pypaystack)

## License
This project is released under the [MIT](https://choosealicense.com/licenses/mit/) License

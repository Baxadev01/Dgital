import stripe
from django.conf import settings

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)

def get_vat_tax_rates():
    # We currently support the following countries: US, GB, AU, and all countries in the EU.
    # пока сделал такую фильтрацию, другиъ применеий пока не планируется, 
    # но если будут - возможно придется тут поменять
    tax_rates = stripe.TaxRate.list(active=True,inclusive=False,limit=100)
    rates_list = [rate.id for rate in tax_rates if rate.display_name == 'VAT']

    return rates_list

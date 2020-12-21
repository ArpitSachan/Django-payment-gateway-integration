from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
from paytm import models
from paytm import private
from django.views.generic import TemplateView

# Create your views here.

class AboutView(TemplateView):
    template_name = 'paytm/about.html'

@login_required
def initiate_payment(request):
    if request.method == 'GET':
        return render(request, 'paytm/pay.html')

    amount = int(request.POST['amount'])
    username = request.POST['username']
    password = request.POST['password']
    try:
        user = authenticate(username=username, password=password)
        if user is None:
            raise ValueError
    except:
        return render(request, 'paytm/pay.html', context={'error':'wrong credentials'})

    transaction = models.Transaction.objects.create(made_by=user, amount=amount)
    transaction.save()
    merchant_key = settings.PAYTM_SECRET_KEY

    params = dict((
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str(transaction.made_by.email)),
        ('TXN_AMOUNT', str(amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', settings.PAYTM_CALLBACK_URL),
    ))

    checksum = private.generate_checksum(params, merchant_key)

    transaction.checksum = checksum
    transaction.save()

    params['CHECKSUMHASH'] = checksum
    print('Sent:', checksum)
    return render(request, 'paytm/redirect.html', context=params)


@csrf_exempt
def paytm_callback(request):
    if request.method == 'POST':
        paytm_checksum = ''
        data = dict(request.POST)
        params = {}
        paytm_checksum = data['CHECKSUMHASH'][0]
        for key, value in data.items():
            if key == 'CHECKSUMHASH':
                paytm_checksum = value[0]
            else:
                params[key] = str(value[0])
        
        is_valid_checksum = private.verify_checksum(params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
        if is_valid_checksum:
            print('Checksum matched')
            data['message'] = "Checksum matched!"
        else:
            print('Mismatched')
            data['message'] = 'Checksum mismatched!'
        
        return render(request, 'paytm/callback.html', context=data)
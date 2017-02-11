import mechanize
import boto3
import os
import botocore

try:
    sns     = boto3.client('sns')
    decrypt = boto3.client('kms').decrypt
except botocore.exceptions.NoRegionError:
    aws_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    sns     = boto3.client('sns', region_name=aws_region)
    decrypt = boto3.client('kms', region_name=aws_region).decrypt

# E.g., a US phone number with area code 123: '+11239873456'
phone_number='PHONE NUMBER WITH COUNTRY AND AREA CODE'

# Load encrypted credit card information (stored in environment variables).
from base64 import b64decode
CC_number           = decrypt(CiphertextBlob=b64decode(os.environ['CC_number']))['Plaintext']
print CC_number
CC_expiration_month = decrypt(CiphertextBlob=b64decode(os.environ['CC_expiration_month']))['Plaintext']
CC_expiration_year  = decrypt(CiphertextBlob=b64decode(os.environ['CC_expiration_year']))['Plaintext']
CC_CVV              = decrypt(CiphertextBlob=b64decode(os.environ['CC_CVV']))['Plaintext']

# Choose an org to donate to; defaults to ACLU.
# 'ACLU' or 'Planned Parenthood'
org = 'ACLU'
#org = 'Planned Parenthood'

# E.g., to donate $5 (the minimum): '5' 
donation_amount = 'AMOUNT'

first_name = 'FIRST_NAME'
last_name  = 'LAST_NAME'
email      = 'EMAIL'

address = 'ADDRESS'
city    = 'CITY'
# For ACLU, need state numerical code. For Planned Parenthood, two-letter abbreviation.
state   = 'STATE'
zipcode = 'ZIPCODE'
# For ACLU, need country numerical code. For Planned Parenthood, country name (US is default).
country = 'COUNTRY'

f_map = {
    'ACLU': { 
        'url'        : 'https://action.aclu.org/donate-aclu',
        'form'       : ('nr', 3),
        'onetime'    : ('submitted[donation][aclu_recurring]', ['0']),
        'onetime_opt': ('submitted[donation][amount]', ['other']),
        'amount'     : ('submitted[donation][other_amount]', donation_amount),
        'first_name' : ('submitted[donor_information][first_name]', first_name),
        'last_name'  : ('submitted[donor_information][last_name]', last_name),
        'email'      : ('submitted[donor_information][email]', email),
        'address'    : ('submitted[billing_information][address]', address),
        'city'       : ('submitted[billing_information][city]', city),
        'state'      : ('submitted[billing_information][state]', [state]),
        'zipcode'    : ('submitted[billing_information][zip]', zipcode),
        'cc_num'     : ('submitted[credit_card_information][card_number]', CC_number),
        'cc_exp_mon' : ('submitted[credit_card_information][expiration_date][card_expiration_month]', [CC_expiration_month]),
        'cc_exp_yr'  : ('submitted[credit_card_information][card_cvv]', CC_CVV),
        'extra_args' : [
            ('submitted[credit_card_information][fight_for_freedom][1]', 0),
            ('submitted[credit_card_information][profile_may_we_share_your_info][1]', 0)
        ],
        'validation' : 'thank you',
        'org_pprint' : 'the ACLU'
    },
    'Planned Parenthood': {
        'url'        : 'https://www.plannedparenthood.org/',
        'form'       : 'process', 
        'onetime'    : ('gift_type', ['onetime']),
        'onetime_opt': ('submitted[donation][amount]', ['other']),
        'amount'     : ('submitted[donation][other_amount]', donation_amount),
        'first_name' : ('submitted[donor_information][first_name]', first_name),
        'last_name'  : ('submitted[donor_information][last_name]', last_name),
        'email'      : ('submitted[donor_information][email]', email),
        'address'    : ('submitted[billing_information][address]', address),
        'city'       : ('submitted[billing_information][city]', city),
        'state'      : ('submitted[billing_information][state]', [state]),
        'zipcode'    : ('submitted[billing_information][zip]', zipcode),
        'cc_num'     : ('submitted[credit_card_information][card_number]', CC_number),
        'cc_exp_mon' : ('submitted[credit_card_information][expiration_date][card_expiration_month]', [CC_expiration_month]),
        'cc_exp_yr'  : ('submitted[credit_card_information][card_cvv]', CC_CVV),
        'extra_args' : [],
        'validation' : 'thank you',
        'org_pprint' : 'Planned Parenthood'
    }
}

#print f_map[org]['first_name'][0], form_map[org]['state'][1], form_map[org]['extra_args'][0][0]

br = mechanize.Browser(factory=mechanize.RobustFactory()) 
br.set_debug_http(True)

#def lambda_handler(event, context):
def non_lambda():
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    
    br.open(f_map[org]['url'])

    if org.lower() == 'planned parenthood':
        # Find donation link.
        donate_links = br.links(url_regex='Donation')
        if not donate_links:
            print "Error: no donation link found."
            exit(1)
        donate_link = next(donate_links)
        br.open(donate_link.url)

    print br.geturl()

    form = f_map[org]['form']
    if type(form) is tuple:
        # E.g.: br.select_form(nr=3)
        form_in = 'br.select_form({}={})'.format(form[0], form[1])
        eval(form_in)
    else:
        br.select_form(form)
    
    onetime_key, onetime_val = f_map[org]['onetime']
    print br.form.find_control(name=onetime_key)
    #print br.form.find_control(name='gift_type')
    br.form[f_map[org]['onetime'][0]] = f_map[org]['onetime'][1]
    print br.form[onetime_key]
    print br.form.find_control(name=onetime_key)
       
    onetime_opt_key, onetime_opt_val = f_map[org]['onetime_opt']
    br.form[onetime_opt_key] = onetime_opt_val
    exit(1)

    br.form['gift_type'] = ['onetime']
    br.form['level_standardexpanded'] = ['30882']
    amount_ctrl = br.form.find_control(name='level_standardexpanded30882amount', type='text')
    amount_ctrl.value = '5'

    br.form['billing_first_namename'] = 'FIRST NAME'
    br.form['billing_last_namename'] = 'LAST NAME'
    br.form['donor_email_addressname'] = 'EMAIL'

    br.form['billing_addr_street1name'] = 'ADDRESS'
    br.form['billing_addr_cityname'] = 'CITY'
    # Two letter state abbreviation, all caps.
    br.form['billing_addr_state'] = ['STATE ABBREV']
    br.form['billing_addr_zipname'] = 'ZIPCODE'
    
    ccnum_ctrl = br.form.find_control(name='responsive_payment_typecc_numbername', type='text')
    ccnum_ctrl.value = CC_number

    br.form['responsive_payment_typecc_exp_date_MONTH'] = [CC_expiration_month]
    br.form['responsive_payment_typecc_exp_date_YEAR'] = [CC_expiration_year]
    
    cvv_ctrl = br.form.find_control(name='responsive_payment_typecc_cvvname', type='text')
    cvv_ctrl.value = CC_CVV
    
    exit(1)
    #response = br.submit()
    
    # Validate donation / form submission.
    if 'thank you' in response.read().lower():
        message = "Success! You donated $5 to Planned Parenthood :)"
    else:
        message = "Error: Your donation didn't go through :("

    # Send text message.
    sns.publish(PhoneNumber=phone_number, Message=message)

non_lambda()

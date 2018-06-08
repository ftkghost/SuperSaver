import re

from core.exception import InvalidInput


RE_ADDRESS_STREET = re.compile(r"^[-a-zA-Z0-9#_'.\s,()]{1,512}$")
RE_ADDRESS_CITY = re.compile(r'^[a-zA-Z]{1,128}$')
RE_ADDRESS_SUBURB = re.compile(r'^[-a-zA-Z0-9 ]{1,128}$')

# https://www.nzpost.co.nz/personal/sending-within-nz/how-to-address-mail/postcodes/how-postcodes-work
RE_ADDRESS_POSTAL_CODE_NZ = re.compile(r'^[0-9]{4}$')

RE_CONTACT_NAME = re.compile(r'^[-a-zA-Z ]{2,128}$')
# https://en.wikipedia.org/wiki/Telephone_numbers_in_New_Zealand#Mobile_phones
RE_CONTACT_NUMBER = re.compile(r'^[0-9]{8,10}$')


def check_non_empty_str(value: str, max_length=0, error_message=None):
    value = value.strip() if value else ''
    if not error_message:
        error_message = 'Invalid value ' + value
    if max_length and len(value) > max_length:
        raise InvalidInput(error_message)
    if not value:
        raise InvalidInput(error_message)
    return value


def check_non_empty_str_with_pattern(value: str, pattern, error_message: str=None):
    if not error_message:
        error_message = 'Invalid value ' + value
    value = check_non_empty_str(value, 0, error_message)
    if isinstance(pattern, str):
        regex = re.compile(pattern)
    else:
        # Assume it is re.__Regex
        regex = pattern
    if not regex.match(value):
        raise InvalidInput(error_message)
    return value


def check_and_normalise_nz_phone_number(nz_phone_number: str, error_message: str):
    phone = nz_phone_number.strip() if nz_phone_number else ''
    if not error_message:
        error_message = 'Invalid phone number {0}.'.format(nz_phone_number)
    if not phone:
        raise InvalidInput(error_message)
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('.', '')
    if not phone.startswith('0'):
        phone = '0' + phone

    # In RE_CONTACT_NUMBER, we only allow phone number length 8 to 10.
    # https://en.wikipedia.org/wiki/Telephone_numbers_in_New_Zealand#Mobile_phones
    if not RE_CONTACT_NUMBER.match(phone):
        raise InvalidInput(error_message)
    return phone

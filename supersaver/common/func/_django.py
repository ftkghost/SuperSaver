import json
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.db.models import Model
from django.db.models.fields.files import FieldFile
from django.template import loader as template_loader

from common.utils.datetime import to_client_timestamp


def none_if_model_not_exist(model_class, **kwargs):
    try:
        return_dict = False
        if 'return_dict' in kwargs:
            return_dict = kwargs['return_dict']
            del kwargs['return_dict']
        if return_dict:
            return model_class.objects.values().get(**kwargs)
        else:
            return model_class.objects.get(**kwargs)
    except ObjectDoesNotExist:
        return None


def convert_model_to_dict(obj, ignore_attr_with_prefix='_'):
    if obj is None or isinstance(obj, (int, str, float, bool)):
        return obj
    if isinstance(obj, dict):
        to_dict = {}
        for key in obj:
            if isinstance(key, str) and not key.startswith(ignore_attr_with_prefix):
                value = obj[key]
                if isinstance(value, datetime):
                    to_dict[key] = to_client_timestamp(value)
                elif isinstance(value, date):
                    to_dict[key] = value.isoformat()
                elif isinstance(value, UUID):
                    to_dict[key] = str(value)
                elif isinstance(value, Decimal):
                    to_dict[key] = str(value)
                elif isinstance(value, dict):
                    to_dict[key] = convert_model_to_dict(value, ignore_attr_with_prefix)
                elif isinstance(value, (tuple, list)):
                    l = []
                    for v in value:
                        l.append(convert_model_to_dict(v, ignore_attr_with_prefix))
                    to_dict[key] = l
                else:
                    to_dict[key] = value
    elif isinstance(obj, Model):
        # meta caches field names
        num_cache = len(obj._meta._get_fields_cache)
        fields_cache = None
        if num_cache > 0:
            fields_cache = list(obj._meta._get_fields_cache.values())[num_cache - 1]
        field_names = [field.name for field in fields_cache]
        to_dict = {}
        for key in field_names:
            if key not in obj.__dict__:
                continue
            value = obj.__dict__[key]
            if isinstance(value, datetime):
                # Client can not handle 6 digit microseconds in date time iso format.
                to_dict[key] = to_client_timestamp(value)
            elif isinstance(value, UUID):
                to_dict[key] = str(value)
            elif isinstance(value, Decimal):
                to_dict[key] = str(value)
            elif isinstance(value, FieldFile):
                to_dict[key] = value.url
            else:
                to_dict[key] = value
    else:
        raise TypeError('Can not convert type ' + str(type(obj)) + ' to dict.')
    return to_dict


def convert_models_to_dict_list(objects, ignore_attr_with_prefix='_'):
    if objects is None:
        return None
    if not isinstance(objects, (list, tuple)):
        raise TypeError('Can not convert ' + str(type(objects)) + ' to dict list.')
    to_dict_list = []
    for i in range(0, len(objects)):
        to_dict_list.append(convert_model_to_dict(objects[i], ignore_attr_with_prefix))
    return to_dict_list


def deserialize_post_data(post):
    raw_data = post.get('data')
    if raw_data is None:
        return None
    else:
        return json.loads(raw_data)


def get_login_user(request):
    if hasattr(request, 'user') and request.user is not None and not request.user.is_anonymous():
        return True, request.user
    else:
        return False, None


def send_email_multi_alternatives_with_template(
        from_email, to_list,
        subject, text_template,
        context, html_template=None, headers=None):
    # revert the changes of a Django patch
    # https://code.djangoproject.com/attachment/ticket/11212/0001-Ticket-11212-default-to-7bit-email.patch
    from email import charset
    charset.add_charset('utf-8', charset.SHORTEST, charset.QP, 'utf-8')
    text_content = template_loader.render_to_string(
        text_template, context)
    mail = EmailMultiAlternatives(subject, text_content, from_email, list(to_list), headers=headers)
    if html_template:
        html_content = template_loader.render_to_string(
            html_template, context)
        mail.attach_alternative(html_content, 'text/html')
    mail.send()
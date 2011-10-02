from piston.emitters import Emitter
from django.utils import simplejson
from django.core.serializers.json import DateTimeAwareJSONEncoder

import datetime
import decimal
from django.utils import datetime_safe
from django.utils import simplejson

from pinax.apps.account.models import Account
from timezones.utils import localtime_for_timezone


class TimezoneAwareJSONEncoder(simplejson.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """

    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TimezoneAwareJSONEncoder, self).__init__(*args, **kwargs)
        if user and user.is_authenticated():
            account = Account.objects.get_for_user(user, None)
            self.timezone = account.timezone

    def default(self, o):
        if isinstance(o, datetime.datetime):
            d = datetime_safe.new_datetime(o)
            if self.timezone:
                d = localtime_for_timezone(d, self.timezone)
            return d.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(o, datetime.date):
            d = datetime_safe.new_date(o)
            return d.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        else:
            return super(DjangoJSONEncoder, self).default(o)


class TimeZoneEmitter(Emitter):
    """
    JSON emitter, understands timestamps and timezones.
    """
    def render(self, request):
        cb = request.GET.get('callback')
        u = request.user
        seria = simplejson.dumps(self.construct(), cls=TimezoneAwareJSONEncoder,
            ensure_ascii=False, indent=4, user=u)

        # Callback
        if cb:
            return '%s(%s)' % (cb, seria)
        return seria

Emitter.register('json', TimeZoneEmitter, 'application/json; charset=utf-8')

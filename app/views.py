from annoying.decorators import ajax_request, render_to
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import QueryDict
from django.http.response import HttpResponseBadRequest, HttpResponseNotAllowed, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import TemplateDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from app.models import Log, Purchase, Event, MyUser, BudgetUnit, gen_access_token


class BadRequestException(Exception): pass
class UnsupportedException(Exception): pass

@ajax_request
def json_handler(request, data):
    if isinstance(data, models.Model):
        return data.as_dict()
    elif isinstance(data, dict):
        return data
    else:
        return {'result': 1, 'data': list(map(lambda x: x.as_dict(), data))}

    
def process_request(request, method, model, id=None):

    if id is not None:
        obj = get_object_or_404(model, pk=id)

    if method == "GET":
        if id is not None:
            return obj
        return model.objects.all()

    data = QueryDict(request.body)

    if method == "POST":
        assert id is not None, "id expected"
        obj.populate_model_and_save(data)
        return obj

    if method == "PUT":
        assert id is None, "unexpected id"
        obj = model()
        obj.populate_model_and_save(data)
        return {"id": obj.id, "result": 1}

    assert method == "DELETE", "Expected DELETE method"
    obj.delete()

    return {"result": 1}


@render_to("log.html")
def show_log(request):
    return {'data': Log.objects.extra(order_by=['-date'])}


@render_to("event.html")
def event(request, id):
    event = Event.objects.get(pk=id)

    eaten_by_id = dict()
    wasted_by_id = dict()

    for p in event.participants.all():
        for u in p.users.all():
            eaten_by_id[u.id] = 0
            wasted_by_id[u.id] = 0

    for p in event.purchases.all():
        max1 = max(1, len(list(p.shared.all())))
        avg_cost = int(round(p.cost / max1))
        wasted_by_id[p.owner.id] += p.cost
        for s in p.shared.all():
            eaten_by_id[s.id] += avg_cost

    eaten_by_id_bu = dict()
    wasted_by_id_bu = dict()
    summary = list()

    for p in event.participants.all():
        eaten_by_id_bu[p.id] = 0
        wasted_by_id_bu[p.id] = 0
        users = []
        for u in p.users.all():
            user = {
                'model': u,
                'eaten': eaten_by_id[u.id],
                'wasted': wasted_by_id[u.id],
                'delta': eaten_by_id[u.id] - wasted_by_id[u.id]
            }
            eaten_by_id_bu[p.id] += eaten_by_id[u.id]
            wasted_by_id_bu[p.id] += wasted_by_id[u.id]
            users.append(user)

        item = {
            'model': p,
            'eaten': eaten_by_id_bu[p.id],
            'wasted': wasted_by_id_bu[p.id],
            'delta': eaten_by_id_bu[p.id] - wasted_by_id_bu[p.id],
            'users': users if len(users) > 1 else []
        }

        item['d'] = item['delta']

        summary.append(item)

    debtors = sorted(filter(lambda x: x['delta'] > 0, summary), cmp=lambda x, y: y['d'] - x['d'])
    creditors = sorted(filter(lambda x: x['delta'] < 0, summary), cmp=lambda x, y: x['d'] - y['d'])

    i = 0
    j = 0

    offers = []

    while i < len(debtors) and j < len(creditors):
        sum = min(abs(debtors[i]['d']), abs(creditors[j]['d']))
        debtors[i]['d'] -= sum
        creditors[j]['d'] += sum

        offers.append({'from': debtors[i]['model'], 'to': creditors[j]['model'], 'sum': sum})
        if debtors[i]['d'] == 0:
            i += 1
        if creditors[j]['d'] == 0:
            j += 1

    return {'event': event, 'summary': summary, 'offers': offers}


@ajax_request
@csrf_exempt
def login(request):
    username = request.GET['username']
    password = request.GET['password']

    user = auth.authenticate(username=username, password=password)
    if user is not None:
        auth.login(request, user)
        user.shekel.access_token = gen_access_token()
        user.shekel.save()
        return {'result':  1, 'access_token': user.shekel.access_token}

    return {'result': 0}

@login_required
@csrf_exempt
def request_handler(request, model_name, **kwargs):
    accept_type = request.META.get("HTTP_ACCEPT")
    method = request.META["REQUEST_METHOD"]
    try:
        log = Log()
        log.method = method
        log.url = request.get_full_path()
        log.accept_type = accept_type if accept_type is not None else "<accept-type>"
        log.save()

        models = {
            "event": Event,
            "purchase": Purchase,
            "user": MyUser,
            "unit": BudgetUnit
        }

        if model_name not in models:
            raise Http404()
        model = models[model_name]
        data = process_request(request, method=method, model=model, **kwargs)

        return json_handler(request, data)

    except (UnsupportedException, TemplateDoesNotExist) as e:
        return HttpResponseNotAllowed(str(e))
    except (BadRequestException, AssertionError, ValueError) as e:
        return HttpResponseBadRequest(str(e))
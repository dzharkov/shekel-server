import binascii
import os
from django.contrib.auth.models import User
from django.db import models
from django.utils.dateparse import parse_date


def ids(items):
    return map(lambda x: x.id, items.all())

ACCESS_TOKEN_LENGTH = 32


def gen_access_token():
    return binascii.b2a_hex(os.urandom(ACCESS_TOKEN_LENGTH / 2))


class MyUser(models.Model):
    access_token = models.CharField(
        max_length=ACCESS_TOKEN_LENGTH,
        unique=True, null=True, blank=True
    )
    user = models.OneToOneField(User, related_name="shekel")

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.user.first_name
        }

    def __unicode__(self):
        return unicode(self.user.first_name)


class BudgetUnit(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    users = models.ManyToManyField(MyUser)

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'user_ids': ids(self.users)
        }

    def __unicode__(self):
        if self.name is not None and len(self.name) > 0:
            return self.name

        return " / ".join(list(map(lambda x: unicode(x), self.users.all())))

class Event(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()

    participants = models.ManyToManyField(BudgetUnit)

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "date": self.date.strftime("%Y-%m-%d"),
            "participant_ids": ids(self.participants),
            "purchase_ids": ids(self.purchases)
        }

    def populate_model_and_save(self, data):
        try:
            self.name = data["name"]
            self.date = parse_date(data["date"])

            unit_ids = map(lambda id: BudgetUnit.objects.get(int(id)), data["unit_ids"].split(","))
            self.shared.clear()
            self.shared.add(*unit_ids)
            self.save()
        except (KeyError, ValueError) as e:
            raise ValueError(e)


    def full_name(self):
        return self.name + " " + self.date.strftime("%Y-%m-%d")

    def __unicode__(self):
        return self.full_name()


class Purchase(models.Model):
    owner = models.ForeignKey(MyUser)
    name = models.CharField(max_length=100)
    party = models.ForeignKey(Event, related_name="purchases")

    cost = models.IntegerField()
    shared = models.ManyToManyField(MyUser, related_name="q")

    def as_dict(self):
        return {
            "id": self.id,
            "party_id": self.party_id,
            "owner_id   ": self.owner_id,
            "name": self.name,
            "cost": self.cost,
            "shared_ids": ids(self.shared)
        }

    def populate_model_and_save(self, data):
        try:
            self.name = data["name"]
            self.party_id = int(data["party_id"])
            self.cost = int(data["cost"])

            shared_ids = map(lambda id: MyUser.objects.get(int(id)), data["shared_ids"].split(","))
            self.shared.clear()
            self.shared.add(*shared_ids)
            self.save()
        except (KeyError, ValueError) as e:
            raise ValueError(e)

    def __unicode__(self):
        return self.name + "(" + str(self.cost) + ")"

class Log(models.Model):
    date = models.DateTimeField(auto_now=True)
    accept_type = models.CharField(max_length=100)
    method = models.CharField(max_length=10)
    url = models.CharField(max_length=100)

    def as_dict(self):
        return {
            "date": self.date,
            "accept_type": self.accept_type,
            "method": self.method,
            "url": self.url
        }

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20150823_1232'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='owner',
            field=models.ForeignKey(default=2, to='app.MyUser'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='purchase',
            name='shared',
            field=models.ManyToManyField(related_name='q', to='app.MyUser'),
            preserve_default=True,
        ),
    ]

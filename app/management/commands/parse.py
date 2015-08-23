from threading import Thread, BoundedSemaphore
import urllib
import re
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        main = 'http://www.justdogbreeds.com/dog-breeds.html'

        s = "\n".join(urllib.urlopen(main).readlines())
        m = re.findall(r'=([^=]*)\s+class=thumblink', s)




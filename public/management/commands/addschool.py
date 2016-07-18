from django.core.management.base import BaseCommand

from public.models import School


class Command(BaseCommand):

    help = 'Add a school'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)
        parser.add_argument('city', type=str)

    def handle(self, *args, **options):
        school = School(name=options['name'], city=options['city'])
        school.save()

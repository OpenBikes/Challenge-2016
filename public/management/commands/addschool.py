from django.core.management.base import BaseCommand

from public.models import Curriculum


class Command(BaseCommand):

    help = 'Add a curriculum'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)
        parser.add_argument('school', type=str)

    def handle(self, *args, **options):
        curriculum = Curriculum(name=options['name'], school=options['school'])
        curriculum.save()

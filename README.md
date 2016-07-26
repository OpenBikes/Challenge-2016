# Challenge

## Development

### Installation

- `pip install -r requirements.txt`
- `python manage.py migrate`
- `python manage.py makemigrations public`
- `python manage.py migrate`

### Workflow

- Run `python manage.py runserver` in the second one


## Running migrations

- Change your models (in `models.py`)
- Run `python manage.py makemigrations` to create migrations for those changes
- Run `python manage.py migrate` to apply those changes to the database

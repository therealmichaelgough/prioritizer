import arrow
from functools import total_ordering
from datetime import timedelta
import datetime
import click
import re
from word2number import w2n

TASK_FILE_NAME = 'tasks.csv'
CALENDAR_FILE_NAME = f'tasks_{arrow.now().date}'
MIN_ESTIMATION_QUANTITY = 20
MIN_ESTIMATION_UNIT = 'minutes'
MAX_ESTIMATION_UNIT = 'years'
MIN_INTERVAL = timedelta(**{MIN_ESTIMATION_UNIT: MIN_ESTIMATION_QUANTITY})
ESTIMATION_PATTERN = re.compile(r'(?P<quantity>((\d+|\d+\/\d+)|[a-zA-Z]+)) +(?P<unit>(days?|min(ute)?s?)|weeks?|years?|hours?|months?|lifetime)')


def parse_quantity(quantity):
    try:
        if quantity == 'a':
            return 1
        try:
            return float(quantity)
        except ValueError:
            try:
                if '/' in quantity:
                    numerator, denominator = quantity.split('/')[0], quantity.split('/')[1]
                    return float(numerator) / float(denominator)
                else:
                    raise
            except:
                raise
    except:
        return Task.extract_quantity_from_words(quantity)


@total_ordering
class Task:
    def _is_valid_operand(self, other):
        return (hasattr(other, "name") and
                hasattr(other, "priority"))

    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.description = kwargs.get('description')
        self.critical = kwargs.get('critical', False)
        self.time_estimate = kwargs.get('time_estimate', MIN_INTERVAL)
        self.remaining_estimate = kwargs.get('remaining_estimate', self.time_estimate)
        self.due_date = kwargs.get('due_date', 'in 1 year')
        self.dependencies = [Task(**dependency.__dict__) for dependency in kwargs.get('dependencies', [])]
        self.priority = self.assign_priority()

    def __repr__(self):
        return f'\nTask: {self.name}\n\tDescription: {self.description}\n\tDue: {self.due_date}\n\tTime Remaining: {self.remaining_estimate}'

    def __str__(self):
        return self.__repr__()

    def assign_priority(self):
        relative_remaining_time = float((self.due_date.ceil('day') - arrow.now()) / self.remaining_estimate)
        critical_modifier = {True: -1, False: 1}[self.critical]
        if relative_remaining_time <= 0:
            critical_modifier *= -1
        return critical_modifier * relative_remaining_time

    def __eq__(self, other):
        return all([self.name == other.name,
                    self.priority == other.priority
                    ])

    def __lt__(self, other):
        if self in other.dependencies:
            return True
        else:
            return self.priority < other.priority

    @classmethod
    def parse_time_delta(cls, task_estimation_string):
        match = ESTIMATION_PATTERN.match(task_estimation_string)
        if not match:
            quantity = MIN_ESTIMATION_QUANTITY
        else:
            quantity = match.groupdict().get('quantity', MIN_ESTIMATION_QUANTITY)
            quantity = parse_quantity(quantity)

        unit = match.groupdict().get('unit', MIN_ESTIMATION_UNIT)

        if unit in ['minutes', 'hours', 'days', 'weeks', 'months', 'years']:
            pass
        elif unit in ['minute', 'hour', 'day', 'week', 'month', 'year']:
            unit = f'{unit}s'
        elif unit in ['min', 'mins']:
            unit = 'minutes'
        elif unit in ['lifetime']:
            return timedelta(days=365 * 40)  # tick tick tick tick
        else:
            unit = MIN_ESTIMATION_UNIT

        return timedelta(**{unit: quantity})

    @classmethod
    def parse_due_date(cls, task_due_date_string):
        if task_due_date_string in ['today', 'now']:
            return arrow.get()
        elif task_due_date_string in ['tomorrow']:
            return arrow.get().shift(days=1).ceil('day')
        try:
            try:
                return arrow.get(task_due_date_string, 'MM-DD-YYYY')
            except:
                return arrow.get(f'{task_due_date_string}-{arrow.get().year}', 'MM-DD-YYYY')
        except:
            try:
                for word_number in w2n.american_number_system.keys():
                    if word_number in task_due_date_string:
                        task_due_date_string = task_due_date_string.replace(word_number, str(w2n.american_number_system[word_number]))
                return arrow.get().dehumanize(task_due_date_string)
            except:
                return None

    @classmethod
    def extract_quantity_from_words(cls, quantity):
        try:
            return w2n.word2number(quantity)
        except:
            return MIN_ESTIMATION_QUANTITY


class Prioritizer:
    def __init__(self, tasks):
        self.queue = tasks if tasks else []

    def insert(self, tasks):
        for task in tasks:
            if task.__class__ is Task:
                self.queue.append(task)

    def output_calendar(self, filename):
        pass

    def output_csv(self, filename):
        pass

    def sorted_tasks(self):
        return sorted(self.queue)

    def print_sorted_tasks(self):
        click.clear()
        print(f'\n{"-"*80}\n'.join([f'{str(t)}\n' for t in self.sorted_tasks()]))


class CliParser:
    @staticmethod
    def new_task_from_prompt():
        task_name = click.prompt("What do you need to do? ")
        if not task_name or task_name in ["nothing", "done", "\n"]:
            return None
        task_description = click.prompt("Short Description: ")
        task_critical = {"yes": True, "no":False}[click.prompt("Is this a critical task? ",
                                     type=click.Choice(["yes", "no"], case_sensitive=False),
                                     show_choices=True)]
        task_estimation = click.prompt("How long will this take? e.g. 'one week' | 1/2 day | 20 mins | 1 hour ")
        task_due_date = click.prompt("When is it due? e.g. 'tomorrow' | 'in 8 days' | 12-23-2021 | 12-23 | today")
        return {
            "name": task_name,
            "description": task_description,
            "critical": task_critical,
            "time_estimate": Task.parse_time_delta(task_estimation),
            "due_date": Task.parse_due_date(task_due_date)
        }

    @staticmethod
    def tasks_from_prompt(existing_tasks):
        add_new_task = True
        #existing_tasks_display = "\n\t*".join(existing_tasks)
        #click.echo(f'Here are your existing tasks: {[Task(t) for t in existing_tasks]}')
        while add_new_task:
            add_new_task = CliParser.new_task_from_prompt()
            if add_new_task:
                yield add_new_task
            else:
                return


def gather_instructions(existing_tasks):
    new_tasks = []
    for t in CliParser.tasks_from_prompt(existing_tasks):
        new_tasks.append(Task(**t))

    return new_tasks


def load_tasks_from_file(filename):
    tasks = []
    return tasks


def main():
    existing_tasks = load_tasks_from_file(TASK_FILE_NAME)
    prioritizer = Prioritizer(existing_tasks)
    new_tasks = gather_instructions(prioritizer.sorted_tasks())
    prioritizer.insert(new_tasks)
    prioritizer.output_calendar(CALENDAR_FILE_NAME)
    prioritizer.output_csv(TASK_FILE_NAME)
    prioritizer.print_sorted_tasks()


if __name__ == "__main__":
    main()
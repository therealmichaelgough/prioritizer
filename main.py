import arrow
from functools import total_ordering
from datetime import timedelta
import datetime
import click
import re

TASK_FILE_NAME = 'tasks.csv'
CALENDAR_FILE_NAME = f'tasks_{arrow.now().date}'
MIN_INTERVAL = timedelta(minutes=20)
ESTIMATION_PATTERN = re.compile()


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
        self.due_date = kwargs.get('due_date')
        self.dependencies = [Task(**dependency.__dict__) for dependency in kwargs.get('dependencies', [])]
        self.priority = self.assign_priority()

    def assign_priority(self):
        critical = {True: lambda x: -1 * float(x), False: lambda x: 1/float(x)}[self.critical]
        time_cost = float(self.time_estimate / MIN_INTERVAL)
        available_time_cost = float((self.due_date - arrow.now()) / MIN_INTERVAL)
        return critical(time_cost/available_time_cost)

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
        return None


    @classmethod
    def parse_due_date(cls, task_due_date_string):
        try:
            try:
                return arrow.get(task_due_date_string, 'MM-DD-YYYY')
            except:
                return arrow.get(f'{task_due_date_string}-{arrow.get().year}', 'MM-DD-YYYY')
        except:
            try:
                return None
            except:
                return None


class Prioritizer:
    def __init__(self, *tasks):
        self.queue = tasks if tasks else []

    def insert(self, *tasks):
        for task in tasks:
            if type(task) is Task:
                self.queue.append(task)

    def output_calendar(self, filename):
        pass

    def output_csv(self, filename):
        pass

    def sorted_tasks(self):
        return sorted(self.queue)


class CliParser:
    @staticmethod
    @click.command()
    def new_task_from_prompt():
        task_name = click.prompt("What do you need to do? ")
        if not task_name or task_name in ["nothing", "done", "\n"]:
            return False
        task_description = click.prompt("Short Description: ")
        task_critical = {"yes": True, "no":False}[click.prompt("Is this a critical task? ",
                                     type=click.Choice(["yes", "no"], case_sensitive=False),
                                     show_choices=True)]
        task_estimation = click.prompt("How long will this take? ")
        task_due_date = click.prompt("When is it due? ")
        return {
            "name": task_name,
            "description": task_description,
            "critical": task_critical,
            "time_estimate": Task.parse_time_delta(task_estimation),
            "due_date": Task.parse_due_date(task_due_date)
        }


    @staticmethod
    @click.command()
    def tasks_from_prompt(existing_tasks, new_tasks):
        add_new_task = True
        existing_tasks_display = "\n\t*".join(existing_tasks)
        click.echo(f'Here are your existing tasks: {existing_tasks_display}')
        while add_new_task:
            add_new_task = CliParser.new_task_from_prompt()
            yield add_new_task


def gather_instructions(existing_tasks):
    new_tasks = []
    for t in CliParser.tasks_from_prompt(existing_tasks, new_tasks):
        new_tasks.append(Task(t))

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

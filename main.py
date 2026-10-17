import json
from datetime import datetime
from pathlib import Path

import questionary

TASKS_FILE = Path(__file__).with_name("todolist.json")
DEADLINE_INPUT_FORMAT = "%Y-%m-%d %H:%M"
DEADLINE_DISPLAY_FORMAT = "%A, %B %d, %Y at %I:%M %p"
CANCEL = "cancel"


# --- Storage -----------------------------------------------------------------

def load_tasks():
    """Return the list of tasks, or None if the file can't be read."""
    try:
        text = TASKS_FILE.read_text(encoding="utf-8").strip()
        tasks = json.loads(text) if text else []
    except FileNotFoundError:
        return []
    except (OSError, ValueError) as error:  # ValueError covers bad JSON/encoding
        print(f"Error reading tasks: {error}")
        return None

    if not isinstance(tasks, list) or not all(isinstance(t, dict) for t in tasks):
        print("Error reading tasks: expected a JSON list of tasks.")
        return None
    return tasks


def save_tasks(tasks):
    try:
        TASKS_FILE.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"Error saving tasks: {error}")
        return False
    return True


# --- Task logic (no prompts, no printing) -----------------------------------

def find_duplicate(tasks, name):
    return next(
        (task for task in tasks if task["name"].casefold() == name.casefold()),
        None,
    )


def add_task(tasks, name, deadline=None):
    """Append a new task to `tasks` and return it."""
    task = {
        "id": max((task["id"] for task in tasks), default=0) + 1,
        "name": name,
        "deadline": deadline.isoformat(timespec="minutes") if deadline else None,
    }
    tasks.append(task)
    return task


def remove_task(tasks, task_id):
    """Remove the task with this ID. Return True if it existed."""
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            del tasks[index]
            return True
    return False


def parse_deadline(value):
    """Parse 'YYYY-MM-DD HH:MM'. Raise ValueError if invalid or in the past."""
    try:
        deadline = datetime.strptime(value.strip(), DEADLINE_INPUT_FORMAT)
    except ValueError:
        raise ValueError("Use YYYY-MM-DD HH:MM, e.g. 2030-10-25 14:30.") from None
    if deadline < datetime.now():
        raise ValueError("The deadline must be in the future.")
    return deadline


def format_task(task):
    deadline = task.get("deadline")
    if deadline:
        deadline = datetime.fromisoformat(deadline).strftime(DEADLINE_DISPLAY_FORMAT)
    else:
        deadline = "No deadline"
    return f"ID: {task['id']} | {task['name']} | Deadline: {deadline}"


# --- Menu actions (prompts and printing) ------------------------------------

def show_tasks():
    tasks = load_tasks()
    if tasks is None:
        return
    if not tasks:
        print("No tasks found.")
        return
    for task in tasks:
        print(format_task(task))


def _validate_deadline(value):
    try:
        parse_deadline(value)
    except ValueError as error:
        return str(error)
    return True


def prompt_add_task():
    name = questionary.text("Task name:").ask()
    if name is None:  # Ctrl+C
        return
    name = name.strip()
    if not name:
        print("Task name cannot be empty.")
        return

    tasks = load_tasks()
    if tasks is None:
        return

    duplicate = find_duplicate(tasks, name)
    if duplicate:
        print(f"Task already exists: {duplicate['name']}")
        if not questionary.confirm("Add it anyway?", default=False).ask():
            print("Task was not added.")
            return

    has_deadline = questionary.confirm("Do you have a deadline for it?", default=False).ask()
    if has_deadline is None:
        return

    deadline = None
    if has_deadline:
        value = questionary.text(
            "Deadline (YYYY-MM-DD HH:MM):", validate=_validate_deadline
        ).ask()
        if value is None:
            return
        deadline = parse_deadline(value)

    task = add_task(tasks, name, deadline)
    if save_tasks(tasks):
        print(f"Task added with ID {task['id']}.")


def prompt_remove_task():
    tasks = load_tasks()
    if tasks is None:
        return
    if not tasks:
        print("No tasks found.")
        return

    choices = [questionary.Choice(title=format_task(t), value=t["id"]) for t in tasks]
    choices.append(questionary.Choice(title="Cancel", value=CANCEL))
    task_id = questionary.select("Which task would you like to remove?", choices=choices).ask()
    if task_id is None or task_id == CANCEL:
        print("Removal cancelled.")
        return

    if remove_task(tasks, task_id) and save_tasks(tasks):
        print(f"Task {task_id} removed.")


def main():
    while True:
        choice = questionary.select(
            "What would you like to do?",
            choices=["Add Task", "Show Tasks", "Remove a Task", "Quit"],
        ).ask()

        if choice is None or choice == "Quit":  # None means Ctrl+C
            print("Goodbye!")
            print("Your tasks are:")
            show_tasks()
            return
        if choice == "Add Task":
            prompt_add_task()
        elif choice == "Show Tasks":
            show_tasks()
        elif choice == "Remove a Task":
            prompt_remove_task()


if __name__ == "__main__":
    main()

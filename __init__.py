import json
from datetime import datetime
from pathlib import Path

import questionary

file_path = Path(__file__).with_name("todolist.json")


def _load_tasks():
  try:
    contents = file_path.read_text(encoding="utf-8")
  except FileNotFoundError:
    return []
  except OSError as error:
    print(f"Error reading tasks: {error}")
    return None

  if not contents.strip():
    return []

  try:
    tasks = json.loads(contents)
  except json.JSONDecodeError as error:
    print(f"Error reading tasks: invalid JSON ({error}).")
    return None

  if not isinstance(tasks, list) or any(not isinstance(task, dict) for task in tasks):
    print("Error reading tasks: expected a JSON list of tasks.")
    return None
  return tasks


def _save_tasks(tasks):
  try:
    file_path.write_text(json.dumps(tasks, indent=2) + "\n", encoding="utf-8")
  except OSError as error:
    print(f"Error saving tasks: {error}")
    return False
  return True


def add_task(task_name, deadline=None):
  if not task_name or not task_name.strip():
    print("Task name cannot be empty.")
    return

  tasks = _load_tasks()
  if tasks is None:
    return

  task_name = task_name.strip()
  duplicate = next(
    (
      task for task in tasks
      if isinstance(task.get("name"), str)
      and task["name"].strip().casefold() == task_name.casefold()
    ),
    None,
  )
  if duplicate:
    print(f"Task already exists: {duplicate['name']}")
    if not questionary.confirm("Add it anyway?", default=False).ask():
      print("Task was not added.")
      return

  existing_ids = [
    task["id"] for task in tasks
    if isinstance(task.get("id"), int) and not isinstance(task.get("id"), bool)
  ]
  task_id = max(existing_ids, default=0) + 1
  task_deadline = deadline.isoformat(timespec="minutes") if isinstance(deadline, datetime) else None
  tasks.append({"id": task_id, "name": task_name.strip(), "deadline": task_deadline})

  if _save_tasks(tasks):
    print(f"Task added with ID {task_id}.")

def show_tasks():
  tasks = _load_tasks()
  if tasks is None:
    return
  if not tasks:
    print("No tasks found.")
    return

  for task in tasks:
    deadline = task.get("deadline")
    if deadline:
      try:
        deadline = datetime.fromisoformat(deadline).strftime("%A, %B %d, %Y at %I:%M %p")
      except (TypeError, ValueError):
        deadline = str(deadline)
    else:
      deadline = "No deadline"
    print(f"ID: {task.get('id', '?')} | {task.get('name', '(unnamed task)')} | Deadline: {deadline}")

def remove_task(task_id):
  if task_id is None or not str(task_id).strip():
    print("Removal cancelled.")
    return

  try:
    task_id = int(task_id)
  except (TypeError, ValueError):
    print("Please enter a valid task ID.")
    return

  tasks = _load_tasks()
  if tasks is None:
    return

  for index, task in enumerate(tasks):
    if task.get("id") == task_id:
      del tasks[index]
      if _save_tasks(tasks):
        print(f"Task {task_id} removed.")
      return

  print(f"No task found with ID {task_id}.")


def _parse_deadline(value):
  now = datetime.now()
  for year in range(now.year, now.year + 9):
    try:
      deadline = datetime.strptime(f"{year}-{value}", "%Y-%m-%d %H:%M")
    except ValueError:
      continue
    if deadline >= now:
      return deadline
  raise ValueError("Please use MM-DD HH:MM and enter a valid upcoming date.")


def main():
  while True:
    choice = questionary.select(
        "What would you like to do?",
        choices=[
            "Add Task",
            "Show Tasks",
            "Remove a Task",
            "Quit"
        ]
    ).ask()

    if choice == "Quit":
      print("Goodbye!")
      print("Your tasks are:")
      show_tasks()
      return

    if choice == "Add Task":
      task_name = input("What task would you like to add?\nTask Name: ")
      has_deadline = questionary.confirm("Do you have a deadline for it?", default=False).ask()
      if has_deadline is None:
        continue

      if has_deadline:
        deadline_input = input("Enter date and time (MM-DD HH:MM): ")
        try:
          deadline = _parse_deadline(deadline_input)
        except ValueError:
          print("Error: Please use MM-DD HH:MM and enter a valid upcoming date (e.g., 10-25 14:30).")
          continue
        print("Deadline saved successfully:", deadline.strftime("%A, %B %d, %Y at %I:%M %p"))
        add_task(task_name, deadline=deadline)
      else:
        add_task(task_name)

    elif choice == "Show Tasks":
      show_tasks()

    elif choice == "Remove a Task":
      print("What task would you like to remove?\nDisplaying tasks:")
      show_tasks()
      task_id = input("What task to delete?\nPress Enter to cancel\nTask ID: ")
      remove_task(task_id)


if __name__ == "__main__":
  main()
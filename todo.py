# todo.py
# A simple command-line to-do list app.
# Tasks are saved to a file (tasks.txt) so they persist between runs.

import os

TASKS_FILE = "tasks.txt"  # the file where tasks are stored


# ── File helpers ──────────────────────────────────────────────────────────────

def load_tasks():
    """Read tasks from the file and return them as a list."""
    # If the file doesn't exist yet, return an empty list
    if not os.path.exists(TASKS_FILE):
        return []

    with open(TASKS_FILE, "r") as f:
        # Each line is one task; strip() removes the newline character at the end
        tasks = [line.strip() for line in f.readlines()]

    # Filter out any blank lines
    return [task for task in tasks if task]


def save_tasks(tasks):
    """Write the current list of tasks to the file."""
    with open(TASKS_FILE, "w") as f:
        for task in tasks:
            f.write(task + "\n")


# ── Display ───────────────────────────────────────────────────────────────────

def show_tasks(tasks):
    """Print all tasks with a numbered list."""
    print()
    if not tasks:
        print("  No tasks yet!")
    else:
        for i, task in enumerate(tasks, start=1):  # start=1 → numbers begin at 1
            print(f"  {i}. {task}")
    print()


# ── Actions ───────────────────────────────────────────────────────────────────

def add_task(tasks):
    """Ask the user for a new task and add it to the list."""
    task = input("Enter the task: ").strip()
    if task:
        tasks.append(task)
        save_tasks(tasks)
        print(f'  Added: "{task}"')
    else:
        print("  Nothing entered — task not added.")


def delete_task(tasks):
    """Ask the user which task to delete, then remove it."""
    show_tasks(tasks)
    if not tasks:
        return

    try:
        number = int(input("Enter task number to delete: "))
        if 1 <= number <= len(tasks):
            removed = tasks.pop(number - 1)  # lists are 0-indexed, so subtract 1
            save_tasks(tasks)
            print(f'  Deleted: "{removed}"')
        else:
            print("  That number is out of range.")
    except ValueError:
        # The user typed something that isn't a number
        print("  Please enter a valid number.")


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    """Run the app — show a menu and respond to the user's choice."""
    print("=== To-Do List ===")

    tasks = load_tasks()  # load any saved tasks at startup

    while True:  # keep looping until the user chooses to quit
        print("What would you like to do?")
        print("  1 — View tasks")
        print("  2 — Add a task")
        print("  3 — Delete a task")
        print("  4 — Quit")

        choice = input("Choose (1-4): ").strip()

        if choice == "1":
            show_tasks(tasks)
        elif choice == "2":
            add_task(tasks)
        elif choice == "3":
            delete_task(tasks)
        elif choice == "4":
            print("Goodbye!")
            break  # exit the while loop → program ends
        else:
            print("  Invalid choice, please enter 1, 2, 3, or 4.\n")


# This block only runs when you execute the file directly (not when imported).
if __name__ == "__main__":
    main()

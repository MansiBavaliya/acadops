
from datetime import date

from academic_state import AcademicState


class ConflictEngine:

    def detect_conflicts(self, state: AcademicState):
        """Detect urgent tasks competing for today's study time."""

        tasks = state.get_active_tasks()
        conflicts = []

        # Sort tasks by deadline and priority.
        tasks = sorted(
            tasks,
            key=lambda task: (task.deadline, task.priority)
        )

        available_hours = state.available_hours_today
        accumulated_hours = 0.0
        seen_tasks = set()

        for task in tasks:
            task_remaining = task.remaining_hours

            if task_remaining <= 0:
                continue

            # Avoid reporting the same task more than once.
            task_key = (task.title, str(task.deadline))
            if task_key in seen_tasks:
                continue

            seen_tasks.add(task_key)
            accumulated_hours += task_remaining

            try:
                deadline_date = date.fromisoformat(
                    str(task.deadline)[:10]
                )
                days_remaining = (
                    deadline_date - date.today()
                ).days
            except (ValueError, TypeError):
                continue

            # Only flag overdue tasks and tasks due within 7 days.
            if (
                accumulated_hours > available_hours
                and days_remaining <= 7
            ):
                conflicts.append({
                    "task": task.title,
                    "deadline": task.deadline,
                    "estimated_hours": task.estimated_hours,
                    "remaining_hours": task_remaining,
                    "available_hours": available_hours,
                    "conflict": "TIME_CONFLICT",
                    "message": (
                        f"{task.title} competes for today's limited "
                        f"study time. Its remaining workload, together "
                        f"with earlier-deadline tasks, exceeds the "
                        f"available capacity of {available_hours} hours."
                    )
                })

        return conflicts


if __name__ == "__main__":
    state = AcademicState(
        student_name="Test Student",
        available_hours_today=5
    )

    state.add_task(
        title="AI Assignment",
        deadline="2026-10-07",
        estimated_hours=2,
        priority=1
    )

    state.add_task(
        title="AI Exam Preparation",
        deadline="2026-10-09",
        estimated_hours=4,
        priority=2
    )

    state.add_task(
        title="Group Presentation",
        deadline="2026-10-13",
        estimated_hours=3,
        priority=3
    )

    engine = ConflictEngine()
    conflicts = engine.detect_conflicts(state)

    print("\n=== AcadOps Conflict Detection ===")

    if not conflicts:
        print("No major time conflicts detected.")
    else:
        for conflict in conflicts:
            print(f"\n⚠️ {conflict['conflict']}")
            print(f"Task: {conflict['task']}")
            print(f"Deadline: {conflict['deadline']}")
            print(f"Remaining hours: {conflict['remaining_hours']}")
            print(f"Available hours: {conflict['available_hours']}")
            print(f"Message: {conflict['message']}")

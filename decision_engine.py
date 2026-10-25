
from datetime import date


class DecisionEngine:

    def get_next_action(self, state):
        """Select the best active task using deadline, priority, and workload."""

        active_tasks = [
            task
            for task in state.get_active_tasks()
            if task.remaining_hours > 0
        ]

        if not active_tasks:
            return {
                "next_action": None,
                "message": "No active academic tasks."
            }

        today = date.today()
        scored_tasks = []

        for task in active_tasks:
            try:
                deadline = date.fromisoformat(task.deadline)
                days_remaining = (deadline - today).days
            except (ValueError, TypeError):
                days_remaining = None

            remaining_hours = max(0, float(task.remaining_hours or 0))

            try:
                priority = int(task.priority)
            except (ValueError, TypeError):
                priority = 3

            priority = max(1, min(priority, 5))

            # Deadline pressure increases as the deadline approaches.
            if days_remaining is None:
                deadline_pressure = 0
            elif days_remaining < 0:
                deadline_pressure = min(30 + abs(days_remaining), 45)
            elif days_remaining == 0:
                deadline_pressure = 28
            elif days_remaining == 1:
                deadline_pressure = 23
            elif days_remaining <= 3:
                deadline_pressure = 18
            elif days_remaining <= 7:
                deadline_pressure = 12
            elif days_remaining <= 14:
                deadline_pressure = 7
            else:
                deadline_pressure = 3

            priority_pressure = (6 - priority) * 3
            workload_pressure = min(remaining_hours, 5) * 2

            urgency_score = (
                deadline_pressure
                + priority_pressure
                + workload_pressure
            )

            scored_tasks.append({
                "task": task,
                "urgency_score": urgency_score,
                "days_remaining": days_remaining,
                "remaining_hours": remaining_hours,
                "priority": priority
            })

        # Rank by urgency first, then deadline, priority, and workload.
        scored_tasks.sort(
            key=lambda item: (
                -item["urgency_score"],
                item["days_remaining"]
                if item["days_remaining"] is not None
                else float("inf"),
                item["priority"],
                -item["remaining_hours"]
            )
        )

        selected = scored_tasks[0]
        task = selected["task"]
        days_remaining = selected["days_remaining"]
        remaining_hours = selected["remaining_hours"]

        if days_remaining is None:
            reason = (
                f"{task.title} is recommended based on its priority "
                "and remaining workload. Its deadline could not be validated."
            )
        elif days_remaining < 0:
            reason = (
                f"{task.title} is overdue by {abs(days_remaining)} day(s) "
                f"and has {remaining_hours} hour(s) of work remaining."
            )
        elif days_remaining == 0:
            reason = (
                f"{task.title} is due today and has "
                f"{remaining_hours} hour(s) of work remaining."
            )
        elif days_remaining == 1:
            reason = (
                f"{task.title} is due tomorrow and has "
                f"{remaining_hours} hour(s) of work remaining."
            )
        else:
            reason = (
                f"{task.title} is recommended based on its deadline, "
                f"priority, and remaining workload. "
                f"{remaining_hours} hour(s) of work remain."
            )

        return {
            "next_action": task.title,
            "urgency_score": round(selected["urgency_score"], 2),
            "estimated_hours": task.estimated_hours,
            "remaining_hours": remaining_hours,
            "progress": task.progress,
            "deadline": task.deadline,
            "days_remaining": days_remaining,
            "reason": reason
        }


from datetime import date


class RiskEngine:

    def analyze(self, state):
        """Analyze remaining workload and individual task deadlines."""

        today = date.today()

        # Include only active tasks that still have work remaining.
        active_tasks = [
            task
            for task in state.get_active_tasks()
            if task.remaining_hours > 0
        ]

        total_workload = sum(
            float(task.remaining_hours)
            for task in active_tasks
        )

        available_hours = max(
            0.0,
            float(state.available_hours_today)
        )

        # ------------------------------------------
        # WORKLOAD RISK
        # ------------------------------------------

        if total_workload == 0:
            workload_ratio = 0.0
        elif available_hours == 0:
            workload_ratio = float("inf")
        else:
            workload_ratio = total_workload / available_hours

        if total_workload == 0:
            workload_level = "ON TRACK"
            score = 0
            message = "All academic tasks are completed."

        elif workload_ratio > 3:
            workload_level = "CRITICAL"
            score = 100
            message = (
                "Your remaining workload is more than "
                "three times your available study capacity."
            )

        elif workload_ratio > 2:
            workload_level = "HIGH RISK"
            score = 80
            message = (
                "Your remaining workload is more than "
                "twice your available study capacity."
            )

        elif workload_ratio > 1:
            workload_level = "AT RISK"
            score = 60
            message = (
                "Your remaining workload exceeds "
                "your available study capacity."
            )

        else:
            workload_level = "ON TRACK"
            score = 20
            message = (
                "Your remaining workload fits within "
                "your available study capacity."
            )

        # ------------------------------------------
        # DEADLINE RISKS
        # ------------------------------------------

        deadline_risks = []

        for task in active_tasks:
            try:
                deadline = date.fromisoformat(task.deadline)
                days_remaining = (deadline - today).days

            except (ValueError, TypeError):
                days_remaining = None

            if days_remaining is None:
                risk = "UNKNOWN"
                message = (
                    "The deadline is missing or invalid. "
                    "Check the task deadline."
                )

            elif days_remaining < 0:
                risk = "OVERDUE"
                overdue_days = abs(days_remaining)
                message = (
                    f"This task is overdue by "
                    f"{overdue_days} day(s). "
                    f"{task.remaining_hours} hour(s) of work remain."
                )

            elif days_remaining == 0:
                risk = "CRITICAL"
                message = (
                    "This task is due today. Prioritize "
                    "the remaining work."
                )

            elif days_remaining == 1:
                risk = "CRITICAL"
                message = (
                    "This task is due tomorrow. "
                    "Complete it as soon as possible."
                )

            elif days_remaining <= 3:
                risk = "HIGH"
                message = (
                    "This task is due within three days. "
                    "Plan study time soon."
                )

            elif days_remaining <= 5:
                risk = "MEDIUM"
                message = (
                    "This deadline is approaching. "
                    "Make time for the remaining work."
                )

            else:
                risk = "LOW"
                message = (
                    "There is more time before this deadline, "
                    "but keep making progress."
                )

            deadline_risks.append({
                "task": task.title,
                "days_remaining": days_remaining,
                "risk": risk,
                "estimated_hours": task.estimated_hours,
                "remaining_hours": task.remaining_hours,
                "progress": task.progress,
                "message": message
            })

        # ------------------------------------------
        # RETURN ANALYSIS
        # ------------------------------------------

        return {
            "workload": {
                "level": workload_level,
                "score": score,
                "message": message if not deadline_risks else (
                    "Workload risk calculated from remaining "
                    "tasks and available study time."
                ),
                "total_workload_hours": round(total_workload, 2),
                "available_hours": available_hours,
                "workload_ratio": (
                    round(workload_ratio, 2)
                    if workload_ratio != float("inf")
                    else None
                )
            },
            "deadline_risks": deadline_risks
        }

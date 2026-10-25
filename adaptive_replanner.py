
from academic_state import AcademicState
from decision_engine import DecisionEngine
from risk_engine import RiskEngine
from conflict_engine import ConflictEngine
import database
from datetime import date


class AdaptiveReplanner:
    def __init__(self, state):
        self.state = state
        self.decision_engine = DecisionEngine()
        self.risk_engine = RiskEngine()
        self.conflict_engine = ConflictEngine()

    def _days_remaining(self, task):
        try:
            deadline = date.fromisoformat(str(task.deadline)[:10])
            return (deadline - date.today()).days
        except (ValueError, TypeError):
            return 99999

    def _task_score(self, task, recommended_title):
        days = self._days_remaining(task)
        remaining = float(task.remaining_hours)

        if days < 0:
            deadline_score = min(30 + abs(days), 45)
        elif days == 0:
            deadline_score = 28
        elif days == 1:
            deadline_score = 23
        elif days <= 3:
            deadline_score = 18
        elif days <= 7:
            deadline_score = 12
        elif days <= 14:
            deadline_score = 7
        else:
            deadline_score = 3

        priority_score = max(0, 6 - int(task.priority)) * 3
        workload_score = max(0, 5 - min(remaining, 5)) * 2
        recommended_score = 5 if task.title == recommended_title else 0

        return (
            deadline_score
            + priority_score
            + workload_score
            + recommended_score
        )

    def replan(self):
        analysis = self._analyze_state()

        active_tasks = [
            task
            for task in self.state.get_active_tasks()
            if float(task.remaining_hours) > 0
        ]

        available_hours = max(
            0.0, float(self.state.available_hours_today)
        )

        if not active_tasks:
            result = {
                "status": "complete",
                "message": "All academic tasks are completed.",
                "available_hours": available_hours,
                "remaining_hours": available_hours,
                "next_best_action": {
                    "next_action": None,
                    "message": "No active academic tasks."
                },
                "risk_analysis": analysis["risks"],
                "conflicts": analysis["conflicts"],
                "plan": []
            }

            saved = database.save_academic_plan(result)
            result["saved_plan_id"] = saved["plan_id"]
            return result

        next_action = self.decision_engine.get_next_action(self.state)
        recommended_title = next_action.get("next_action")

        # Prioritize the recommended next action in the allocation.
        sorted_tasks = sorted(
            active_tasks,
            key=lambda task: (
                task.title != recommended_title,
                -self._task_score(task, recommended_title),
                self._days_remaining(task),
                int(task.priority),
                float(task.remaining_hours)
            )
        )

        plan = []
        remaining_hours = available_hours

        for task in sorted_tasks:
            task_remaining = round(float(task.remaining_hours), 2)

            if remaining_hours <= 0:
                plan.append({
                    "task": task.title,
                    "action": "DEFER",
                    "estimated_hours": 0,
                    "remaining_work": task_remaining,
                    "remaining_after_session": task_remaining,
                    "progress": task.progress,
                    "reason": (
                        "Today's study capacity has been used. "
                        "Schedule this task for another session."
                    )
                })
                continue

            allocated_hours = round(
                min(task_remaining, remaining_hours), 2
            )

            remaining_after = round(
                task_remaining - allocated_hours, 2
            )

            if remaining_after <= 0:
                action = "WORK_NOW"
                reason = (
                    "The remaining work fits within today's "
                    "available study time."
                )
                remaining_after = 0
            else:
                action = "PARTIAL_WORK"
                reason = (
                    f"Study for {allocated_hours} hour(s) today; "
                    f"schedule the remaining {remaining_after} "
                    "hour(s) for another session."
                )

            plan.append({
                "task": task.title,
                "action": action,
                "estimated_hours": allocated_hours,
                "remaining_work": task_remaining,
                "remaining_after_session": remaining_after,
                "progress": task.progress,
                "reason": reason
            })

            remaining_hours = round(
                max(0.0, remaining_hours - allocated_hours), 2
            )

        result = {
            "status": "replanned",
            "available_hours": available_hours,
            "remaining_hours": round(remaining_hours, 2),
            "next_best_action": next_action,
            "risk_analysis": analysis["risks"],
            "conflicts": analysis["conflicts"],
            "plan": plan
        }

        saved = database.save_academic_plan(result)
        result["saved_plan_id"] = saved["plan_id"]

        return result

    def _analyze_state(self):
        risks = self.risk_engine.analyze(self.state)
        conflicts = self.conflict_engine.detect_conflicts(self.state)

        return {
            "risks": risks,
            "conflicts": conflicts
        }

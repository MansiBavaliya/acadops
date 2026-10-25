from academic_state import AcademicState
from decision_engine import DecisionEngine
from risk_engine import RiskEngine
from conflict_engine import ConflictEngine


class AcadOpsAgent:

    def __init__(self, state: AcademicState):
        self.state = state
        self.decision_engine = DecisionEngine()
        self.risk_engine = RiskEngine()
        self.conflict_engine = ConflictEngine()

    def analyze(self):

        decision = self.decision_engine.get_next_action(
            self.state
        )

        risks = self.risk_engine.analyze(
            self.state
        )

        conflicts = self.conflict_engine.detect_conflicts(
            self.state
        )

        return {
            "decision": decision,
            "risks": risks,
            "conflicts": conflicts
        }

    def generate_response(self):

        analysis = self.analyze()

        decision = analysis["decision"]
        workload = analysis["risks"]["workload"]
        deadline_risks = analysis["risks"]["deadline_risks"]
        conflicts = analysis["conflicts"]

        response = []

        # Next action
        if "next_action" in decision:

            response.append(
                f"🎯 Your next best action is: "
                f"{decision['next_action']}."
            )

            response.append(
                f"Why: {decision['reason']}"
            )

        # Workload
        response.append(
            f"\n📊 Workload Status: "
            f"{workload['level']}"
        )

        response.append(
            f"You have {workload['total_workload_hours']} "
            f"hours of work but only "
            f"{workload['available_hours']} "
            f"hours available."
        )

        # Deadline risks
        critical_tasks = [
            risk for risk in deadline_risks
            if risk["risk"] == "CRITICAL"
        ]

        if critical_tasks:

            response.append(
                "\n🚨 Critical Deadline Risk:"
            )

            for risk in critical_tasks:

                response.append(
                    f"- {risk['task']} has "
                    f"{risk['days_remaining']} day(s) remaining."
                )

        # Conflicts
        if conflicts:

            response.append(
                "\n⚠️ Time Conflicts Detected:"
            )

            for conflict in conflicts:

                response.append(
                    f"- {conflict['task']} competes "
                    f"for limited study time."
                )

        return "\n".join(response)


if __name__ == "__main__":

    state = AcademicState(
        student_name="Mansi",
        available_hours_today=3
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

    agent = AcadOpsAgent(state)

    print("\n==============================")
    print("       🤖 ACADOPS AGENT")
    print("==============================")

    print(agent.generate_response())
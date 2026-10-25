
import json

from flask import Flask, render_template, request, jsonify, redirect, url_for

from academic_state import AcademicState
from acadops_agent import AcadOpsAgent
from adaptive_replanner import AdaptiveReplanner
from chat_engine import ChatEngine
import database


app = Flask(__name__)

# Initialize the existing database without deleting saved data.
database.initialize_database()


def prepare_saved_plan(saved_plan):
    """Prepare a saved plan for safe display in the dashboard."""
    if not saved_plan:
        return saved_plan

    if isinstance(saved_plan, dict):
        prepared = dict(saved_plan)
    else:
        try:
            prepared = dict(saved_plan)
        except (TypeError, ValueError):
            app.logger.warning("Saved plan has an unsupported format.")
            return None

    plan_data = prepared.get("plan")

    if isinstance(plan_data, str):
        try:
            prepared["plan"] = json.loads(plan_data)
        except json.JSONDecodeError:
            app.logger.warning("Saved plan contains invalid JSON.")
            prepared["plan"] = plan_data

    return prepared


@app.route("/")
def dashboard():
    """Render the AcadOps dashboard using current academic data."""

    state = AcademicState(
        student_name="Student",
        available_hours_today=database.get_available_study_hours()
    )

    state.load_tasks()

    agent = AcadOpsAgent(state)
    analysis = agent.analyze()

    saved_plan = prepare_saved_plan(
        database.get_latest_academic_plan()
    )

    tasks_for_template = [
        {
            "title": task.title,
            "deadline": task.deadline,
            "estimated_hours": task.estimated_hours,
            "priority": task.priority,
            "completed": task.completed,
            "progress": task.progress,
            "remaining_hours": task.remaining_hours
        }
        for task in state.get_active_tasks()
    ]

    decision_data = analysis.get("decision", {})
    risks = analysis.get("risks", {})

    return render_template(
        "dashboard.html",

        # Pass both names to maintain compatibility with the template.
        decision=decision_data,
        decision_data=decision_data,

        # Workload and deadline risk information.
        workload=risks.get("workload", {}),
        deadline_risks=risks.get("deadline_risks", []),

        # Conflicts, tasks, and available study hours.
        conflicts=analysis.get("conflicts", []),
        tasks=tasks_for_template,
        available_hours=state.available_hours_today,

        # Most recently saved plan.
        saved_plan=saved_plan
    )


@app.route("/history")
def history():
    """Display saved academic plan history without deleting records."""

    plans = database.get_academic_plan_history(limit=200)

    return render_template(
        "history.html",
        plans=plans
    )


@app.route("/replan", methods=["POST"])
def replan():
    """Generate an updated academic plan."""

    state = AcademicState(
        student_name="Student",
        available_hours_today=database.get_available_study_hours()
    )

    state.load_tasks()

    AdaptiveReplanner(state).replan()

    return redirect(url_for("dashboard"))


@app.route("/chat", methods=["POST"])
def chat():
    """Handle conversational questions from the dashboard."""

    data = request.get_json(silent=True) or {}
    message = data.get("message", "")

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            "success": False,
            "reply": "Please enter a question as text."
        }), 400

    try:
        reply = ChatEngine().get_response(message.strip())

        return jsonify({
            "success": True,
            "response": reply,
            "reply": reply
        })

    except Exception:
        app.logger.exception("AcadOps chat request failed")

        return jsonify({
            "success": False,
            "response": (
                "Sorry, I couldn't process that question. "
                "Please try again."
            ),
            "reply": (
                "Sorry, I couldn't process that question. "
                "Please try again."
            )
        }), 500


if __name__ == "__main__":
    app.run(debug=True)

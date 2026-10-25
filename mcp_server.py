
from mcp.server.mcpserver import MCPServer

import database

from academic_state import AcademicState
from acadops_agent import AcadOpsAgent
from adaptive_replanner import AdaptiveReplanner


mcp = MCPServer("AcadOps")


# Initialize the database and create any missing tables
database.initialize_database()


# Load the previously saved study hours
saved_hours = database.get_available_study_hours()


# Initialize academic state using persistent settings
state = AcademicState(
    student_name="Student",
    available_hours_today=saved_hours
)

state.load_tasks()


# Add sample tasks only when the database is empty
if not state.tasks:
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


@mcp.tool()
def get_academic_state() -> dict:
    """Get the student's current academic workload."""
    return state.summary()


@mcp.tool()
def get_next_action() -> dict:
    """Determine the student's next best academic action."""
    agent = AcadOpsAgent(state)
    analysis = agent.analyze()

    return analysis["decision"]


@mcp.tool()
def get_academic_risk() -> dict:
    """Analyze workload and deadline risks."""
    agent = AcadOpsAgent(state)
    analysis = agent.analyze()

    return analysis["risks"]


@mcp.tool()
def get_conflicts() -> list:
    """Detect academic time conflicts."""
    agent = AcadOpsAgent(state)
    analysis = agent.analyze()

    return analysis["conflicts"]


@mcp.tool()
def mark_task_completed(title: str) -> dict:
    """Mark an academic task as completed."""
    success = state.mark_completed(title)

    if success:
        return {
            "success": True,
            "message": f"{title} has been marked as completed."
        }

    return {
        "success": False,
        "message": f"Task '{title}' was not found."
    }


@mcp.tool()
def add_academic_task(
    title: str,
    deadline: str,
    estimated_hours: float,
    priority: int = 3
) -> dict:
    """Add a new academic task."""
    state.add_task(
        title=title,
        deadline=deadline,
        estimated_hours=estimated_hours,
        priority=priority
    )

    return {
        "success": True,
        "message": f"{title} has been added.",
        "task": {
            "title": title,
            "deadline": deadline,
            "estimated_hours": estimated_hours,
            "priority": priority
        }
    }


@mcp.tool()
def record_progress(
    title: str,
    progress: int
) -> dict:
    """Record progress on an academic task."""
    return state.update_progress(
        title=title,
        progress=progress
    )


@mcp.tool()
def replan_academic_workload() -> dict:
    """Generate, analyze, and save an adaptive academic plan."""
    replanner = AdaptiveReplanner(state)

    return replanner.replan()


@mcp.tool()
def get_saved_academic_plan() -> dict:
    """Retrieve the latest saved academic plan from SQLite."""
    return database.get_latest_academic_plan()


@mcp.tool()
def update_available_study_hours(
    available_hours: float
) -> dict:
    """Save today's study hours and generate a revised academic plan."""

    # Validate the requested study hours
    if not 0 <= available_hours <= 24:
        return {
            "success": False,
            "message": "Available study hours must be between 0 and 24."
        }

    # Save the new setting in SQLite
    save_result = database.set_available_study_hours(
        available_hours
    )

    if not save_result["success"]:
        return save_result

    # Update the in-memory academic state
    state.available_hours_today = available_hours

    # Generate and save the revised academic plan
    replanner = AdaptiveReplanner(state)
    result = replanner.replan()

    return {
        "success": True,
        "message": (
            "Available study hours saved successfully. "
            "The academic plan has been regenerated."
        ),
        "available_hours": available_hours,
        "revised_plan": result
    }


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http"
    )

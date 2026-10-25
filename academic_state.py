from dataclasses import dataclass, field

import database


@dataclass
class AcademicTask:
    title: str
    deadline: str
    estimated_hours: float
    priority: int = 3
    completed: bool = False
    progress: int = 0

    @property
    def remaining_hours(self):
        """Calculate the remaining work based on progress."""

        remaining = self.estimated_hours * (
            1 - self.progress / 100
        )

        return round(max(0, remaining), 2)


@dataclass
class AcademicState:
    student_name: str = "Student"
    available_hours_today: float = 3.0
    tasks: list[AcademicTask] = field(default_factory=list)

    # ==========================================
    # INITIALIZE DATABASE
    # ==========================================

    def __post_init__(self):
        database.initialize_database()

    # ==========================================
    # ADD TASK
    # ==========================================

    def add_task(
        self,
        title: str,
        deadline: str,
        estimated_hours: float,
        priority: int = 3
    ):

        task = AcademicTask(
            title=title,
            deadline=deadline,
            estimated_hours=estimated_hours,
            priority=priority
        )

        self.tasks.append(task)

        database.add_task(
            title=title,
            deadline=deadline,
            estimated_hours=estimated_hours,
            priority=priority
        )

    # ==========================================
    # LOAD TASKS FROM DATABASE
    # ==========================================

    def load_tasks(self):

        rows = database.get_tasks()

        self.tasks = []

        for row in rows:

            task = AcademicTask(
                title=row["title"],
                deadline=row["deadline"],
                estimated_hours=row["estimated_hours"],
                priority=row["priority"],
                completed=bool(row["completed"]),
                progress=row["progress"]
            )

            self.tasks.append(task)

        return self.tasks

    # ==========================================
    # GET ACTIVE TASKS
    # ==========================================

    def get_active_tasks(self):

        self.load_tasks()

        return [
            task
            for task in self.tasks
            if not task.completed
        ]

    # ==========================================
    # MARK TASK COMPLETED
    # ==========================================

    def mark_completed(self, title: str):

        success = database.mark_completed(title)

        if success:

            for task in self.tasks:

                if task.title.lower() == title.lower():

                    task.completed = True
                    task.progress = 100

            return True

        return False

    # ==========================================
    # UPDATE TASK PROGRESS
    # ==========================================

    def update_progress(
        self,
        title: str,
        progress: int
    ):

        result = database.update_progress(
            title,
            progress
        )

        if result["success"]:

            for task in self.tasks:

                if task.title.lower() == title.lower():

                    task.progress = progress

                    if progress == 100:
                        task.completed = True

            return result

        return result

    # ==========================================
    # DELETE TASK
    # ==========================================

    def delete_task(self, title: str):

        success = database.delete_task(title)

        if success:

            self.tasks = [
                task
                for task in self.tasks
                if task.title.lower() != title.lower()
            ]

        return success

    # ==========================================
    # ACADEMIC STATE SUMMARY
    # ==========================================

    def summary(self):

        active_tasks = self.get_active_tasks()

        return {
            "student": self.student_name,
            "available_hours_today": self.available_hours_today,
            "active_tasks": len(active_tasks),
            "total_estimated_hours": sum(
                task.remaining_hours
                for task in active_tasks
            )
        }
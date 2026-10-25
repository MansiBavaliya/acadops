import json
import re
from datetime import datetime

from academic_state import AcademicState
from acadops_agent import AcadOpsAgent
from adaptive_replanner import AdaptiveReplanner
import database


class ChatEngine:
    """Academic assistant for tasks, progress, deadlines, and exam setup."""

    SETUP_KEY = "student_onboarding"

    NORMAL_CHAT_PHRASES = (
        "show my tasks",
        "show tasks",
        "list tasks",
        "all tasks",
        "task progress",
        "what should i study",
        "what should i do",
        "study first",
        "next task",
        "next action",
        "recommend",
        "overdue",
        "deadline",
        "due date",
        "due soon",
        "workload",
        "available time",
        "conflict",
        "conflicts",
        "help",
        "hello",
        "hi",
        "hey",
        "how are you",
        "how are you doing",
        "how's it going",
        "how are things",
        "what's up",
        "good morning",
        "good afternoon",
        "good evening",
        "thank you",
        "thanks",
        "who are you",
    )

    def get_response(self, message):
        """Route normal chat before allowing onboarding to intercept it."""

        if not isinstance(message, str) or not message.strip():
            return "Please enter a message so I can help you."

        original_message = message.strip()
        lowered = original_message.casefold()

        state = AcademicState(
            student_name="Student",
            available_hours_today=database.get_available_study_hours(),
        )
        state.load_tasks()

        tasks = state.get_active_tasks()
        all_tasks = database.get_tasks()

        analysis = AcadOpsAgent(state).analyze()
        decision = analysis["decision"]
        workload = analysis["risks"]["workload"]
        deadline_risks = analysis["risks"]["deadline_risks"]
        conflicts = analysis["conflicts"]

        # Check onboarding without allowing it to intercept normal chat.
        setup = self._get_setup()

        is_normal_chat = any(
            phrase in lowered for phrase in self.NORMAL_CHAT_PHRASES
        )

        has_percentage = bool(
            re.search(r"(?<!\d)(100|[1-9]?\d)\s*%", lowered)
        )

        is_progress_request = (
            has_percentage
            or any(
                phrase in lowered
                for phrase in (
                    "set ",
                    "update ",
                    "change ",
                    "mark ",
                    "studied ",
                    "study for ",
                    "spent ",
                    "worked on ",
                    "work on ",
                    "i completed ",
                    "i have completed ",
                    "mark as completed",
                    "mark as done",
                )
            )
        )

        # Normal questions and progress updates always take priority.
        if (
            setup
            and not setup.get("complete")
            and not is_normal_chat
            and not is_progress_request
        ):
            result = self._process_setup_answer(setup, original_message)
            if result:
                return result

        # Greetings.
        words = re.findall(r"[a-z]+", lowered)

        if words and words[0] in ("hello", "hi", "hey"):
            if not tasks:
                return (
                    "Hello! I'm AcadOps, your academic planning assistant.\n\n"
                    "Let's create your first study plan. Tell me when your "
                    "exams start, for example: "
                    "'My exams start on 10 November 2026.'"
                )

            return (
                "Hello! I'm AcadOps, your academic planning assistant. "
                "Ask me about your next task, deadlines, workload, "
                "study-time conflicts, or task progress."
            )

        # Friendly replies for casual conversation.
        if any(
            phrase in lowered
            for phrase in (
                "how are you",
                "how are you doing",
                "how's it going",
                "how are things",
            )
        ):
            return (
                "I'm doing well and ready to help you study! 😊\n"
                "How can I help you with your academic tasks today?"
            )

        if "thank you" in lowered or "thanks" in lowered:
            return (
                "You're welcome! 😊 I'm here to help you stay "
                "on track with your studies."
            )

        if any(
            phrase in lowered
            for phrase in ("good morning", "good afternoon", "good evening", "what's up")
        ):
            return (
                "Hello! 👋 I'm AcadOps, ready to help with your studies. "
                "What would you like to work on today?"
            )

        if "who are you" in lowered:
            return (
                "I'm AcadOps, your academic planning assistant. "
                "I can help with tasks, deadlines, workload, study plans, "
                "and progress updates."
            )

        # Update task progress before answering general questions.
        progress_response = self._handle_progress_update(
            original_message,
            all_tasks,
        )

        if progress_response is not None:
            return progress_response

        # Start onboarding only when the user requests a study plan.
        start_phrases = (
            "create my study plan",
            "create a study plan",
            "first study plan",
            "help me create my exam study plan",
            "start exam setup",
            "set up my exams",
        )

        if any(phrase in lowered for phrase in start_phrases):
            setup = {
                "complete": False,
                "exam_start": None,
                "subjects": [],
                "subject_dates": {},
                "chapters": None,
                "topics": [],
                "hours": None,
                "step": "exam_start",
            }
            self._save_setup(setup)

            return (
                "Let's build your study plan together!\n\n"
                "When do your exams start? Please include the year, "
                "for example: 10 November 2026."
            )

        # Recommend the next action.
        if any(
            phrase in lowered
            for phrase in (
                "what should i study",
                "what should i do",
                "study first",
                "next task",
                "next action",
                "recommend",
                "what next",
            )
        ):
            if decision.get("next_action"):
                return (
                    f"Your next best action is: {decision['next_action']}.\n"
                    f"Reason: {decision.get('reason', 'This task has high priority.')}\n"
                    f"Available study time today: "
                    f"{state.available_hours_today} hours."
                )

            return (
                "You have no active tasks requiring work. "
                "You can create a study plan if you have upcoming exams."
            )

        # List tasks and progress.
        if any(
            phrase in lowered
            for phrase in (
                "show my tasks",
                "show tasks",
                "list tasks",
                "list my tasks",
                "all tasks",
                "task progress",
                "my academic tasks",
            )
        ):
            if not all_tasks:
                return "You don't have any saved academic tasks yet."

            lines = ["Here are your saved academic tasks:"]

            for task in all_tasks:
                title = task.get("title", "Untitled task")
                deadline = task.get("deadline", "No deadline")
                progress = int(task.get("progress", 0) or 0)
                estimated = float(task.get("estimated_hours", 0) or 0)
                remaining = estimated * (1 - progress / 100)

                status = (
                    "Completed"
                    if task.get("completed") or progress >= 100
                    else "In progress"
                )

                lines.append(
                    f"- {title} | Deadline: {deadline} | "
                    f"Progress: {progress}% | "
                    f"Remaining: {remaining:.2f} hours | {status}"
                )

            return "\n".join(lines)

        # Deadline risks.
        if any(
            word in lowered
            for word in ("overdue", "deadline", "due date", "due soon")
        ):
            if not deadline_risks:
                return "No deadline risks were found in your current task data."

            lines = ["Here are your current deadline risks:"]

            for risk in deadline_risks:
                days = risk.get("days_remaining")

                if isinstance(days, (int, float)):
                    if days < 0:
                        timing = f"{abs(days)} day(s) overdue"
                    elif days == 0:
                        timing = "due today"
                    else:
                        timing = f"{days} day(s) remaining"
                else:
                    timing = "deadline timing unavailable"

                lines.append(
                    f"- {risk.get('task', 'Task')}: "
                    f"{risk.get('risk', 'Risk unknown')} - {timing}."
                )

            return "\n".join(lines)

        # Workload and study capacity.
        if any(
            word in lowered
            for word in ("workload", "hours", "busy", "capacity", "available time")
        ):
            return (
                f"Workload status: {workload.get('level', 'Unknown')}.\n"
                f"Remaining workload: "
                f"{workload.get('total_workload_hours', 0)} hours.\n"
                f"Available study time: "
                f"{workload.get('available_hours', state.available_hours_today)} "
                f"hours per day."
            )

        # Study-time conflicts.
        if any(word in lowered for word in ("conflict", "conflicts", "schedule")):
            if not conflicts:
                return "No study-time conflicts were detected."

            lines = ["Here are your detected study-time conflicts:"]

            for conflict in conflicts:
                lines.append(
                    f"- {conflict.get('task', 'Task')}: "
                    f"{conflict.get('message', str(conflict))}"
                )

            return "\n".join(lines)

        return (
            "I'm AcadOps, your academic planning assistant.\n\n"
            "You can ask:\n"
            "- Show my tasks.\n"
            "- What should I study next?\n"
            "- Which tasks are overdue?\n"
            "- Show my workload.\n"
            "- Show my task progress.\n"
            "- Set AI Assignment to 75% complete.\n"
            "- I studied 1 hour for AI Exam Preparation.\n"
            "- Mark AI Assignment as completed.\n\n"
            "To begin exam setup, say: "
            "'Help me create my exam study plan.'"
        )

    def _handle_progress_update(self, message, all_tasks):
        """Update only the task explicitly identified by the user."""

        lowered = message.strip().casefold()

        percent_match = re.search(
            r"(?<!\d)(100|[1-9]?\d)\s*%",
            lowered,
        )

        hours_match = re.search(
            r"(?<!\d)(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)\b",
            lowered,
        )

        study_verbs = (
            "studied",
            "study for",
            "spent",
            "worked on",
            "work on",
            "completed",
            "finished",
            "done",
        )

        progress_verbs = (
            "set",
            "update",
            "change",
            "mark",
            "progress",
            "complete",
            "completed",
            "finish",
            "finished",
            "done",
        )

        is_hours_update = (
            hours_match is not None
            and any(verb in lowered for verb in study_verbs)
        )

        is_percentage_update = (
            percent_match is not None
            and any(verb in lowered for verb in progress_verbs)
        )

        is_completion_request = any(
            phrase in lowered
            for phrase in (
                "mark as completed",
                "mark completed",
                "mark as complete",
                "mark complete",
                "mark as done",
                "mark done",
                "task is complete",
                "task is completed",
                "task is done",
                "i completed",
                "i have completed",
            )
        )

        if is_hours_update:
            update_type = "hours"
        elif is_percentage_update:
            update_type = "percentage"
        elif is_completion_request:
            update_type = "complete"
        else:
            return None

        # Match exact task titles contained in the user's message.
        matching_tasks = []

        for task in all_tasks:
            title = str(task.get("title", "")).strip()

            if title and title.casefold() in lowered:
                matching_tasks.append(task)

        if not matching_tasks:
            return (
                "I couldn't identify the task to update. Please include its "
                "exact title, for example: "
                "'Set AI Assignment to 75% complete.'"
            )

        # Prefer the longest title to avoid matching a shorter task.
        longest_length = max(
            len(str(task.get("title", "")).strip())
            for task in matching_tasks
        )

        matching_tasks = [
            task for task in matching_tasks
            if len(str(task.get("title", "")).strip()) == longest_length
        ]

        if len(matching_tasks) != 1:
            choices = [
                f"- {task.get('title')} (deadline: {task.get('deadline')})"
                for task in matching_tasks[:5]
            ]
            return (
                "I found multiple matching tasks, so I haven't changed "
                "anything. Please specify the task's deadline:\n"
                + "\n".join(choices)
            )

        task = matching_tasks[0]
        task_id = task.get("id")
        title = task.get("title", "Task")
        current_progress = int(task.get("progress", 0) or 0)
        estimated_hours = float(task.get("estimated_hours", 0) or 0)

        if task.get("completed") or current_progress >= 100:
            return f"'{title}' is already marked as completed. No changes were made."

        if update_type == "percentage":
            new_progress = int(percent_match.group(1))

            if new_progress < current_progress:
                return (
                    f"'{title}' is currently at {current_progress}%. "
                    "This request would reduce its progress. "
                    "Please confirm the percentage you want to set."
                )

        elif update_type == "complete":
            new_progress = 100

        else:
            hours_studied = float(hours_match.group(1))

            if hours_studied <= 0:
                return "Please enter a study duration greater than zero."

            if estimated_hours <= 0:
                return (
                    f"I can't calculate progress for '{title}' because "
                    "its estimated hours are invalid."
                )

            remaining_hours = estimated_hours * (
                1 - current_progress / 100
            )

            if hours_studied > remaining_hours + 0.001:
                return (
                    f"'{title}' has approximately {remaining_hours:.2f} "
                    f"hour(s) remaining. You entered {hours_studied:g} "
                    "hour(s), so I haven't changed the saved progress."
                )

            new_progress = min(
                100,
                round(
                    current_progress
                    + hours_studied / estimated_hours * 100
                ),
            )

        result = database.update_progress_by_id(task_id, new_progress)

        if not result.get("success"):
            return (
                "I couldn't update the task: "
                + result.get("message", "Unknown database error.")
            )

        # Refresh the saved study plan after a successful progress update.
        try:
            state = AcademicState(
                student_name="Student",
                available_hours_today=database.get_available_study_hours(),
            )
            state.load_tasks()
            AdaptiveReplanner(state).replan()
        except Exception:
            # The progress update remains saved if plan refresh fails.
            pass

        if new_progress >= 100:
            return (
                f"Great! '{title}' is now marked as completed.\n"
                "Your saved task progress has been updated."
            )

        remaining = max(
            0,
            estimated_hours * (1 - new_progress / 100),
        )

        if update_type == "hours":
            return (
                f"Progress updated for '{title}'.\n"
                f"Study time recorded: {hours_match.group(1)} hour(s).\n"
                f"Progress: {new_progress}% complete.\n"
                f"Estimated work remaining: {remaining:.2f} hours."
            )

        return (
            f"Progress updated for '{title}'.\n"
            f"Progress: {new_progress}% complete.\n"
            f"Estimated work remaining: {remaining:.2f} hours."
        )

    def _get_setup(self):
        raw = database.get_setting(self.SETUP_KEY)

        if not raw:
            return None

        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    def _save_setup(self, setup):
        database.set_setting(self.SETUP_KEY, json.dumps(setup))

    def _ask_next_setup_question(self, setup):
        step = setup.get("step")

        if step == "exam_start":
            return "When do your exams start? Please include the year."

        if step == "subjects":
            return "Which subjects do you have? List them separated by commas."

        if step == "subject_dates":
            return (
                "What is the exam date for each subject? Use this format: "
                "Maths - 10 November 2026, Science - 12 November 2026."
            )

        if step == "chapters":
            return (
                "Which chapters or topics do you need to study? "
                "List them separated by commas. You can also say 'not sure'."
            )

        if step == "hours":
            return "How many hours can you study each day? Enter a number from 1 to 24."

        return (
            "Let's continue setting up your study plan. "
            "What information can you share next?"
        )

    def _parse_date(self, text):
        """Parse common date formats into YYYY-MM-DD."""

        text = text.strip().replace(",", "")

        formats = (
            "%d %B %Y",
            "%d %b %Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
        )

        for fmt in formats:
            try:
                return datetime.strptime(text, fmt).date().isoformat()
            except ValueError:
                continue

        return None

    def _parse_topics(self, text):
        """Split a topic list into clean, non-empty items."""

        if text.strip().casefold() in (
            "not sure",
            "none",
            "no chapters",
            "no topics",
        ):
            return []

        return [
            item.strip(" \t-*")
            for item in re.split(r"[,;\n]+", text)
            if item.strip(" \t-*")
        ]

    def _process_setup_answer(self, setup, answer):
        """Process one answer in the optional exam-planning workflow."""

        step = setup.get("step")
        answer = answer.strip()

        if step == "exam_start":
            parsed = self._parse_date(answer)

            if not parsed:
                return (
                    "I couldn't understand that date. Please use a format "
                    "such as 10 November 2026."
                )

            setup["exam_start"] = parsed
            setup["step"] = "subjects"
            self._save_setup(setup)

            return (
                f"Thanks! Your exam period starts on {parsed}.\n"
                "Which subjects do you have? Separate them with commas."
            )

        if step == "subjects":
            subjects = self._parse_topics(answer)

            if not subjects:
                return "Please enter at least one subject, separated by commas."

            setup["subjects"] = subjects
            setup["subject_dates"] = {}
            setup["step"] = "subject_dates"
            self._save_setup(setup)

            return (
                "Now enter each subject and its exam date. Example:\n"
                "Maths - 10 November 2026, Science - 12 November 2026"
            )

        if step == "subject_dates":
            entries = [
                item.strip()
                for item in re.split(r"[,;\n]+", answer)
                if item.strip()
            ]

            parsed_dates = {}

            for entry in entries:
                if "-" not in entry:
                    return (
                        "Please use this format: Maths - 10 November 2026, "
                        "Science - 12 November 2026."
                    )

                subject, raw_date = entry.split("-", 1)
                subject = subject.strip()
                parsed = self._parse_date(raw_date)

                if not subject or not parsed:
                    return (
                        f"I couldn't read the subject date in '{entry}'. "
                        "Please use a format like Maths - 10 November 2026."
                    )

                parsed_dates[subject] = parsed

            missing = [
                subject for subject in setup.get("subjects", [])
                if not any(
                    subject.casefold() == entered.casefold()
                    for entered in parsed_dates
                )
            ]

            if missing:
                return (
                    "I still need dates for: "
                    + ", ".join(missing)
                    + ". Please include those subjects too."
                )

            setup["subject_dates"] = parsed_dates
            setup["step"] = "chapters"
            self._save_setup(setup)

            return (
                "Which chapters or topics do you need to study? "
                "List them separated by commas, or say 'not sure'."
            )

        if step == "chapters":
            setup["topics"] = self._parse_topics(answer)
            setup["step"] = "hours"
            self._save_setup(setup)

            return (
                "How many hours can you study each day? "
                "Enter a number from 1 to 24."
            )

        if step == "hours":
            match = re.search(r"\d+(?:\.\d+)?", answer)

            if not match:
                return "Please enter the number of hours you can study each day."

            hours = float(match.group())

            if hours < 1 or hours > 24:
                return "Please enter a number from 1 to 24 hours."

            setup["hours"] = hours

            try:
                database.set_available_study_hours(hours)

                topics = setup.get("topics") or []
                subject_dates = setup.get("subject_dates", {})
                subjects = setup.get("subjects", [])

                # Use entered topics as individual tasks when provided.
                # Otherwise, create one task per subject.
                if topics:
                    task_specs = []

                    for topic in topics:
                        matching_subject = next(
                            (
                                subject for subject in subjects
                                if subject.casefold() in topic.casefold()
                            ),
                            subjects[0] if subjects else topic,
                        )
                        deadline = next(
                            (
                                exam_date
                                for subject, exam_date in subject_dates.items()
                                if subject.casefold()
                                == matching_subject.casefold()
                            ),
                            setup.get("exam_start"),
                        )
                        task_specs.append((topic, deadline))
                else:
                    task_specs = [
                        (
                            subject,
                            next(
                                (
                                    exam_date
                                    for entered, exam_date in subject_dates.items()
                                    if entered.casefold() == subject.casefold()
                                ),
                                setup.get("exam_start"),
                            ),
                        )
                        for subject in subjects
                    ]

                created = 0
                per_task_hours = max(0.5, hours / max(1, len(task_specs)))

                existing = database.get_tasks()
                existing_keys = {
                    (
                        str(task.get("title", "")).casefold(),
                        str(task.get("deadline", "")),
                    )
                    for task in existing
                }

                for index, (title, deadline) in enumerate(task_specs, start=1):
                    key = (title.casefold(), str(deadline))

                    if key in existing_keys:
                        continue

                    database.add_task(
                        title=title,
                        deadline=deadline,
                        estimated_hours=round(per_task_hours, 2),
                        priority=index,
                    )
                    created += 1

                setup["complete"] = True
                setup["step"] = "complete"
                self._save_setup(setup)

                if created:
                    return (
                        "Your exam setup is saved!\n"
                        f"Available study time: {hours:g} hours per day.\n"
                        f"New tasks created: {created}.\n"
                        "You can now ask 'What should I study next?' "
                        "to get a recommendation."
                    )

                return (
                    "Your study availability has been saved. "
                    "The tasks from this setup already exist, so I did not "
                    "create duplicates. Ask 'What should I study next?' "
                    "for your current recommendation."
                )

            except Exception as exc:
                return (
                    "I received your study hours, but couldn't finish saving "
                    "the setup. Your existing tasks have not been reset. "
                    f"Technical detail: {exc}"
                )

        return self._ask_next_setup_question(setup)

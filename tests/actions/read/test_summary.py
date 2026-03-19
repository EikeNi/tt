from unittest import TestCase
from io import StringIO
from contextlib import redirect_stdout
import re
import mock
import tt.tt as tt_cli

from tt.actions.read import summary


class TestSummary(TestCase):

    def test_get_last_n_months_order_and_values(self):
        months = summary.get_last_n_months(2026, 3, 12)
        self.assertEqual(12, len(months))
        self.assertEqual({"year": 2025, "month": 4}, months[0])
        self.assertEqual({"year": 2026, "month": 3}, months[-1])

    def test_render_total_plot_contains_total_and_scale(self):
        rows = [
            {
                "label": "2026-02",
                "rate": 90.0,
                "worked": summary.timedelta(hours=144),
                "target": summary.timedelta(hours=160),
                "category_rates": {
                    "Dissertation": 20.0,
                    "Projekt": 30.0,
                    "Lehre": 25.0,
                    "Institut": 15.0,
                },
            },
            {
                "label": "2026-03",
                "rate": 100.0,
                "worked": summary.timedelta(hours=160),
                "target": summary.timedelta(hours=160),
                "category_rates": {
                    "Dissertation": 25.0,
                    "Projekt": 35.0,
                    "Lehre": 20.0,
                    "Institut": 20.0,
                },
            },
        ]

        lines = summary.render_last_12_month_total_plot(rows)
        rendered = "\n".join(lines)
        if summary.HAS_ASCIICHART:
            self.assertIn("Total", rendered)
            self.assertIn("02", rendered)
            self.assertIn("03", rendered)
            self.assertNotIn("Scale:", rendered)
            self.assertNotIn("Months", rendered)
        else:
            self.assertIn("asciichartpy", rendered)
            self.assertIn("Install with:", rendered)

    def test_render_total_plot_with_categories_uses_stacked_header(self):
        rows = [
            {
                "label": "2026-02",
                "rate": 90.0,
                "worked": summary.timedelta(hours=144),
                "target": summary.timedelta(hours=160),
                "category_rates": {
                    "Dissertation": 20.0,
                    "Projekt": 30.0,
                    "Lehre": 25.0,
                    "Institut": 15.0,
                },
            },
            {
                "label": "2026-03",
                "rate": 100.0,
                "worked": summary.timedelta(hours=160),
                "target": summary.timedelta(hours=160),
                "category_rates": {
                    "Dissertation": 25.0,
                    "Projekt": 35.0,
                    "Lehre": 20.0,
                    "Institut": 20.0,
                },
            },
        ]

        lines = summary.render_last_12_month_total_plot(rows, include_categories=True)
        rendered = "\n".join(lines)
        self.assertIn("Stacked categories (total is top edge)", rendered)
        self.assertIn("Legend:", rendered)
        self.assertIn("D=Dissertation", rendered)
        self.assertIn("P=Projekt", rendered)
        self.assertIn("L=Lehre", rendered)
        self.assertIn("I=Institut", rendered)
        self.assertIn("02", rendered)
        self.assertIn("03", rendered)
        self.assertNotIn("Scale:", rendered)
        self.assertNotIn("T=total", rendered.lower())

    @mock.patch("tt.actions.read.summary.get_current_year_local_tz")
    @mock.patch("tt.actions.read.summary.get_current_month_local_tz")
    @mock.patch("tt.actions.read.summary.prompt_for_category")
    @mock.patch("tt.actions.read.summary.get_data_store")
    def test_action_summary_defaults_and_prints_12_month_plot(
        self, mocked_store, mocked_prompt, mocked_month, mocked_year
    ):
        mocked_year.return_value = "2026"
        mocked_month.return_value = "03"
        mocked_prompt.return_value = "Projekt"

        mocked_store.return_value.load.return_value = {
            "work": [
                {
                    "name": "project-a",
                    "start": "2026-03-02T08:00:00.000001Z",
                    "end": "2026-03-02T12:00:00.000001Z",
                    "tags": ["client"],
                },
                {
                    "name": "project-a",
                    "start": "2026-02-02T08:00:00.000001Z",
                    "end": "2026-02-02T16:00:00.000001Z",
                    "tags": ["client"],
                },
            ],
            "holiday": [],
            "task_categories": {"project-a": "Projekt"},
        }

        output = StringIO()
        with redirect_stdout(output):
            summary.action_summary(None, None, None)

        value = output.getvalue()
        self.assertIn("Category distribution:", value)
        self.assertIn("Dissertation", value)
        self.assertIn("Projekt", value)
        self.assertIn("Lehre", value)
        self.assertIn("Institut", value)
        self.assertIn("Last 12 months total utilization trend:", value)
        if summary.HAS_ASCIICHART:
            self.assertIn("Total", value)
            self.assertNotIn("Scale:", value)
        else:
            self.assertIn("Install with:", value)

    def test_parse_args_summary_with_categories_flag(self):
        fn, args = tt_cli.parse_args(["tt", "summary", "03", "2026", "--with-categories"])

        self.assertEqual(summary.action_summary, fn)
        self.assertEqual("03", args["month"])
        self.assertEqual("2026", args["year"])
        self.assertTrue(args["include_categories"])

    @mock.patch("tt.actions.read.summary.prompt_for_category")
    def test_assign_missing_categories_interactive_sets_missing_values(self, mocked_prompt):
        mocked_prompt.side_effect = ["Lehre", "Institut"]
        category_by_task = {"task-a": None, "task-b": "Projekt", "task-c": None}
        work = [
            {"name": "task-a", "start": "2026-03-01T08:00:00.000001Z"},
            {"name": "task-b", "start": "2026-03-01T10:00:00.000001Z"},
            {"name": "task-c", "start": "2026-03-02T10:00:00.000001Z"},
        ]

        summary.assign_missing_categories_interactive(category_by_task, work)

        self.assertEqual("Lehre", category_by_task["task-a"])
        self.assertEqual("Projekt", category_by_task["task-b"])
        self.assertEqual("Institut", category_by_task["task-c"])

    def test_ensure_task_categories_creates_mapping_and_defaults(self):
        data = {
            "work": [
                {"name": "task-a", "start": "2026-03-01T08:00:00.000001Z"},
                {"name": "task-b", "start": "2026-03-01T10:00:00.000001Z"},
            ],
            "holiday": [],
        }

        categories = summary.ensure_task_categories(data, data["work"])

        self.assertIn("task_categories", data)
        self.assertIsNone(categories["task-a"])
        self.assertIsNone(categories["task-b"])

from rivernet import __main__ as cli


def test_every_planned_command_is_listed_in_help():
    help_text = cli.build_parser().format_help()
    for name in cli.PLANNED:
        assert name in help_text


def test_no_command_prints_help_and_succeeds():
    assert cli.main([]) == 0


def test_unimplemented_commands_exit_with_status_2():
    for name in cli.PLANNED:
        if name in cli.HANDLERS:
            continue  # implemented by a landed task
        assert cli.main([name]) == 2


def test_extra_arguments_are_passed_through_to_the_handler(monkeypatch):
    seen = {}

    def handler(args):
        seen["args"] = args
        return 0

    monkeypatch.setitem(cli.HANDLERS, "extract", handler)
    assert cli.main(["extract", "--in", "a.pbf", "--out", "b.jsonl.gz"]) == 0
    assert seen["args"] == ["--in", "a.pbf", "--out", "b.jsonl.gz"]


def test_planned_tasks_reference_task_ids_of_the_plan():
    assert all(task.startswith("T") for task in cli.PLANNED.values())

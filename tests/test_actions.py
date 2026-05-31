from src.actions import DryRunActionExecutor, create_executor
from src.models import ActionCommand


def test_create_dry_run_executor() -> None:
    executor = create_executor("dry-run")
    assert isinstance(executor, DryRunActionExecutor)


def test_dry_run_execute() -> None:
    executor = DryRunActionExecutor()
    executor.execute(ActionCommand(type="idle", duration=0.1, reason="test"))

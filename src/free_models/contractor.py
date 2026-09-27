from __future__ import annotations

import json
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ContractorTask:
    """Portable task envelope shared between Hermes and a temporary worker."""

    objective: str
    repo: str
    allowed_paths: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)
    data_class: str = "public_or_sanitized"
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)

    def validate(self) -> None:
        if not self.objective.strip() or not self.repo.strip():
            raise ValueError("objective and repo are required")
        if self.data_class not in {"public_or_sanitized", "local_project"}:
            raise ValueError("contractor tasks only accept public_or_sanitized or local_project data")
        if any(".." in Path(path).parts for path in self.allowed_paths):
            raise ValueError("allowed_paths cannot escape the repository")

    def to_json(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass
class ContractorResult:
    task_id: str
    model: str
    provider: str
    status: str
    output: str = ""
    return_code: int | None = None
    duration_seconds: float = 0.0
    verified: bool = False
    verification_output: str = ""
    error: str | None = None


class FreeModelContractor:
    """Run a bounded, explicitly-pinned Hermes sub-agent.

    This wrapper never changes the global Hermes model. The caller supplies the
    model and the task envelope; verification commands are run locally after
    the worker returns.
    """

    def __init__(self, provider: str = "openrouter", timeout: int = 900):
        self.provider = provider
        self.timeout = timeout

    @staticmethod
    def _prompt(task: ContractorTask) -> str:
        paths = ", ".join(task.allowed_paths) if task.allowed_paths else "only files necessary for the objective"
        checks = " && ".join(task.verification) if task.verification else "no verification command supplied"
        return (
            "You are a bounded coding contractor.\n"
            f"Task ID: {task.task_id}\nObjective: {task.objective}\n"
            f"Repository: {task.repo}\nAllowed paths: {paths}\n"
            f"Verification to run after edits: {checks}\n"
            "Do not access credentials, unrelated files, or external accounts. Make the smallest useful change. "
            "Report files changed, tests run, and blockers."
        )

    def run(self, task: ContractorTask, model: str, dry_run: bool = False) -> ContractorResult:
        task.validate()
        if dry_run:
            return ContractorResult(task.task_id, model, self.provider, "DRY_RUN", output=self._prompt(task))
        started = time.monotonic()
        command = ["hermes", "chat", "-q", self._prompt(task), "--provider", self.provider,
                   "--model", model, "--in", task.repo, "--max-turns", "20", "--source", "contractor"]
        try:
            proc = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            return ContractorResult(task.task_id, model, self.provider, "TIMEOUT", duration_seconds=time.monotonic() - started,
                                    error=str(exc))
        output = (proc.stdout or "")[-20_000:]
        result = ContractorResult(task.task_id, model, self.provider, "COMPLETED" if proc.returncode == 0 else "FAILED",
                                  output=output, return_code=proc.returncode,
                                  duration_seconds=round(time.monotonic() - started, 3))
        if proc.returncode != 0:
            result.error = (proc.stderr or "worker failed")[-4_000:]
        result.verified, result.verification_output = self.verify(task)
        return result

    def verify(self, task: ContractorTask) -> tuple[bool, str]:
        outputs: list[str] = []
        for command in task.verification:
            proc = subprocess.run(command, cwd=task.repo, shell=True, capture_output=True, text=True,
                                  timeout=min(self.timeout, 300), check=False)
            outputs.append(f"$ {command}\n{proc.stdout}{proc.stderr}")
            if proc.returncode != 0:
                return False, "\n".join(outputs)
        return True, "\n".join(outputs)


def save_result(result: ContractorResult, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

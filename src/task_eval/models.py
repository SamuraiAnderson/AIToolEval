from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict


@dataclass
class Task:
    id: str
    test_repo: str
    test_repo_ref: str
    metadata: dict = field(default_factory=dict)
    prompts_dir: str = "prompts"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(**data)


@dataclass
class TestCaseResult:
    __test__ = False  # prevent pytest collection

    name: str
    passed: bool
    duration: float
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> TestCaseResult:
        return cls(**data)


@dataclass
class EvalResult:
    run_id: str
    task_id: str
    tool: str
    model: str
    run_index: int
    timestamp: str
    tags: str  # JSON string
    # prompt
    prompt_file: str
    prompt: str
    # git baseline
    base_commit_sha: str
    eval_commit_sha: str | None
    # test results
    tests_passed: int
    tests_total: int
    test_details: str  # JSON string of list[TestCaseResult]
    time_spent: float
    success: bool
    # code changes
    lines_added: int
    lines_deleted: int
    files_modified: int
    patch: str | None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> EvalResult:
        return cls(**data)

    def get_test_case_results(self) -> list[TestCaseResult]:
        raw = json.loads(self.test_details)
        return [TestCaseResult.from_dict(r) for r in raw]

    def get_tags(self) -> dict:
        return json.loads(self.tags) if self.tags else {}

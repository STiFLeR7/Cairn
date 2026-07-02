from cairn.agent import Agent, AgentRun
from cairn.model import Action, CODE, FINISH
from cairn.model_mock import ScriptableMockModel
from cairn.runtime.checkpoint_store import CheckpointStore
from cairn.runtime.effect_ledger import EffectLedger
from cairn.worlds import Workspace


def _agent(tmp_path, script):
    ws_dir = tmp_path / "ws"; ws_dir.mkdir()
    world = Workspace(str(ws_dir), str(tmp_path / "snaps"))
    store = CheckpointStore(str(tmp_path / "ck"))
    ledger = EffectLedger(str(tmp_path / "e.jsonl"), "run")
    model = ScriptableMockModel(script)
    return ws_dir, Agent(model, world, store=store, ledger=ledger, max_steps=10)


def test_agent_run_executes_the_script_and_checkpoints(tmp_path):
    script = [
        Action(kind=CODE, code="open('a.txt','w').write('1')"),
        Action(kind=CODE, code="open('b.txt','w').write('2')"),
        Action(kind=FINISH, result="done"),
    ]
    ws_dir, agent = _agent(tmp_path, script)
    run = agent.run("make a and b")
    assert isinstance(run, AgentRun)
    assert run.finished is True            # model emitted FINISH
    assert run.steps == 2                  # two code actions executed
    assert run.checkpoints == 2            # one checkpoint per executed step
    assert (ws_dir / "a.txt").exists() and (ws_dir / "b.txt").exists()
    assert run.final_state is not None


def test_agent_resume_with_no_checkpoint_starts_fresh(tmp_path):
    script = [Action(kind=CODE, code="open('a.txt','w').write('1')"), Action(kind=FINISH)]
    ws_dir, agent = _agent(tmp_path, script)
    run = agent.resume("make a")          # no checkpoint yet -> behaves like run
    assert run.resumed is False
    assert (ws_dir / "a.txt").exists()


def test_agent_resume_regrounds_and_continues_after_a_crash(tmp_path):
    # Step 0 runs and checkpoints; then we simulate a crash (new Agent, same dirs) and resume.
    ws_dir = tmp_path / "ws"; ws_dir.mkdir()
    snaps = str(tmp_path / "snaps"); ck = str(tmp_path / "ck"); ej = str(tmp_path / "e.jsonl")

    def fresh_world():
        return Workspace(str(ws_dir), snaps)

    script = [
        Action(kind=CODE, code="open('a.txt','w').write('1')"),
        Action(kind=CODE, code="open('b.txt','w').write('2')"),
        Action(kind=FINISH),
    ]
    # First Agent: run only the first step, then "crash" (max_steps=1 stops after one execute).
    a1 = Agent(ScriptableMockModel(script), fresh_world(),
               store=CheckpointStore(ck), ledger=EffectLedger(ej, "run"), max_steps=1)
    r1 = a1.run("make a then b")
    assert r1.steps == 1 and (ws_dir / "a.txt").exists() and not (ws_dir / "b.txt").exists()

    # Recovery Agent: fresh objects pointing at the SAME durable dirs; resume re-grounds step 0.
    a2 = Agent(ScriptableMockModel(script), fresh_world(),
               store=CheckpointStore(ck), ledger=EffectLedger(ej, "run"), max_steps=10)
    r2 = a2.resume("make a then b")
    assert r2.resumed is True
    assert len(r2.history) == 2                     # step 0 re-grounded + step 1 executed
    assert r2.history[0].action.code == "open('a.txt','w').write('1')"   # step 0 re-grounded from the cairn
    assert r2.recovery_tax == 1                     # only ONE new step needed (not a full restart)
    assert (ws_dir / "b.txt").exists()              # the task got finished
    assert r2.finished is True


class _ExecResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode; self.stdout = stdout; self.stderr = stderr


class ExecFakeWorld:
    """An in-memory, NON-filesystem executable World — proves the Agent isn't workspace-bound.

    `execute` interprets a tiny 'k=v' command language by mutating in-memory state.
    """

    def __init__(self):
        self.state: dict[str, str] = {}
        self._snaps: dict[str, dict] = {}
        self._n = 0

    def snapshot(self) -> str:
        sid = f"s{self._n}"; self._n += 1
        self._snaps[sid] = dict(self.state)
        return sid

    def restore(self, snap_id: str) -> None:
        self.state = dict(self._snaps[snap_id])

    def digest(self) -> dict:
        return {k: self.state[k] for k in sorted(self.state)}

    def execute(self, code: str, cwd=None) -> _ExecResult:
        k, _, v = code.partition("=")
        self.state[k.strip()] = v.strip()
        return _ExecResult()


def test_agent_recovers_on_a_non_workspace_world(tmp_path):
    world = ExecFakeWorld()
    store = CheckpointStore(str(tmp_path / "ck"))
    ledger = EffectLedger(str(tmp_path / "e.jsonl"), "run")
    script = [
        Action(kind=CODE, code="x=1"),
        Action(kind=CODE, code="y=2"),
        Action(kind=FINISH),
    ]
    # Run step 0 then "crash".
    a1 = Agent(ScriptableMockModel(script), world,
               store=store, ledger=ledger, max_steps=1)
    a1.run("set x then y")
    assert world.state == {"x": "1"}

    # Corrupt in-memory state, then recover + continue with a fresh Agent on the SAME world+dirs.
    world.state = {"x": "CORRUPT"}
    a2 = Agent(ScriptableMockModel(script), world,
               store=CheckpointStore(str(tmp_path / "ck")),
               ledger=EffectLedger(str(tmp_path / "e.jsonl"), "run"), max_steps=10)
    run = a2.resume("set x then y")

    assert world.state == {"x": "1", "y": "2"}      # restored from snapshot, then y set
    assert run.recovery_tax == 1                    # only the un-done step was redone
    assert run.finished is True

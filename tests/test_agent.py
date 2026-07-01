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

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

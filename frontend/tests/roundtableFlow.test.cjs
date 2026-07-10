const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("../node_modules/typescript/lib/typescript");

function loadTsModule(relativePath) {
  const modulePath = path.join(__dirname, "..", relativePath);
  const source = fs.readFileSync(modulePath, "utf8");
  const compiled = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2019,
      esModuleInterop: true,
    },
  }).outputText;
  const mod = { exports: {} };
  const localRequire = (request) => {
    if (request.startsWith(".")) {
      return loadTsModule(path.join(path.dirname(relativePath), request));
    }
    return require(request);
  };
  const run = new Function("require", "module", "exports", "__dirname", "__filename", compiled);
  run(localRequire, mod, mod.exports, path.dirname(modulePath), modulePath);
  return mod.exports;
}

const flow = loadTsModule("lib/roundtableFlow.ts");

let state = flow.createRoundtableFlowState(["confucius", "laozi"]);
assert.equal(state.speeches.length, 2);
assert.equal(state.speeches[0].id, "1-confucius");

state = flow.applyDebateStreamEvent(state, {
  type: "sage_start",
  sage_key: "confucius",
  sage_name: "孔子",
  round: 1,
});
assert.equal(state.activeSageId, "confucius");
assert.equal(state.speeches[0].isStreaming, true);

state = flow.applyDebateStreamEvent(state, {
  type: "sage_chunk",
  sage_key: "confucius",
  content: "士不可以不弘毅",
});
assert.equal(state.speeches[0].content, "士不可以不弘毅");

state = flow.applyDebateStreamEvent(state, {
  type: "sage_end",
  sage_key: "confucius",
  speech: {
    sage_key: "confucius",
    sage_name: "孔子",
    round_number: 1,
    content: "士不可以不弘毅",
    citations: [
      {
        id: "引1",
        source: "《论语·泰伯》",
        original: "士不可以不弘毅",
        verifiable: true,
      },
    ],
  },
});
assert.equal(state.speeches[0].isComplete, true);
assert.equal(state.speeches[0].citations[0].text, "士不可以不弘毅");
assert.equal(state.speeches[0].citations[0].similarity, 1);

state = flow.applyDebateStreamEvent(state, {
  type: "round_done",
  round: 2,
  clashes: [
    {
      from_sage: "mozi",
      to_sage: "laozi",
      clash_type: "refute",
      summary: "墨子反驳老子的不争",
    },
  ],
});
assert.equal(state.clashes[0].fromSageId, "mozi");
assert.equal(state.clashes[0].toSageId, "laozi");
assert.equal(state.clashes[0].type, "refute");

const report = flow.normalizeDebateReport({
  topic: "我该不该躺平？",
  consensus: ["消极放弃不可取"],
  divergences: ["儒法重进取，道家重守静"],
  recommendations: [{ sage: "孔子", recommendation: "守志待时" }],
  summary: "退守不是放弃。",
  participating_sages: ["孔子", "老子"],
});
assert.equal(report.consensus[0], "消极放弃不可取");
assert.equal(report.recommendations[0].sage, "孔子");

const guestRound = flow.normalizeBackendRound({
  round_number: 4,
  round_type: "guest_response",
  speeches: [
    {
      sage_key: "confucius",
      sage_name: "孔子",
      round_number: 4,
      content: "孔子回应李白",
      citations: [],
    },
    {
      sage_key: "laozi",
      sage_name: "老子",
      round_number: 4,
      content: "老子回应李白",
      citations: [],
    },
  ],
  clashes: [
    {
      from_sage: "confucius",
      to_sage: "li_bai",
      clash_type: "reframe",
      summary: "孔子重构李白观点",
    },
  ],
});
assert.equal(guestRound.speeches.length, 2);
assert.equal(guestRound.speeches[0].sageId, "confucius");
assert.equal(guestRound.speeches[0].roundNumber, 4);
assert.equal(guestRound.clashes[0].toSageId, "li_bai");

const evidencedSpeech = flow.normalizeBackendSpeech({
  sage_key: "confucius",
  round_number: 5,
  content: "第一句。第二句。",
  citations: [],
  sentence_evidence: [
    { sentence: "第一句。", source: "《论语·泰伯》", original: "士不可以不弘毅。", similarity: 0.91, verifiable: true },
    { sentence: "第二句。", source: "《论语·述而》", original: "仁远乎哉？", similarity: 0.88, verifiable: true },
  ],
});
assert.equal(evidencedSpeech.sentenceEvidence.length, 2);
assert.equal(evidencedSpeech.sentenceEvidence[0].source, "《论语·泰伯》");
assert.equal(evidencedSpeech.sentenceEvidence[1].verifiable, true);

assert.equal(flow.canUseInterventionBar("debating", "session-1"), true);
assert.equal(flow.canUseInterventionBar("complete", "session-1"), true);
assert.equal(flow.canUseInterventionBar("select", "session-1"), false);
assert.equal(flow.canUseInterventionBar("debating", null), false);
assert.equal(flow.shouldQueueIntervention("debating"), true);
assert.equal(flow.shouldQueueIntervention("debating", false), false);
assert.equal(flow.shouldQueueIntervention("complete"), false);

const graph = flow.normalizeDebateStateGraph({
  session_id: "session-1",
  current_node: "round2",
  nodes: [
    { id: "init", label: "开场建局", kind: "start" },
    { id: "round2", label: "交锋辩驳", kind: "agent_round" },
  ],
  transitions: [{ from_node: "init", to_node: "round2", action: "run_round2" }],
  trace: [{ from_node: "init", to_node: "round2", action: "run_round2", ok: true }],
});
assert.equal(graph.sessionId, "session-1");
assert.equal(graph.currentNode, "round2");
assert.equal(graph.transitions[0].fromNode, "init");
assert.equal(graph.trace[0].ok, true);

const roster = flow.normalizeGuestRoster([
  {
    sage_key: "li_bai",
    sage_name: "李白",
    era: "唐",
    core_thought: "尽兴而活",
    unlocked: true,
    collected: true,
    staying: false,
  },
]);
assert.equal(roster[0].sageKey, "li_bai");
assert.equal(roster[0].collected, true);
assert.equal(roster[0].staying, false);

assert.equal(flow.shouldAutoTriggerGuest({ phase: "complete", speechCount: 4, guestCount: 0, alreadyTriggered: false, randomValue: 0.2 }), true);
assert.equal(flow.shouldAutoTriggerGuest({ phase: "complete", speechCount: 4, guestCount: 0, alreadyTriggered: false, randomValue: 0.9 }), false);
assert.equal(flow.shouldAutoTriggerGuest({ phase: "debating", speechCount: 4, guestCount: 0, alreadyTriggered: false, randomValue: 0.2 }), false);
assert.equal(flow.shouldAutoTriggerGuest({ phase: "complete", speechCount: 4, guestCount: 1, alreadyTriggered: false, randomValue: 0.2 }), false);

console.log("roundtableFlow tests passed");

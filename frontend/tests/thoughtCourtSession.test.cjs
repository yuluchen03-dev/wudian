const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");
const session = loadTsModule("lib/thoughtCourtSession.ts");

(async () => {
  const events = [];
  const gateway = {
    async startDebate(topic, sages) { return { sessionId: "s-1", topic, participants: sages }; },
    async streamRound(_id, onEvent) {
      onEvent({ type: "sage_end", sage_key: "confucius", speech: { sage_key: "confucius", content: "孔子曰", citations: [{ source: "《论语·学而》", original: "人不知而不愠", verifiable: true }] } });
      onEvent({ type: "sage_error", sage_key: "mencius", message: "timeout" });
      onEvent({ type: "round_done", round: 1 });
    },
    async getReport() { return { report: { topic: "x", consensus: ["c"], divergences: ["d"], recommendations: [], summary: "s", participating_sages: ["孔子"] } }; },
  };

  const prepared = await session.prepareLiveCourt("x", ["confucius", "mencius", "laozi"], gateway, (event) => events.push(event));
  assert.equal(prepared.sessionId, "s-1");
  assert.equal(prepared.evidence.length, 1);
  assert.equal(prepared.citationStatus, "partial");
  assert.equal(prepared.speeches.find((s) => s.sageId === "mencius").status, "failed");
  assert.ok(events.some((event) => event.type === "REMOTE_STREAMING"));

  const broken = { ...gateway, async startDebate() { throw new Error("offline"); } };
  await assert.rejects(() => session.prepareLiveCourt("x", ["confucius"], broken, () => {}), /offline/);

  console.log("thoughtCourtSession tests passed");
})();

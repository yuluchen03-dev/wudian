import { CASES, PILOT_METRICS, SAGE_META, TRUST_STEPS } from "./court-data.js";
import { createCourtScene } from "./court-scene.js";

export const STATES = ["intake", "opening", "evidence", "debate", "weighting", "verdict", "epilogue"];
const progressMap = { intake: "intake", opening: "intake", evidence: "evidence", debate: "debate", weighting: "verdict", verdict: "verdict", epilogue: "verdict" };
const allowed = { intake: ["opening"], opening: ["evidence", "intake"], evidence: ["intake", "debate"], debate: ["evidence", "weighting"], weighting: ["debate", "verdict"], verdict: ["epilogue"], epilogue: ["intake"] };

let state = "intake";
let selectedCaseIndex = 0;
let selectedEvidence = new Set([0, 1, 2]);
let activeSage = "confucius";
let weights = { self: 34, relationship: 33, change: 33 };
let openingTimer = null;
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const canvas = $("#court-canvas");
const force2d = new URLSearchParams(location.search).has("force2d");
const scene = createCourtScene(canvas, { forceFallback: force2d, onFallback: () => document.documentElement.classList.add("is-2d-fallback") });

function currentCase() { return CASES[selectedCaseIndex]; }
function escapeHtml(value) { return String(value).replace(/[&<>"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[char]); }
function setActiveSage(sageId) { activeSage = sageId; document.documentElement.dataset.activeSage = sageId; scene.setActiveSage(sageId); renderDebate(); }

export function go(nextState, { force = false } = {}) {
  if (!STATES.includes(nextState)) return false;
  if (!force && !allowed[state]?.includes(nextState)) return false;
  window.clearTimeout(openingTimer);
  state = nextState;
  document.body.dataset.state = state;
  $$('[data-panel]').forEach((panel) => { panel.hidden = panel.dataset.panel !== state; });
  const activeProgress = progressMap[state];
  const order = ["intake", "evidence", "debate", "verdict"];
  $$('[data-progress]').forEach((button) => {
    button.classList.toggle("active", button.dataset.progress === activeProgress);
    button.classList.toggle("done", order.indexOf(button.dataset.progress) < order.indexOf(activeProgress));
  });
  scene.setState(state, { courtCase: currentCase(), evidenceIds: [...selectedEvidence], weights });
  if (state === "opening") { renderOpening(); openingTimer = window.setTimeout(() => go("evidence"), reducedMotion() ? 80 : 1500); }
  if (state === "evidence") renderEvidence();
  if (state === "debate") renderDebate();
  if (state === "weighting") renderWeights();
  if (state === "verdict") renderVerdict();
  if (state === "epilogue") renderEpilogue();
  $("#experience").focus({ preventScroll: true });
  window.scrollTo({ top: 0, behavior: "auto" });
  return true;
}

function reducedMotion() { return document.documentElement.classList.contains("reduce-motion") || matchMedia("(prefers-reduced-motion: reduce)").matches; }
function renderCases() {
  $("#case-list").innerHTML = CASES.map((item, index) => `<button class="case-button" type="button" data-case="${index}" aria-pressed="${index === selectedCaseIndex}"><span>0${index + 1}</span><b>${escapeHtml(item.question)}</b><small>${item.conflicts.map(escapeHtml).join(" · ")}</small></button>`).join("");
  $$('[data-case]').forEach((button) => button.addEventListener("click", () => { selectedCaseIndex = Number(button.dataset.case); selectedEvidence = new Set([0, 1, 2]); renderCases(); scene.setState("intake", { courtCase: currentCase(), evidenceIds: [...selectedEvidence], weights }); }));
}
function renderOpening() { const item = currentCase(); $("#opening-question").textContent = item.question; $("#opening-conflicts").innerHTML = item.conflicts.map((value) => `<span>${escapeHtml(value)}</span>`).join(""); }
function renderEvidence() {
  const item = currentCase();
  $("#evidence-count").textContent = `${selectedEvidence.size} 条已选`;
  $("#evidence-list").innerHTML = item.evidence.map((evidence, index) => `<article class="evidence-card ${selectedEvidence.has(index) ? "selected" : ""}"><span class="sage">${SAGE_META[evidence.sageId].name}举证</span><q>${escapeHtml(evidence.original)}</q><div class="source">${escapeHtml(evidence.source)} · 已核验</div><p>${escapeHtml(evidence.interpretation)}</p><p class="boundary"><b>适用边界：</b>${escapeHtml(evidence.boundary)}</p><button type="button" data-evidence="${index}" aria-pressed="${selectedEvidence.has(index)}">${selectedEvidence.has(index) ? "移出本案" : "加入本案"}</button></article>`).join("");
  $$('[data-evidence]').forEach((button) => button.addEventListener("click", () => { const index = Number(button.dataset.evidence); selectedEvidence.has(index) ? selectedEvidence.delete(index) : selectedEvidence.add(index); renderEvidence(); scene.setState("evidence", { courtCase: item, evidenceIds: [...selectedEvidence], weights }); }));
}
function relationLabel(type) { return ({ support: "支持", refute: "反驳", reframe: "重构" })[type] || type; }
function renderDebate() {
  const item = currentCase(); const speech = item.speeches.find((entry) => entry.sageId === activeSage) || item.speeches[0];
  $("#sage-tabs").innerHTML = item.speeches.map((entry) => `<button type="button" role="tab" data-sage="${entry.sageId}" aria-selected="${entry.sageId === speech.sageId}">${SAGE_META[entry.sageId].name}</button>`).join("");
  $("#speech-focus").innerHTML = `<h3>${SAGE_META[speech.sageId].name}</h3><span class="position">${escapeHtml(speech.position)}</span><p>${escapeHtml(speech.content)}</p>`;
  $("#relation-summary").innerHTML = item.relations.map((entry) => `<div class="relation-item"><b>${relationLabel(entry.type)}</b>${escapeHtml(entry.summary)}</div>`).join("");
  $$('[data-sage]').forEach((button) => button.addEventListener("click", () => setActiveSage(button.dataset.sage)));
}
function normalizedWeights() { const total = weights.self + weights.relationship + weights.change; if (total === 0) return { self: 34, relationship: 33, change: 33 }; const self = Math.round(weights.self / total * 100); const relationship = Math.round(weights.relationship / total * 100); return { self, relationship, change: 100 - self - relationship }; }
function rankedActions() { const item = currentCase(); return Object.entries(normalizedWeights()).sort((a, b) => b[1] - a[1]).map(([key]) => item.verdict.actions[key]); }
function renderWeights() {
  for (const key of ["self", "relationship", "change"]) $("#weight-" + key).value = weights[key];
  updateWeightView();
}
function updateWeightView() {
  const normalized = normalizedWeights();
  for (const key of ["self", "relationship", "change"]) $("#weight-" + key + "-output").textContent = normalized[key] + "%";
  $("#weighted-actions").innerHTML = rankedActions().map((action) => `<li>${escapeHtml(action)}</li>`).join("");
  scene.setWeights(normalized);
}
function renderVerdict() {
  const item = currentCase();
  $("#verdict-scroll").classList.remove("stamped");
  $("#show-epilogue").hidden = true;
  $("#seal-verdict").hidden = false;
  $("#verdict-scroll").innerHTML = `<h2>${item.label} · 思想判牒</h2><h3>核心矛盾</h3><p>${escapeHtml(item.verdict.conflict)}</p><h3>他们的共识</h3><ul>${item.verdict.consensus.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ul><h3>根本分歧</h3><p>${escapeHtml(item.verdict.divergence)}</p><h3>今日行动</h3><ol>${rankedActions().map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ol><h3>保留问题</h3><p>${escapeHtml(item.verdict.reservation)}</p>`;
}
function renderEpilogue() { $("#trust-chain").innerHTML = TRUST_STEPS.map((value) => `<li>${escapeHtml(value)}</li>`).join(""); $("#pilot-metrics").innerHTML = PILOT_METRICS.map((value) => `<span>${escapeHtml(value)}</span>`).join(""); }
function resetCourt() { selectedCaseIndex = 0; selectedEvidence = new Set([0, 1, 2]); activeSage = "confucius"; weights = { self: 34, relationship: 33, change: 33 }; renderCases(); go("intake", { force: true }); }

$("#open-court").addEventListener("click", () => go("opening"));
$("#enter-debate").addEventListener("click", () => { setActiveSage("confucius"); go("debate"); });
$("#enter-weighting").addEventListener("click", () => go("weighting"));
$("#build-verdict").addEventListener("click", () => go("verdict"));
$("#seal-verdict").addEventListener("click", () => { $("#verdict-scroll").classList.add("stamped"); $("#seal-verdict").hidden = true; $("#show-epilogue").hidden = false; scene.setState("verdict", { sealed: true, courtCase: currentCase(), evidenceIds: [...selectedEvidence], weights }); });
$("#show-epilogue").addEventListener("click", () => go("epilogue"));
$("#restart").addEventListener("click", resetCourt);
$$('[data-back]').forEach((button) => button.addEventListener("click", () => go(button.dataset.back)));
for (const key of ["self", "relationship", "change"]) $("#weight-" + key).addEventListener("input", (event) => { weights[key] = Number(event.target.value); updateWeightView(); });
$("#motion-toggle").addEventListener("click", (event) => { const active = !document.documentElement.classList.contains("reduce-motion"); document.documentElement.classList.toggle("reduce-motion", active); event.currentTarget.setAttribute("aria-pressed", String(active)); scene.setReducedMotion(active); });
window.addEventListener("resize", () => scene.resize());
renderCases(); renderEpilogue(); scene.setState("intake", { courtCase: currentCase(), evidenceIds: [...selectedEvidence], weights });

const assert = require("node:assert/strict");
const { loadTsModule } = require("./helpers/loadTsModule.cjs");

const {
  buildCurtain,
  constrainCurtain,
  injectPointerImpulse,
  integrateCurtain,
  isCurtainSettled,
} = loadTsModule("lib/curtainPhysics.ts");

const bounds = {
  width: 390,
  height: 720,
  buildingLeft: 10,
  buildingTop: 58,
  buildingWidth: 370,
  buildingHeight: 238,
};

const chains = buildCurtain({ text: "天 地\n玄黄宇宙洪荒", ...bounds });
assert.ok(chains.length >= 2 && chains.length <= 16);
assert.ok(chains.every((chain) => chain.length >= 2));
assert.ok(
  chains.flat().every((point) =>
    [
      point.x,
      point.y,
      point.oldX,
      point.oldY,
      point.anchorX,
      point.anchorY,
      point.restLength,
    ].every(Number.isFinite)
  )
);
assert.equal(chains.at(-1)[1].char, "天", "the first glyph belongs to the rightmost column");
assert.equal(chains.at(-1)[2].char, "地", "glyphs flow top-to-bottom within a column");
assert.equal(isCurtainSettled(chains, 0.03), true, "untouched chains start settled");

const near = chains.at(-1)[1];
const far = chains[0].at(-1);
const nearBefore = { x: near.x, y: near.y };
const farBefore = { x: far.x, y: far.y };
const impacts = injectPointerImpulse(
  chains,
  { x: near.x - 5, y: near.y },
  { x: near.x + 7, y: near.y + 2 },
  { radius: 24, strength: 0.72 }
);
assert.notDeepEqual({ x: near.x, y: near.y }, nearBefore);
assert.deepEqual({ x: far.x, y: far.y }, farBefore);
assert.ok(impacts.some((impact) => impact > 0));

const displacedX = near.x;
integrateCurtain(chains, 0.97, 0.18);
assert.notEqual(near.x, displacedX, "Verlet integration should advance an unpinned displaced point");

constrainCurtain(chains, 6);
for (const chain of chains) {
  assert.equal(chain[0].x, chain[0].anchorX);
  assert.equal(chain[0].y, chain[0].anchorY);
  for (let index = 1; index < chain.length; index += 1) {
    const previous = chain[index - 1];
    const point = chain[index];
    assert.ok(
      Math.abs(Math.hypot(point.x - previous.x, point.y - previous.y) - point.restLength) < 0.4,
      "six constraint passes should restore segment lengths within subpixel tolerance"
    );
  }
}

const tiny = buildCurtain({
  text: "序",
  width: 180,
  height: 120,
  buildingLeft: 0,
  buildingTop: 40,
  buildingWidth: 180,
  buildingHeight: 100,
});
assert.ok(tiny.length >= 2);
assert.ok(tiny.flat().every((point) => Number.isFinite(point.x) && Number.isFinite(point.y)));
assert.equal(isCurtainSettled(tiny, 0.03), true);
const settledProbe = tiny.at(-1)[1];
settledProbe.oldX = settledProbe.x - 0.05;
assert.equal(isCurtainSettled(tiny, 0.03), false, "motion above the threshold is not settled");
assert.equal(isCurtainSettled(tiny, 0.06), true, "motion below the threshold is settled");
settledProbe.oldX = settledProbe.x;

const guardedPoint = tiny.at(-1)[1];
const guardedBefore = { x: guardedPoint.x, y: guardedPoint.y };
assert.deepEqual(
  injectPointerImpulse(
    tiny,
    { x: guardedPoint.x, y: guardedPoint.y },
    { x: guardedPoint.x + 0.001, y: guardedPoint.y },
    { radius: 24, strength: 1 }
  ),
  tiny.map(() => 0),
  "negligible pointer movement should not inject an impulse"
);
assert.deepEqual(
  injectPointerImpulse(
    tiny,
    { x: guardedPoint.x, y: guardedPoint.y },
    { x: guardedPoint.x + 81, y: guardedPoint.y },
    { radius: 100, strength: 1 }
  ),
  tiny.map(() => 0),
  "implausibly fast pointer movement should not inject an impulse"
);
assert.deepEqual({ x: guardedPoint.x, y: guardedPoint.y }, guardedBefore);

assert.doesNotThrow(() => constrainCurtain([[]]), "empty chains should be ignored");

const makePoint = ({ x, y, pinned = false, restLength = 10 }) => ({
  x,
  y,
  oldX: x,
  oldY: y,
  anchorX: x,
  anchorY: y,
  pinned,
  restLength,
  char: "",
});

const freePairAnchor = makePoint({ x: 20, y: 10, pinned: true, restLength: 0 });
const upperFree = makePoint({ x: 20, y: 20 });
const lowerFree = makePoint({ x: 20, y: 20 });
constrainCurtain([[freePairAnchor, upperFree, lowerFree]], 1);
assert.deepEqual(
  { x: upperFree.x, y: upperFree.y },
  { x: 20, y: 15 },
  "coincident free points should split the correction equally upward"
);
assert.deepEqual(
  { x: lowerFree.x, y: lowerFree.y },
  { x: 20, y: 25 },
  "coincident free points should split the correction equally downward"
);

const pinnedCoincident = makePoint({ x: 24, y: 32, pinned: true, restLength: 0 });
const freeCoincident = makePoint({ x: 24, y: 32 });
constrainCurtain([[pinnedCoincident, freeCoincident]], 6);
assert.deepEqual(
  { x: freeCoincident.x, y: freeCoincident.y },
  { x: 24, y: 42 },
  "a free point should recover vertically below its coincident pinned point"
);
assert.equal(
  Math.hypot(freeCoincident.x - pinnedCoincident.x, freeCoincident.y - pinnedCoincident.y),
  10,
  "coincident pinned and free points should recover their rest length"
);

console.log("curtainPhysics tests passed");

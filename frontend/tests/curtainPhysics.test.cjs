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

console.log("curtainPhysics tests passed");

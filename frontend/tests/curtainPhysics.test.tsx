import { describe, it, expect } from "vitest";
import {
  buildCurtain,
  constrainCurtain,
  injectPointerImpulse,
  integrateCurtain,
  isCurtainSettled,
} from "../lib/curtainPhysics";

describe("curtainPhysics", () => {
  const bounds = {
    width: 390,
    height: 720,
    buildingLeft: 10,
    buildingTop: 58,
    buildingWidth: 370,
    buildingHeight: 238,
  };

  it("builds curtain chains with valid structure", () => {
    const chains = buildCurtain({ text: "天 地\n玄黄宇宙洪荒", ...bounds });
    expect(chains.length).toBeGreaterThanOrEqual(2);
    expect(chains.length).toBeLessThanOrEqual(16);
    expect(chains.every((chain) => chain.length >= 2)).toBe(true);
    expect(
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
    ).toBe(true);
  });

  it("preserves glyph ordering in chains", () => {
    const chains = buildCurtain({ text: "天 地\n玄黄宇宙洪荒", ...bounds });
    expect(chains.at(-1)[1].char).toBe("天", "the first glyph belongs to the rightmost column");
    expect(chains.at(-1)[2].char).toBe("地", "glyphs flow top-to-bottom within a column");
  });

  it("settled chains start settled", () => {
    const chains = buildCurtain({ text: "天 地\n玄黄宇宙洪荒", ...bounds });
    expect(isCurtainSettled(chains, 0.03)).toBe(true, "untouched chains start settled");
  });

  it("injects pointer impulse and displaces points", () => {
    const chains = buildCurtain({ text: "天 地\n玄黄宇宙洪荒", ...bounds });
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
    expect({ x: near.x, y: near.y }).not.toEqual(nearBefore);
    expect({ x: far.x, y: far.y }).toEqual(farBefore);
    expect(impacts.some((impact) => impact > 0)).toBe(true);
  });

  it("advances point via Verlet integration", () => {
    const chains = buildCurtain({ text: "天 地\n玄黄宇宙洪荒", ...bounds });
    const near = chains.at(-1)[2];
    // Set oldX to create velocity for Verlet integration
    near.oldX = near.x - 0.05;
    const displacedX = near.x;
    integrateCurtain(chains, 0.97, 0.18);
    expect(near.x).not.toBe(displacedX, "Verlet integration should advance an unpinned displaced point");
  });

  it("constrains curtain and restores segment lengths", () => {
    const chains = buildCurtain({ text: "天 地\n玄黄宇宙洪荒", ...bounds });
    constrainCurtain(chains, 6);
    for (const chain of chains) {
      expect(chain[0].x).toBe(chain[0].anchorX);
      expect(chain[0].y).toBe(chain[0].anchorY);
      for (let index = 1; index < chain.length; index += 1) {
        const previous = chain[index - 1];
        const point = chain[index];
        expect(
          Math.abs(Math.hypot(point.x - previous.x, point.y - previous.y) - point.restLength) < 0.4,
          "six constraint passes should restore segment lengths within subpixel tolerance"
        ).toBe(true);
      }
    }
  });

  it("validates tiny curtain", () => {
    const tiny = buildCurtain({
      text: "序",
      width: 180,
      height: 120,
      buildingLeft: 0,
      buildingTop: 40,
      buildingWidth: 180,
      buildingHeight: 100,
    });
    expect(tiny.length).toBeGreaterThanOrEqual(2);
    expect(tiny.flat().every((point) => Number.isFinite(point.x) && Number.isFinite(point.y))).toBe(true);
    expect(isCurtainSettled(tiny, 0.03)).toBe(true);
  });

  it("detects motion above threshold", () => {
    const tiny = buildCurtain({
      text: "序",
      width: 180,
      height: 120,
      buildingLeft: 0,
      buildingTop: 40,
      buildingWidth: 180,
      buildingHeight: 100,
    });
    const settledProbe = tiny.at(-1)[1];
    settledProbe.oldX = settledProbe.x - 0.05;
    expect(isCurtainSettled(tiny, 0.03)).toBe(false, "motion above the threshold is not settled");
    expect(isCurtainSettled(tiny, 0.06)).toBe(true, "motion below the threshold is settled");
    settledProbe.oldX = settledProbe.x;
  });

  it("negligible pointer movement does not inject impulse", () => {
    const tiny = buildCurtain({
      text: "序",
      width: 180,
      height: 120,
      buildingLeft: 0,
      buildingTop: 40,
      buildingWidth: 180,
      buildingHeight: 100,
    });
    const guardedPoint = tiny.at(-1)[1];
    const guardedBefore = { x: guardedPoint.x, y: guardedPoint.y };

    expect(
      injectPointerImpulse(
        tiny,
        { x: guardedPoint.x, y: guardedPoint.y },
        { x: guardedPoint.x + 0.001, y: guardedPoint.y },
        { radius: 24, strength: 1 }
      )
    ).toEqual(tiny.map(() => 0), "negligible pointer movement should not inject an impulse");

    expect(
      injectPointerImpulse(
        tiny,
        { x: guardedPoint.x, y: guardedPoint.y },
        { x: guardedPoint.x + 81, y: guardedPoint.y },
        { radius: 100, strength: 1 }
      )
    ).toEqual(tiny.map(() => 0), "implausibly fast pointer movement should not inject an impulse");

    expect({ x: guardedPoint.x, y: guardedPoint.y }).toEqual(guardedBefore);
  });

  it("ignores empty chains", () => {
    expect(() => constrainCurtain([[]])).not.toThrow("empty chains should be ignored");
  });

  it("splits correction equally for coincident free points", () => {
    const makePoint = ({ x, y, pinned = false, restLength = 10 }) => ({
      x, y, oldX: x, oldY: y, anchorX: x, anchorY: y, pinned, restLength, char: "",
    });

    const freePairAnchor = makePoint({ x: 20, y: 10, pinned: true, restLength: 0 });
    const upperFree = makePoint({ x: 20, y: 20 });
    const lowerFree = makePoint({ x: 20, y: 20 });
    constrainCurtain([[freePairAnchor, upperFree, lowerFree]], 1);
    expect({ x: upperFree.x, y: upperFree.y }).toEqual({ x: 20, y: 15 }, "coincident free points should split the correction equally upward");
    expect({ x: lowerFree.x, y: lowerFree.y }).toEqual({ x: 20, y: 25 }, "coincident free points should split the correction equally downward");
  });

  it("recovers free point below coincident pinned point", () => {
    const makePoint = ({ x, y, pinned = false, restLength = 10 }) => ({
      x, y, oldX: x, oldY: y, anchorX: x, anchorY: y, pinned, restLength, char: "",
    });

    const pinnedCoincident = makePoint({ x: 24, y: 32, pinned: true, restLength: 0 });
    const freeCoincident = makePoint({ x: 24, y: 32 });
    constrainCurtain([[pinnedCoincident, freeCoincident]], 6);
    expect({ x: freeCoincident.x, y: freeCoincident.y }).toEqual({ x: 24, y: 42 }, "a free point should recover vertically below its coincident pinned point");
    expect(Math.hypot(freeCoincident.x - pinnedCoincident.x, freeCoincident.y - pinnedCoincident.y)).toBe(10, "coincident pinned and free points should recover their rest length");
  });
});

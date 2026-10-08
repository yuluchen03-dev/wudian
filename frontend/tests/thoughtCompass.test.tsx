import { describe, it, expect } from "vitest";
import { analyzeThoughtCompass, normalizeBackendThoughtCompass } from "../lib/thoughtCompass";

describe("thoughtCompass", () => {
  it("analyzes a statement and returns the correct label", () => {
    const mark = analyzeThoughtCompass("我觉得卷不动了就该歇着，人不该被工作绑架，但也想做真正有意义的事。");
    expect(mark.label).toBe("逍遥实干派");
  });

  it("returns valid percentage ranges", () => {
    const mark = analyzeThoughtCompass("我觉得卷不动了就该歇着，人不该被工作绑架，但也想做真正有意义的事。");
    expect(mark.activePercent).toBeGreaterThanOrEqual(30);
    expect(mark.activePercent).toBeLessThanOrEqual(55);
    expect(mark.quietPercent).toBeGreaterThan(mark.activePercent);
  });

  it("identifies the nearest school", () => {
    const mark = analyzeThoughtCompass("我觉得卷不动了就该歇着，人不该被工作绑架，但也想做真正有意义的事。");
    expect(mark.nearestSchool).toBe("儒道之间");
  });

  it("includes label in imprint", () => {
    const mark = analyzeThoughtCompass("我觉得卷不动了就该歇着，人不该被工作绑架，但也想做真正有意义的事。");
    expect(mark.imprint).toMatch(/逍遥实干派/);
  });

  it("normalizes backend thought compass payload", () => {
    const backendMark = normalizeBackendThoughtCompass({
      x: 42,
      y: 51,
      active_percent: 42,
      quiet_percent: 58,
      nearest_school: "儒道之间",
      label: "逍遥实干派",
      imprint: "今日论道，你自成一家，我们称之为「逍遥实干派」。",
    });
    expect(backendMark.activePercent).toBe(42);
    expect(backendMark.quietPercent).toBe(58);
    expect(backendMark.nearestSchool).toBe("儒道之间");
  });
});

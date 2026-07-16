export type CurtainPoint = {
  x: number;
  y: number;
  oldX: number;
  oldY: number;
  anchorX: number;
  anchorY: number;
  pinned: boolean;
  restLength: number;
  char: string;
};

export type CurtainChain = CurtainPoint[];

export type CurtainBuildOptions = {
  text: string;
  width: number;
  height: number;
  buildingLeft: number;
  buildingTop: number;
  buildingWidth: number;
  buildingHeight: number;
};

export type PointerPoint = { x: number; y: number };

const clamp = (value: number, minimum: number, maximum: number) =>
  Math.max(minimum, Math.min(maximum, value));

export function buildCurtain(options: CurtainBuildOptions): CurtainChain[] {
  const glyphs = Array.from(options.text.replace(/\s+/g, ""));
  const narrow = options.width < 720;
  const maxColumns = narrow ? 16 : 26;
  const spacing = 17;
  const minimumRows = Math.max(2, Math.ceil((narrow ? 260 : 360) / spacing));
  const rowCapacity = Math.max(1, minimumRows - 1);
  const columns = clamp(Math.ceil(Math.max(1, glyphs.length) / rowCapacity), 2, maxColumns);
  const imageBottom = options.buildingTop + options.buildingHeight - 2;
  const requiredRows = Math.max(2, Math.ceil(Math.max(1, glyphs.length) / columns) + 1);
  const availableRows = Math.max(2, Math.floor((options.height - 48 - imageBottom) / spacing) + 1);
  const rows = Math.max(2, Math.min(availableRows, Math.max(minimumRows, requiredRows)));
  const center = options.buildingLeft + options.buildingWidth / 2;
  const curtainWidth = Math.max(1, options.buildingWidth * 0.84);
  const left = center - curtainWidth / 2;
  const top = imageBottom + 16;
  const curtainBottom = imageBottom + (rows - 1) * spacing;
  const restLength = Math.max(6.4, (curtainBottom - top) / Math.max(1, rows - 1));

  return Array.from({ length: columns }, (_, column) => {
    const x = left + (column * curtainWidth) / Math.max(1, columns - 1);
    const readingColumn = columns - 1 - column;

    return Array.from({ length: rows }, (_, row) => {
      const y = top + row * restLength;
      const glyphIndex = readingColumn * (rows - 1) + row - 1;

      return {
        x,
        y,
        oldX: x,
        oldY: y,
        anchorX: x,
        anchorY: y,
        pinned: row === 0,
        restLength,
        char: row > 0 ? glyphs[glyphIndex] ?? "" : "",
      };
    });
  });
}

export function injectPointerImpulse(
  chains: CurtainChain[],
  previous: PointerPoint,
  current: PointerPoint,
  options: { radius: number; strength: number }
): number[] {
  const moveX = current.x - previous.x;
  const moveY = current.y - previous.y;
  const speed = Math.hypot(moveX, moveY);
  const impacts = chains.map(() => 0);

  if (speed < 0.01 || speed > 80) return impacts;

  chains.forEach((chain, chainIndex) => {
    for (let index = 1; index < chain.length; index += 1) {
      const point = chain[index];
      const distance = Math.hypot(point.x - previous.x, point.y - previous.y);
      if (distance >= options.radius) continue;

      const falloff = 1 - distance / options.radius;
      point.x += moveX * options.strength * falloff;
      point.y += moveY * options.strength * falloff;
      impacts[chainIndex] = Math.max(impacts[chainIndex], speed * falloff);
    }
  });

  return impacts;
}

export function integrateCurtain(chains: CurtainChain[], friction: number, gravity: number): void {
  for (const chain of chains) {
    for (const point of chain) {
      if (point.pinned) continue;

      const velocityX = (point.x - point.oldX) * friction;
      const velocityY = (point.y - point.oldY) * friction;
      point.oldX = point.x;
      point.oldY = point.y;
      point.x += velocityX;
      point.y += velocityY + gravity;
    }
  }
}

export function constrainCurtain(chains: CurtainChain[], passes = 6): void {
  for (let pass = 0; pass < passes; pass += 1) {
    for (const chain of chains) {
      const anchor = chain[0];
      anchor.x = anchor.anchorX;
      anchor.y = anchor.anchorY;

      for (let index = 1; index < chain.length; index += 1) {
        const previous = chain[index - 1];
        const point = chain[index];
        const dx = point.x - previous.x;
        const dy = point.y - previous.y;
        const distance = Math.max(0.0001, Math.hypot(dx, dy));
        const difference = (distance - point.restLength) / distance;

        if (previous.pinned) {
          point.x -= dx * difference;
          point.y -= dy * difference;
        } else {
          const correctionX = dx * difference * 0.5;
          const correctionY = dy * difference * 0.5;
          previous.x += correctionX;
          previous.y += correctionY;
          point.x -= correctionX;
          point.y -= correctionY;
        }
      }
    }
  }
}

export function isCurtainSettled(chains: CurtainChain[], threshold: number): boolean {
  return chains.every((chain) =>
    chain.every(
      (point) => point.pinned || Math.hypot(point.x - point.oldX, point.y - point.oldY) <= threshold
    )
  );
}

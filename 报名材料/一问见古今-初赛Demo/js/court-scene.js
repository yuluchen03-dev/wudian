import * as THREE from "./three.module.min.js";

const STATE_CAMERA = {
  intake: [0, 5.2, 13.5], opening: [0, 4.5, 9.2], evidence: [0, 7.2, 8.5],
  debate: [0, 4.8, 9.4], weighting: [0, 6.2, 10.2], verdict: [0, 7.8, 7.4], epilogue: [0, 8.5, 14.5],
};
const SAGE_POSITIONS = { confucius: [-3.8, 0, .4], mencius: [3.8, 0, .4], laozi: [0, 0, -3.8] };
const PORTRAIT_PATHS = {
  confucius: "assets/confucius.png",
  mencius: "assets/mencius.png",
  laozi: "assets/laozi.png",
};

export function createCourtScene(canvas, { forceFallback = false, onFallback = () => {} } = {}) {
  if (forceFallback) {
    document.documentElement.classList.add("is-2d-fallback"); onFallback(new Error("Forced 2D fallback")); return noScene();
  }
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false, powerPreference: "high-performance" });
  } catch (error) {
    document.documentElement.classList.add("is-2d-fallback"); onFallback(error); return noScene();
  }

  const world = new THREE.Scene();
  world.background = new THREE.Color(0x0d1413);
  world.fog = new THREE.FogExp2(0x0d1413, .035);
  const camera = new THREE.PerspectiveCamera(42, 1, .1, 80);
  camera.position.set(...STATE_CAMERA.intake);
  const targetCamera = new THREE.Vector3(...STATE_CAMERA.intake);
  const lookTarget = new THREE.Vector3(0, 1.1, 0);
  const clock = new THREE.Clock();
  let state = "intake";
  let activeSage = "confucius";
  let reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let destroyed = false;
  let sealed = false;
  let sampleFrames = 0;
  let sampleTime = 0;

  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, innerWidth < 768 ? 1.5 : 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const hemi = new THREE.HemisphereLight(0xbfd8d2, 0x111412, 1.8); world.add(hemi);
  const key = new THREE.SpotLight(0xf0d8a3, 42, 32, Math.PI / 5, .55, 1.3); key.position.set(-5, 10, 8); key.castShadow = true; world.add(key);
  const jadeLight = new THREE.PointLight(0x4f988c, 18, 18); jadeLight.position.set(5, 3, 2); world.add(jadeLight);
  const redLight = new THREE.PointLight(0xa93629, 10, 14); redLight.position.set(-4, 2, 1); world.add(redLight);

  const floor = new THREE.Mesh(new THREE.CylinderGeometry(8.5, 8.8, .28, 64), new THREE.MeshStandardMaterial({ color: 0x111a18, roughness: .82, metalness: .12 }));
  floor.position.y = -.22; floor.receiveShadow = true; world.add(floor);
  for (const radius of [2.4, 5.2, 8]) {
    const ring = new THREE.Mesh(new THREE.RingGeometry(radius - .018, radius + .018, 96), new THREE.MeshBasicMaterial({ color: radius === 5.2 ? 0x4f988c : 0x6d6c5c, transparent: true, opacity: radius === 5.2 ? .34 : .18, side: THREE.DoubleSide }));
    ring.rotation.x = -Math.PI / 2; ring.position.y = -.065; world.add(ring);
  }
  const rays = new THREE.Group();
  for (let i = 0; i < 12; i++) {
    const ray = new THREE.Mesh(new THREE.BoxGeometry(.025, .015, 7.4), new THREE.MeshBasicMaterial({ color: 0x4f988c, transparent: true, opacity: .1 }));
    ray.rotation.y = i * Math.PI / 6; ray.position.y = -.04; rays.add(ray);
  }
  world.add(rays);

  const dossier = createDossier(); world.add(dossier);
  const evidenceBooks = [createBook(0xb54836), createBook(0xc6a765), createBook(0x4f988c)];
  evidenceBooks.forEach((book, index) => { book.position.set((index - 1) * 2.2, .2, 1.7); book.rotation.y = (index - 1) * -.12; world.add(book); });

  const textureLoader = new THREE.TextureLoader();
  const portraitSeats = {
    confucius: createPortraitSeat("confucius", 0xb54836, PORTRAIT_PATHS.confucius, textureLoader),
    mencius: createPortraitSeat("mencius", 0xc6a765, PORTRAIT_PATHS.mencius, textureLoader),
    laozi: createPortraitSeat("laozi", 0x4f988c, PORTRAIT_PATHS.laozi, textureLoader),
  };
  const startsMobile = canvas.clientWidth < 768;
  Object.entries(portraitSeats).forEach(([id, seat]) => {
    seat.position.set(...(startsMobile ? [0, 0, .6] : SAGE_POSITIONS[id]));
    seat.visible = !startsMobile || id === activeSage;
    world.add(seat);
  });

  const relationGroup = new THREE.Group(); world.add(relationGroup);
  const particles = createDust(); world.add(particles);

  function setRelations(relations = []) {
    relationGroup.clear();
    relations.forEach((relation, index) => {
      const from = new THREE.Vector3(...SAGE_POSITIONS[relation.from]).add(new THREE.Vector3(0, 1.6, 0));
      const to = new THREE.Vector3(...SAGE_POSITIONS[relation.to]).add(new THREE.Vector3(0, 1.6, 0));
      const mid = from.clone().lerp(to, .5); mid.y += .8 + index * .22;
      const curve = new THREE.QuadraticBezierCurve3(from, mid, to);
      const color = relation.type === "refute" ? 0xa93629 : relation.type === "reframe" ? 0xc6a765 : 0x4f988c;
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(42)), new THREE.LineBasicMaterial({ color, transparent: true, opacity: .8 }));
      line.userData.type = relation.type; relationGroup.add(line);
    });
  }

  function setState(nextState, context = {}) {
    state = nextState;
    sealed = Boolean(context.sealed);
    targetCamera.set(...(STATE_CAMERA[nextState] || STATE_CAMERA.intake));
    const showBooks = ["evidence", "debate", "weighting", "verdict"].includes(nextState);
    evidenceBooks.forEach((book, index) => { book.visible = showBooks && (context.evidenceIds || [0, 1, 2]).includes(index); });
    relationGroup.visible = ["debate", "weighting", "verdict"].includes(nextState);
    setRelations(context.courtCase?.relations || []);
    dossier.visible = nextState !== "intake" && nextState !== "epilogue";
    dossier.userData.paper.material.color.setHex(sealed ? 0xf6efe0 : 0xe8e1d3);
    particles.visible = !reduced && ["opening", "evidence", "debate"].includes(nextState);
    if (nextState === "intake") setActiveSage("confucius");
  }

  function setActiveSage(sageId) { activeSage = sageId in portraitSeats ? sageId : "confucius"; }
  function setWeights(values) {
    const normalized = values || { self: 34, relationship: 33, change: 33 };
    portraitSeats.confucius.userData.weight = normalized.relationship / 100;
    portraitSeats.mencius.userData.weight = normalized.self / 100;
    portraitSeats.laozi.userData.weight = normalized.change / 100;
    jadeLight.intensity = 12 + normalized.relationship * .11;
    redLight.intensity = 7 + normalized.change * .1;
  }
  function setReducedMotion(value) { reduced = Boolean(value); particles.visible = !reduced && ["opening", "evidence", "debate"].includes(state); }
  function resize() {
    const width = Math.max(1, canvas.clientWidth); const height = Math.max(1, canvas.clientHeight);
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, width < 768 ? 1.5 : 2));
    renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix();
  }

  function animate() {
    if (destroyed) return;
    requestAnimationFrame(animate);
    const delta = Math.min(clock.getDelta(), .08); const time = clock.elapsedTime;
    sampleFrames += 1; sampleTime += delta;
    if (sampleFrames === 60) {
      const average = sampleTime / sampleFrames;
      if (average > .032) { renderer.shadowMap.enabled = false; document.documentElement.classList.add("degraded-motion"); }
      if (average > .06) { document.documentElement.classList.add("is-2d-fallback"); onFallback(new Error("Low WebGL performance")); }
    }
    const easing = reduced ? 1 : 1 - Math.pow(.001, delta);
    camera.position.lerp(targetCamera, easing);
    camera.lookAt(lookTarget);
    const isMobile = canvas.clientWidth < 768;
    Object.entries(portraitSeats).forEach(([id, seat], index) => {
      const isActive = id === activeSage;
      const isDebating = isActive && state === "debate";
      const base = isMobile ? [0, 0, .6] : SAGE_POSITIONS[id];
      const weightLift = state === "weighting" ? (seat.userData.weight || .33) * .7 : 0;
      const bob = reduced ? 0 : Math.sin(time * 1.15 + index) * .035;
      const targetOpacity = state === "debate" ? (isActive ? 1 : .38) : .92;
      const targetGlow = state === "debate" ? (isActive ? .58 : .05) : .16;
      seat.visible = !isMobile || isActive;
      seat.position.x += (base[0] - seat.position.x) * easing;
      seat.position.y += (bob + weightLift - seat.position.y) * easing;
      seat.position.z += (base[2] + (!isMobile && isDebating ? 1.05 : 0) - seat.position.z) * easing;
      seat.rotation.y += ((!isMobile && isDebating ? -Math.atan2(base[0], 8) : 0) - seat.rotation.y) * easing;
      seat.userData.fadeMaterials.forEach((material) => { material.opacity += (targetOpacity - material.opacity) * easing; });
      seat.userData.glowMaterial.opacity += (targetGlow - seat.userData.glowMaterial.opacity) * easing;
      seat.userData.accentMaterial.emissiveIntensity += ((isDebating ? .8 : .25) - seat.userData.accentMaterial.emissiveIntensity) * easing;
    });
    if (!reduced) particles.rotation.y += delta * .018;
    dossier.rotation.y += ((sealed ? -.08 : 0) - dossier.rotation.y) * easing;
    renderer.render(world, camera);
  }

  resize(); animate();
  return { setState, setActiveSage, setWeights, setReducedMotion, resize, destroy() { destroyed = true; renderer.dispose(); } };
}

function createPortraitSeat(id, accentColor, texturePath, textureLoader) {
  const group = new THREE.Group(); group.name = id;
  const darkMaterial = new THREE.MeshStandardMaterial({ color: 0x111715, roughness: .58, metalness: .32, transparent: true });
  const accentMaterial = new THREE.MeshStandardMaterial({ color: accentColor, emissive: accentColor, emissiveIntensity: .25, roughness: .42, metalness: .44, transparent: true });
  const plinthMaterial = new THREE.MeshStandardMaterial({ color: 0x202926, roughness: .62, metalness: .3, transparent: true });
  const portraitMaterial = new THREE.MeshBasicMaterial({ color: accentColor, transparent: true });
  const glowMaterial = new THREE.MeshBasicMaterial({
    color: accentColor, transparent: true, opacity: .16, blending: THREE.AdditiveBlending, depthWrite: false,
  });

  const glow = new THREE.Mesh(new THREE.PlaneGeometry(3.35, 3.7), glowMaterial); glow.position.set(0, 2.05, -.19); group.add(glow);
  const backPanel = new THREE.Mesh(new THREE.BoxGeometry(2.9, 3.25, .32), darkMaterial); backPanel.position.y = 2.05; backPanel.castShadow = true; group.add(backPanel);
  const portrait = new THREE.Mesh(new THREE.PlaneGeometry(2.42, 2.42), portraitMaterial); portrait.position.set(0, 2.08, .171); group.add(portrait);
  for (const x of [-1.52, 1.52]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(.18, 3.4, .42), accentMaterial); post.position.set(x, 2.02, .02); post.castShadow = true; group.add(post);
  }
  const cap = new THREE.Mesh(new THREE.BoxGeometry(3.22, .2, .42), accentMaterial); cap.position.set(0, 3.75, .02); cap.castShadow = true; group.add(cap);
  const plinth = new THREE.Mesh(new THREE.BoxGeometry(3.55, .3, 1.25), plinthMaterial); plinth.position.y = .15; plinth.castShadow = true; plinth.receiveShadow = true; group.add(plinth);
  const riser = new THREE.Mesh(new THREE.BoxGeometry(2.9, .42, .82), darkMaterial); riser.position.y = .43; riser.castShadow = true; group.add(riser);

  const portraitTexture = textureLoader.load(
    texturePath,
    (texture) => {
      const width = texture.image?.naturalWidth || texture.image?.width || 1;
      const height = texture.image?.naturalHeight || texture.image?.height || 1;
      const aspect = width / height;
      portrait.scale.set(aspect > 1 ? 1 : aspect, aspect > 1 ? 1 / aspect : 1, 1);
      portraitMaterial.color.setHex(0xffffff);
      portraitMaterial.map = texture;
      portraitMaterial.needsUpdate = true;
    },
    undefined,
    () => {
      portraitMaterial.map = null;
      portraitMaterial.color.setHex(accentColor);
      portraitMaterial.needsUpdate = true;
    },
  );
  portraitTexture.colorSpace = THREE.SRGBColorSpace;

  group.userData = {
    weight: .33,
    fadeMaterials: [darkMaterial, accentMaterial, plinthMaterial, portraitMaterial],
    glowMaterial,
    accentMaterial,
  };
  return group;
}
function createDossier() {
  const group = new THREE.Group();
  const base = new THREE.Mesh(new THREE.BoxGeometry(3.5, .16, 2.25), new THREE.MeshStandardMaterial({ color: 0x372c25, roughness: .72 })); base.castShadow = true; group.add(base);
  const paperMaterial = new THREE.MeshStandardMaterial({ color: 0xe8e1d3, roughness: .9 });
  const paper = new THREE.Mesh(new THREE.BoxGeometry(3.18, .07, 2), paperMaterial); paper.position.y = .13; paper.castShadow = true; group.add(paper);
  const seal = new THREE.Mesh(new THREE.CylinderGeometry(.27, .27, .055, 24), new THREE.MeshStandardMaterial({ color: 0xa93629, roughness: .6 })); seal.position.set(1.12, .19, .62); group.add(seal);
  group.position.set(0, .08, .2); group.userData.paper = paper; return group;
}
function createBook(color) {
  const group = new THREE.Group(); const cover = new THREE.MeshStandardMaterial({ color, roughness: .65 }); const page = new THREE.MeshStandardMaterial({ color: 0xdcd3c3, roughness: .95 });
  const pages = new THREE.Mesh(new THREE.BoxGeometry(1.25, .22, 1.75), page); pages.castShadow = true; group.add(pages);
  for (const y of [-.16, .16]) { const slab = new THREE.Mesh(new THREE.BoxGeometry(1.34, .07, 1.86), cover); slab.position.y = y; slab.castShadow = true; group.add(slab); }
  return group;
}
function createDust() {
  const geometry = new THREE.BufferGeometry(); const positions = new Float32Array(240 * 3);
  for (let i = 0; i < positions.length; i += 3) { positions[i] = (Math.random() - .5) * 18; positions[i + 1] = Math.random() * 8; positions[i + 2] = (Math.random() - .5) * 14; }
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  return new THREE.Points(geometry, new THREE.PointsMaterial({ color: 0xc6a765, size: .025, transparent: true, opacity: .32 }));
}
function noScene() { return { setState() {}, setActiveSage() {}, setWeights() {}, setReducedMotion() {}, resize() {}, destroy() {} }; }

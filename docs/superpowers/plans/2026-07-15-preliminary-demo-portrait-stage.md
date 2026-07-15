# Preliminary Demo Portrait Stage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the toy-like procedural sage figures with three recognizable, locally textured portrait seats while preserving the offline 3D thought-court flow.

**Architecture:** Keep the DOM state machine and public scene API unchanged. Replace only the Three.js character factory and character animation with framed portrait-seat groups built from local PNG textures, then update the one UI hint that describes how users focus a sage.

**Tech Stack:** HTML5, JavaScript ES modules, local Three.js 0.180.0, Node.js source validation, PowerShell ZIP packaging, in-app browser QA.

---

## File Map

- Modify: `报名材料/validate-preliminary-demo.cjs` - assert portrait textures are used by the scene and geometric people are absent.
- Modify: `报名材料/悟典-初赛Demo/js/court-scene.js` - replace `createSage` with `createPortraitSeat` and animate whole portrait seats.
- Modify: `报名材料/悟典-初赛Demo/index.html` - rename the focus hint from a person action to a portrait-seat action.
- Modify: `报名材料/悟典-思想审判场-初赛Demo.zip` - rebuild the final upload artifact.

### Task 1: Lock the portrait-stage contract

**Files:**
- Modify: `报名材料/validate-preliminary-demo.cjs`
- Test: `报名材料/悟典-初赛Demo/js/court-scene.js`
- Test: `报名材料/悟典-初赛Demo/index.html`

- [ ] **Step 1: Add failing source assertions**

Add these assertions after the existing Three.js scene assertions:

```js
for (const portrait of ["confucius.png", "mencius.png", "laozi.png"]) {
  assert.ok(scene.includes(portrait), `3D scene must load ${portrait}`);
}
assert.match(scene, /THREE\.TextureLoader/, "3D portrait seats must use local textures");
assert.match(scene, /createPortraitSeat/, "3D portrait-seat factory is required");
assert.doesNotMatch(scene, /createSage|IcosahedronGeometry|userData\.arm/, "Geometric sage dolls must be removed");
assert.match(html, /点击肖像切换立场/, "Debate hint must describe portrait interaction honestly");
```

- [ ] **Step 2: Run the validator and confirm the expected failure**

Run:

```powershell
node 报名材料\validate-preliminary-demo.cjs
```

Expected: FAIL because `court-scene.js` does not contain `confucius.png` and still contains `createSage`.

- [ ] **Step 3: Commit the failing contract**

```powershell
git add -- 报名材料/validate-preliminary-demo.cjs
git commit -m "test: require recognizable portrait seats"
```

### Task 2: Replace geometric figures with textured portrait seats

**Files:**
- Modify: `报名材料/悟典-初赛Demo/js/court-scene.js`
- Test: `报名材料/validate-preliminary-demo.cjs`

- [ ] **Step 1: Define portrait metadata beside the seat positions**

```js
const PORTRAIT_PATHS = {
  confucius: "assets/confucius.png",
  mencius: "assets/mencius.png",
  laozi: "assets/laozi.png",
};
```

- [ ] **Step 2: Replace the sage construction block**

Create one shared texture loader and three portrait groups:

```js
const textureLoader = new THREE.TextureLoader();
const portraitSeats = {
  confucius: createPortraitSeat("confucius", 0xb54836, PORTRAIT_PATHS.confucius, textureLoader),
  mencius: createPortraitSeat("mencius", 0xc6a765, PORTRAIT_PATHS.mencius, textureLoader),
  laozi: createPortraitSeat("laozi", 0x4f988c, PORTRAIT_PATHS.laozi, textureLoader),
};
Object.entries(portraitSeats).forEach(([id, seat]) => {
  seat.position.set(...SAGE_POSITIONS[id]);
  world.add(seat);
});
```

- [ ] **Step 3: Add the complete portrait-seat factory**

```js
function createPortraitSeat(id, accentColor, texturePath, textureLoader) {
  const group = new THREE.Group();
  group.name = `${id}-portrait-seat`;

  const stone = new THREE.MeshStandardMaterial({ color: 0x151d1b, roughness: .72, metalness: .24 });
  const accent = new THREE.MeshStandardMaterial({ color: accentColor, emissive: accentColor, emissiveIntensity: .18, roughness: .5, metalness: .38 });
  const portraitMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: .9, toneMapped: false });
  const texture = textureLoader.load(texturePath, (loaded) => {
    loaded.colorSpace = THREE.SRGBColorSpace;
    loaded.needsUpdate = true;
    portraitMaterial.map = loaded;
    portraitMaterial.needsUpdate = true;
  }, undefined, () => {
    portraitMaterial.map = null;
    portraitMaterial.color.setHex(accentColor);
    portraitMaterial.opacity = .32;
    portraitMaterial.needsUpdate = true;
  });
  texture.colorSpace = THREE.SRGBColorSpace;
  portraitMaterial.map = texture;

  const back = new THREE.Mesh(new THREE.BoxGeometry(2.42, 2.9, .22), stone);
  back.position.y = 1.55;
  back.castShadow = true;
  group.add(back);

  const portrait = new THREE.Mesh(new THREE.PlaneGeometry(2.08, 2.08), portraitMaterial);
  portrait.position.set(0, 1.72, .125);
  group.add(portrait);

  for (const x of [-1.17, 1.17]) {
    const post = new THREE.Mesh(new THREE.BoxGeometry(.08, 2.75, .12), accent);
    post.position.set(x, 1.55, .2);
    group.add(post);
  }
  const cap = new THREE.Mesh(new THREE.BoxGeometry(2.5, .09, .16), accent);
  cap.position.set(0, 2.96, .2);
  group.add(cap);

  const plinth = new THREE.Mesh(new THREE.BoxGeometry(2.72, .28, .72), stone);
  plinth.position.y = .08;
  plinth.castShadow = true;
  plinth.receiveShadow = true;
  group.add(plinth);

  const glow = new THREE.Mesh(new THREE.PlaneGeometry(2.25, 2.25), new THREE.MeshBasicMaterial({ color: accentColor, transparent: true, opacity: .08, side: THREE.DoubleSide }));
  glow.position.set(0, 1.72, -.13);
  group.add(glow);

  group.userData = { portrait, accent, glow, weight: .33 };
  return group;
}
```

- [ ] **Step 4: Retarget scene state, weights, and animation**

Replace all `sages` references with `portraitSeats`. `setWeights` must set the same three semantic weights on portrait seats. In `animate`, move and turn the whole seat, adjust portrait opacity and glow opacity, and remove all arm rotations:

```js
Object.entries(portraitSeats).forEach(([id, seat], index) => {
  const base = SAGE_POSITIONS[id];
  const isActive = id === activeSage && state === "debate";
  const weightLift = state === "weighting" ? (seat.userData.weight || .33) * .55 : 0;
  const mobile = canvas.clientWidth < 768;
  const targetBase = mobile ? [0, 0, .6] : base;
  seat.visible = !mobile || id === activeSage;
  seat.position.x += (targetBase[0] - seat.position.x) * easing;
  seat.position.y += ((reduced ? 0 : Math.sin(time * .75 + index) * .018) + weightLift - seat.position.y) * easing;
  seat.position.z += (targetBase[2] + (isActive ? 1.05 : 0) - seat.position.z) * easing;
  seat.rotation.y += ((isActive && !mobile ? -Math.atan2(base[0], 8) : 0) - seat.rotation.y) * easing;
  seat.userData.portrait.material.opacity += ((isActive || state !== "debate" ? .94 : .48) - seat.userData.portrait.material.opacity) * easing;
  seat.userData.glow.material.opacity += ((isActive ? .28 : .08) - seat.userData.glow.material.opacity) * easing;
});
```

- [ ] **Step 5: Run validation and syntax checks**

```powershell
node 报名材料\validate-preliminary-demo.cjs
node --check 报名材料\悟典-初赛Demo\js\court-scene.js
```

Expected: both commands exit 0.

- [ ] **Step 6: Commit the Three.js replacement**

```powershell
git add -- 报名材料/悟典-初赛Demo/js/court-scene.js
git commit -m "feat: replace sage dolls with portrait seats"
```

### Task 3: Make the UI language honest and prove responsive behavior

**Files:**
- Modify: `报名材料/悟典-初赛Demo/index.html`
- Test: `报名材料/validate-preliminary-demo.cjs`

- [ ] **Step 1: Update the debate hint**

Replace:

```html
<span>点击人物聚焦席位</span>
```

with:

```html
<span>点击肖像切换立场</span>
```

- [ ] **Step 2: Run source validation**

```powershell
node 报名材料\validate-preliminary-demo.cjs
git diff --check
```

Expected: both commands exit 0.

- [ ] **Step 3: Serve and inspect desktop**

Run this local static server, then use the in-app browser at 1440×900:

```powershell
python -m http.server 4178 --bind 127.0.0.1 --directory '报名材料\悟典-初赛Demo'
```

Confirm:

- Three portrait photographs are clearly visible on the intake stage.
- No geometric head, cylinder body, beard cone, or arm is present.
- Evidence books and relation curves remain visible.
- Switching each debate tab moves and lights the matching portrait seat.
- Browser console has no errors or warnings.

- [ ] **Step 4: Inspect 390×844, reduced motion, and forced fallback**

Confirm zero horizontal overflow. In the 3D path only the active portrait is shown on mobile. Enable the motion toggle and confirm CSS and scene motion reduce. Open `?force2d=1` and complete the flow with local portrait images.

- [ ] **Step 5: Commit the UI wording**

```powershell
git add -- 报名材料/悟典-初赛Demo/index.html
git commit -m "fix: describe portrait interaction honestly"
```

### Task 4: Rebuild and verify the upload artifact

**Files:**
- Modify: `报名材料/悟典-思想审判场-初赛Demo.zip`

- [ ] **Step 1: Rebuild the ZIP from the Demo folder contents**

```powershell
Compress-Archive -Path '报名材料\悟典-初赛Demo\*' -DestinationPath '报名材料\悟典-思想审判场-初赛Demo.zip' -CompressionLevel Optimal -Force
```

- [ ] **Step 2: Expand to a fresh temporary directory and validate**

Create a unique directory under `$env:TEMP`, expand the ZIP, then run:

```powershell
$extractRoot = Join-Path $env:TEMP ('wudian-portrait-stage-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $extractRoot | Out-Null
Expand-Archive -LiteralPath '报名材料\悟典-思想审判场-初赛Demo.zip' -DestinationPath $extractRoot
node 报名材料\validate-preliminary-demo.cjs $extractRoot
```

Expected: `Preliminary 3D demo validation passed.`

- [ ] **Step 3: Verify exact package properties**

Confirm the ZIP is below 20 MB, contains `index.html` at its root, contains all three PNG portraits, and contains no `http://` or `https://` runtime references.

- [ ] **Step 4: Run final verification**

```powershell
node 报名材料\validate-preliminary-demo.cjs
node --check 报名材料\悟典-初赛Demo\js\app.js
node --check 报名材料\悟典-初赛Demo\js\court-data.js
node --check 报名材料\悟典-初赛Demo\js\court-scene.js
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 5: Commit the artifact**

```powershell
git add -- 报名材料/悟典-思想审判场-初赛Demo.zip
git commit -m "build: refresh preliminary portrait-stage demo"
```

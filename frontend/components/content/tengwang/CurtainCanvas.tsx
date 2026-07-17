"use client";

import { useEffect, useRef, type RefObject } from "react";
import {
  buildCurtain,
  constrainCurtain,
  injectPointerImpulse,
  integrateCurtain,
  isCurtainSettled,
  type CurtainChain,
  type PointerPoint,
} from "@/lib/curtainPhysics";
import styles from "./TengwangExperience.module.css";

type CurtainSettings = {
  strength: number;
  reach: number;
  inertia: number;
  soundEnabled: boolean;
};

type CurtainCanvasProps = {
  buildingRef: RefObject<HTMLImageElement>;
  text: string;
  settings: CurtainSettings;
  resetVersion: number;
  reducedMotion: boolean;
  onUnavailable: () => void;
};

type WebAudioWindow = typeof window & {
  webkitAudioContext?: typeof AudioContext;
};

type ActiveVoice = {
  oscillators: OscillatorNode[];
  nodes: AudioNode[];
  timerId: number;
  stopped: boolean;
};

type AudioController = {
  suspend: () => void;
};

export default function CurtainCanvas({
  buildingRef,
  text,
  settings,
  resetVersion,
  reducedMotion,
  onUnavailable,
}: CurtainCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const settingsRef = useRef(settings);
  const reducedMotionRef = useRef(reducedMotion);
  const onUnavailableRef = useRef(onUnavailable);
  const audioControllerRef = useRef<AudioController | null>(null);

  useEffect(() => {
    settingsRef.current = settings;
    if (!settings.soundEnabled) {
      audioControllerRef.current?.suspend();
    }
  }, [settings]);

  useEffect(() => {
    reducedMotionRef.current = reducedMotion;
  }, [reducedMotion]);

  useEffect(() => {
    onUnavailableRef.current = onUnavailable;
  }, [onUnavailable]);

  useEffect(() => {
    const canvasElement = canvasRef.current;
    const buildingElement = buildingRef.current;
    const sceneElement = canvasElement?.parentElement;

    if (!canvasElement || !buildingElement || !sceneElement) return;

    const canvas: HTMLCanvasElement = canvasElement;
    const building: HTMLImageElement = buildingElement;
    const scene: HTMLElement = sceneElement;

    let acquiredContext: CanvasRenderingContext2D | null = null;
    try {
      acquiredContext = canvas.getContext("2d", {
        alpha: true,
        desynchronized: true,
      });
    } catch {
      onUnavailableRef.current();
      return;
    }

    if (!acquiredContext) {
      onUnavailableRef.current();
      return;
    }

    const context = acquiredContext;
    const ribbonTones = [
      "rgba(92, 52, 38, 0.34)",
      "rgba(142, 58, 45, 0.31)",
      "rgba(112, 72, 52, 0.3)",
      "rgba(158, 72, 55, 0.27)",
    ];
    const strokeTones = [
      "rgba(71, 40, 31, 0.48)",
      "rgba(117, 43, 35, 0.46)",
      "rgba(84, 54, 40, 0.44)",
      "rgba(128, 53, 43, 0.42)",
    ];

    let chains: CurtainChain[] = [];
    let sceneWidth = 0;
    let sceneHeight = 0;
    let animationId = 0;
    let animationRequested = false;
    let needsRebuild = false;
    let stableFrames = 0;
    let destroyed = false;
    let sceneIsIntersecting = true;
    let pageIsVisible = document.visibilityState !== "hidden";
    let previousPointer: PointerPoint | null = null;

    let audioContext: AudioContext | null = null;
    let masterGain: GainNode | null = null;
    let compressor: DynamicsCompressorNode | null = null;
    let delayNode: DelayNode | null = null;
    let feedbackGain: GainNode | null = null;
    let wetGain: GainNode | null = null;
    const voices = new Set<ActiveVoice>();
    const lastChainSoundAt: number[] = [];
    let lastGlobalSoundAt = Number.NEGATIVE_INFINITY;

    const clamp = (value: number, minimum: number, maximum: number) =>
      Math.max(minimum, Math.min(maximum, value));

    const disconnectNode = (node: AudioNode | null) => {
      if (!node) return;
      try {
        node.disconnect();
      } catch {
        // The node may already have been disconnected by voice cleanup.
      }
    };

    const stopVoice = (voice: ActiveVoice, stopOscillators: boolean) => {
      if (voice.stopped) return;
      voice.stopped = true;
      window.clearTimeout(voice.timerId);

      for (const oscillator of voice.oscillators) {
        oscillator.onended = null;
        if (stopOscillators) {
          try {
            oscillator.stop();
          } catch {
            // An oscillator that already ended cannot be stopped again.
          }
        }
        disconnectNode(oscillator);
      }

      for (const node of voice.nodes) {
        disconnectNode(node);
      }
      voices.delete(voice);
    };

    const initializeAudioFromGesture = () => {
      if (destroyed || !settingsRef.current.soundEnabled) return null;

      if (!audioContext) {
        const audioWindow = window as WebAudioWindow;
        const AudioContextConstructor =
          audioWindow.AudioContext ?? audioWindow.webkitAudioContext;
        if (!AudioContextConstructor) return null;

        let candidateContext: AudioContext | null = null;
        let candidateMaster: GainNode | null = null;
        let candidateCompressor: DynamicsCompressorNode | null = null;
        let candidateDelay: DelayNode | null = null;
        let candidateFeedback: GainNode | null = null;
        let candidateWet: GainNode | null = null;

        try {
          candidateContext = new AudioContextConstructor();
          candidateMaster = candidateContext.createGain();
          candidateCompressor = candidateContext.createDynamicsCompressor();
          candidateDelay = candidateContext.createDelay(0.5);
          candidateFeedback = candidateContext.createGain();
          candidateWet = candidateContext.createGain();

          const now = candidateContext.currentTime;
          candidateMaster.gain.setValueAtTime(0.13, now);
          candidateCompressor.threshold.setValueAtTime(-24, now);
          candidateCompressor.knee.setValueAtTime(18, now);
          candidateCompressor.ratio.setValueAtTime(6, now);
          candidateCompressor.attack.setValueAtTime(0.004, now);
          candidateCompressor.release.setValueAtTime(0.18, now);
          candidateDelay.delayTime.setValueAtTime(0.11, now);
          candidateFeedback.gain.setValueAtTime(0.16, now);
          candidateWet.gain.setValueAtTime(0.2, now);

          candidateMaster.connect(candidateCompressor);
          candidateMaster.connect(candidateDelay);
          candidateDelay.connect(candidateFeedback);
          candidateFeedback.connect(candidateDelay);
          candidateDelay.connect(candidateWet);
          candidateWet.connect(candidateCompressor);
          candidateCompressor.connect(candidateContext.destination);

          audioContext = candidateContext;
          masterGain = candidateMaster;
          compressor = candidateCompressor;
          delayNode = candidateDelay;
          feedbackGain = candidateFeedback;
          wetGain = candidateWet;
        } catch {
          disconnectNode(candidateWet);
          disconnectNode(candidateFeedback);
          disconnectNode(candidateDelay);
          disconnectNode(candidateCompressor);
          disconnectNode(candidateMaster);
          try {
            candidateContext?.close().catch(() => {});
          } catch {
            // A failed audio context must not affect the visual runtime.
          }
          return null;
        }
      }

      try {
        if (audioContext.state === "suspended") {
          audioContext.resume().catch(() => {});
        }
      } catch {
        return null;
      }
      return audioContext;
    };

    const suspendAudio = () => {
      try {
        if (audioContext && audioContext.state !== "closed") {
          audioContext.suspend().catch(() => {});
        }
      } catch {
        // Audio is optional and may be unavailable during lifecycle changes.
      }
    };

    const audioController: AudioController = { suspend: suspendAudio };
    audioControllerRef.current = audioController;

    const createImpactVoice = (
      chainIndex: number,
      impact: number,
      pointerX: number
    ) => {
      const activeContext = audioContext;
      const destination = masterGain;
      if (!activeContext || !destination || activeContext.state === "closed") {
        return false;
      }

      if (voices.size >= 8) {
        const oldestVoice = voices.values().next().value as
          | ActiveVoice
          | undefined;
        if (oldestVoice) stopVoice(oldestVoice, true);
      }

      let fundamental: OscillatorNode | null = null;
      let harmonic: OscillatorNode | null = null;
      let fundamentalGain: GainNode | null = null;
      let harmonicGain: GainNode | null = null;
      let envelope: GainNode | null = null;
      let panner: StereoPannerNode | null = null;
      let voice: ActiveVoice | null = null;

      try {
        fundamental = activeContext.createOscillator();
        harmonic = activeContext.createOscillator();
        fundamentalGain = activeContext.createGain();
        harmonicGain = activeContext.createGain();
        envelope = activeContext.createGain();

        const now = activeContext.currentTime;
        const duration = clamp(0.13 + impact / 240, 0.14, 0.24);
        const baseFrequency = 174 + (chainIndex % 12) * 13;
        const amplitude = clamp(impact / 210, 0.018, 0.095);

        fundamental.type = "sine";
        fundamental.frequency.setValueAtTime(baseFrequency, now);
        harmonic.type = "triangle";
        harmonic.frequency.setValueAtTime(baseFrequency * 2.01, now);
        fundamentalGain.gain.setValueAtTime(0.82, now);
        harmonicGain.gain.setValueAtTime(0.24, now);

        envelope.gain.setValueAtTime(0.0001, now);
        envelope.gain.exponentialRampToValueAtTime(
          amplitude,
          now + 0.008
        );
        envelope.gain.exponentialRampToValueAtTime(
          0.0001,
          now + duration
        );

        fundamental.connect(fundamentalGain);
        harmonic.connect(harmonicGain);
        fundamentalGain.connect(envelope);
        harmonicGain.connect(envelope);

        if (typeof activeContext.createStereoPanner === "function") {
          panner = activeContext.createStereoPanner();
          const pan =
            sceneWidth > 0
              ? clamp((pointerX / sceneWidth) * 2 - 1, -0.88, 0.88)
              : 0;
          panner.pan.setValueAtTime(pan, now);
          envelope.connect(panner);
          panner.connect(destination);
        } else {
          envelope.connect(destination);
        }

        const activeVoice: ActiveVoice = {
          oscillators: [fundamental, harmonic],
          nodes: [
            fundamentalGain,
            harmonicGain,
            envelope,
            ...(panner ? [panner] : []),
          ],
          timerId: 0,
          stopped: false,
        };
        voice = activeVoice;
        voices.add(activeVoice);

        fundamental.start(now);
        harmonic.start(now);
        fundamental.stop(now + duration + 0.025);
        harmonic.stop(now + duration + 0.025);
        activeVoice.timerId = window.setTimeout(
          () => stopVoice(activeVoice, false),
          (duration + 0.09) * 1000
        );
        return true;
      } catch {
        if (voice) {
          stopVoice(voice, true);
          return false;
        }
        if (fundamental) {
          try {
            fundamental.stop();
          } catch {
            // Ignore partially initialized Web Audio nodes.
          }
        }
        if (harmonic) {
          try {
            harmonic.stop();
          } catch {
            // Ignore partially initialized Web Audio nodes.
          }
        }
        disconnectNode(panner);
        disconnectNode(envelope);
        disconnectNode(harmonicGain);
        disconnectNode(fundamentalGain);
        disconnectNode(harmonic);
        disconnectNode(fundamental);
        return false;
      }
    };

    const playImpactSounds = (impacts: number[], pointerX: number) => {
      try {
        if (!settingsRef.current.soundEnabled) return;
        if (!initializeAudioFromGesture()) return;

        const now = performance.now();
        if (now - lastGlobalSoundAt < 22) return;

        const candidates = impacts
          .map((impact, chainIndex) => ({ impact, chainIndex }))
          .filter(({ impact }) => impact > 0)
          .sort((left, right) => right.impact - left.impact);

        for (const candidate of candidates) {
          const lastAt =
            lastChainSoundAt[candidate.chainIndex] ??
            Number.NEGATIVE_INFINITY;
          if (now - lastAt < 55) continue;

          if (
            createImpactVoice(
              candidate.chainIndex,
              candidate.impact,
              pointerX
            )
          ) {
            lastChainSoundAt[candidate.chainIndex] = now;
            lastGlobalSoundAt = now;
            break;
          }
        }
      } catch {
        // Audio failures are isolated from pointer-driven canvas updates.
      }
    };

    const canRun = () =>
      !destroyed && sceneIsIntersecting && pageIsVisible;

    const calculateRibbonEdges = (
      chain: CurtainChain,
      ribbonWidth: number
    ) => {
      const leftEdge: PointerPoint[] = [];
      const rightEdge: PointerPoint[] = [];
      const halfWidth = ribbonWidth / 2;

      for (let index = 0; index < chain.length; index += 1) {
        const point = chain[index];
        const before = chain[Math.max(0, index - 1)];
        const after = chain[Math.min(chain.length - 1, index + 1)];
        const tangentX = after.x - before.x;
        const tangentY = after.y - before.y;
        const tangentLength = Math.max(
          0.0001,
          Math.hypot(tangentX, tangentY)
        );
        const normalX = -tangentY / tangentLength;
        const normalY = tangentX / tangentLength;

        leftEdge.push({
          x: point.x + normalX * halfWidth,
          y: point.y + normalY * halfWidth,
        });
        rightEdge.push({
          x: point.x - normalX * halfWidth,
          y: point.y - normalY * halfWidth,
        });
      }

      return { leftEdge, rightEdge };
    };

    const drawCurtain = () => {
      context.clearRect(0, 0, sceneWidth, sceneHeight);
      if (!chains.length || sceneWidth <= 0 || sceneHeight <= 0) return;

      const ribbonWidth = clamp(
        (sceneWidth * 0.84) / chains.length,
        4.5,
        6.5
      );
      const fontSize = sceneWidth < 720 ? 9.5 : 10.5;
      context.lineJoin = "round";
      context.lineCap = "round";

      chains.forEach((chain, chainIndex) => {
        if (chain.length < 2) return;
        const { leftEdge, rightEdge } = calculateRibbonEdges(
          chain,
          ribbonWidth
        );
        const toneIndex = chainIndex % ribbonTones.length;

        context.beginPath();
        context.moveTo(leftEdge[0].x, leftEdge[0].y);
        for (let index = 1; index < leftEdge.length; index += 1) {
          context.lineTo(leftEdge[index].x, leftEdge[index].y);
        }
        for (let index = rightEdge.length - 1; index >= 0; index -= 1) {
          context.lineTo(rightEdge[index].x, rightEdge[index].y);
        }
        context.closePath();
        context.fillStyle = ribbonTones[toneIndex];
        context.strokeStyle = strokeTones[toneIndex];
        context.lineWidth = 0.65;
        context.shadowColor = "rgba(57, 34, 27, 0.2)";
        context.shadowBlur = 2.8;
        context.shadowOffsetX = 0.7;
        context.shadowOffsetY = 1.1;
        context.fill();
        context.stroke();

        const anchor = chain[0];
        context.shadowColor = "transparent";
        context.beginPath();
        context.arc(anchor.x, anchor.y, 2.15, 0, Math.PI * 2);
        context.fillStyle = strokeTones[toneIndex];
        context.fill();
        context.strokeStyle = "rgba(250, 244, 232, 0.72)";
        context.lineWidth = 0.6;
        context.stroke();
      });

      context.shadowColor = "rgba(250, 245, 234, 0.3)";
      context.shadowBlur = 1;
      context.shadowOffsetX = 0;
      context.shadowOffsetY = 0.45;
      context.fillStyle = "rgba(48, 31, 26, 0.88)";
      context.font =
        "500 " +
        fontSize +
        "px \"Noto Serif SC\", \"Source Han Serif SC\", \"Songti SC\", serif";
      context.textAlign = "center";
      context.textBaseline = "middle";

      for (const chain of chains) {
        for (let index = 1; index < chain.length; index += 1) {
          const point = chain[index];
          if (point.char) {
            context.fillText(point.char, point.x, point.y);
          }
        }
      }

      context.shadowColor = "transparent";
    };

    function scheduleFrame() {
      animationRequested = true;
      if (!canRun() || animationId !== 0 || chains.length === 0) return;
      animationId = requestAnimationFrame(handleAnimationFrame);
    }

    function rebuildCurtain() {
      needsRebuild = false;

      try {
        const sceneRect = scene.getBoundingClientRect();
        const buildingRect = building.getBoundingClientRect();
        const nextWidth = sceneRect.width;
        const nextHeight = sceneRect.height;

        if (
          nextWidth <= 0 ||
          nextHeight <= 0 ||
          buildingRect.width <= 0 ||
          buildingRect.height <= 0
        ) {
          needsRebuild = true;
          return;
        }

        sceneWidth = nextWidth;
        sceneHeight = nextHeight;
        const dpr = Math.min(
          2,
          Math.max(1, window.devicePixelRatio || 1)
        );
        const backingWidth = Math.max(1, Math.round(sceneWidth * dpr));
        const backingHeight = Math.max(1, Math.round(sceneHeight * dpr));

        if (
          canvas.width !== backingWidth ||
          canvas.height !== backingHeight
        ) {
          canvas.width = backingWidth;
          canvas.height = backingHeight;
        }
        context.setTransform(dpr, 0, 0, dpr, 0, 0);

        const fontSize = sceneWidth < 720 ? 9.5 : 10.5;
        context.font =
          "500 " +
          fontSize +
          "px \"Noto Serif SC\", \"Source Han Serif SC\", \"Songti SC\", serif";
        chains = buildCurtain({
          text,
          width: sceneWidth,
          height: sceneHeight,
          buildingLeft: buildingRect.left - sceneRect.left,
          buildingTop: buildingRect.top - sceneRect.top,
          buildingWidth: buildingRect.width,
          buildingHeight: buildingRect.height,
        });
        stableFrames = 0;
        drawCurtain();
        scheduleFrame();
      } catch {
        chains = [];
        animationRequested = false;
      }
    }

    function handleAnimationFrame() {
      animationId = 0;
      if (!canRun()) return;

      animationRequested = false;
      if (needsRebuild) {
        rebuildCurtain();
        return;
      }
      if (!chains.length) return;

      try {
        const currentSettings = settingsRef.current;
        const baseFriction = currentSettings.inertia / 100;
        const friction = reducedMotionRef.current
          ? Math.min(baseFriction, 0.88)
          : baseFriction;
        integrateCurtain(chains, friction, 0.18);
        constrainCurtain(chains, 6);
        drawCurtain();

        const settledThreshold = reducedMotionRef.current ? 0.08 : 0.03;
        stableFrames = isCurtainSettled(chains, settledThreshold)
          ? stableFrames + 1
          : 0;
        if (stableFrames < 10) scheduleFrame();
      } catch {
        animationRequested = false;
      }
    }

    const pauseAnimation = () => {
      if (animationId !== 0) {
        cancelAnimationFrame(animationId);
        animationId = 0;
      }
    };

    const resumeDemandedWork = () => {
      if (!canRun()) return;
      if (needsRebuild) {
        rebuildCurtain();
      } else if (animationRequested) {
        scheduleFrame();
      }
    };

    const handleResize = () => {
      needsRebuild = true;
      if (canRun()) {
        rebuildCurtain();
      } else {
        animationRequested = true;
      }
    };

    const toScenePoint = (event: PointerEvent): PointerPoint | null => {
      const rect = canvas.getBoundingClientRect();
      if (
        rect.width <= 0 ||
        rect.height <= 0 ||
        sceneWidth <= 0 ||
        sceneHeight <= 0
      ) {
        return null;
      }

      const x = (event.clientX - rect.left) * (sceneWidth / rect.width);
      const y = (event.clientY - rect.top) * (sceneHeight / rect.height);
      if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
      return { x, y };
    };

    const handlePointerEnter = (event: PointerEvent) => {
      if (!event.isPrimary) return;
      previousPointer = toScenePoint(event);
      if (settingsRef.current.soundEnabled) {
        initializeAudioFromGesture();
      }
      scheduleFrame();
    };

    const handlePointerMove = (event: PointerEvent) => {
      if (!event.isPrimary || !chains.length) return;
      const currentPointer = toScenePoint(event);
      if (!currentPointer) {
        previousPointer = null;
        return;
      }

      if (settingsRef.current.soundEnabled) {
        initializeAudioFromGesture();
      }

      if (previousPointer) {
        const currentSettings = settingsRef.current;
        const radius = Number.isFinite(currentSettings.reach)
          ? Math.max(1, currentSettings.reach)
          : 34;
        const strength = Number.isFinite(currentSettings.strength)
          ? currentSettings.strength / 100
          : 0.72;
        const impacts = injectPointerImpulse(
          chains,
          previousPointer,
          currentPointer,
          { radius, strength }
        );
        playImpactSounds(impacts, currentPointer.x);
      }

      previousPointer = currentPointer;
      stableFrames = 0;
      scheduleFrame();
    };

    const handlePointerLeave = () => {
      previousPointer = null;
      scheduleFrame();
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(scene);
    resizeObserver.observe(building);

    const intersectionObserver = new IntersectionObserver((entries) => {
      const sceneEntry =
        entries.find((entry) => entry.target === scene) ?? entries[0];
      if (!sceneEntry) return;

      sceneIsIntersecting =
        sceneEntry.isIntersecting && sceneEntry.intersectionRatio > 0;
      if (sceneIsIntersecting) {
        resumeDemandedWork();
      } else {
        pauseAnimation();
      }
    });
    intersectionObserver.observe(scene);

    const handleVisibilityChange = () => {
      pageIsVisible = document.visibilityState !== "hidden";
      if (pageIsVisible) {
        resumeDemandedWork();
      } else {
        pauseAnimation();
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);

    canvas.addEventListener("pointerenter", handlePointerEnter);
    canvas.addEventListener("pointerdown", handlePointerEnter);
    canvas.addEventListener("pointermove", handlePointerMove);
    canvas.addEventListener("pointerleave", handlePointerLeave);
    canvas.addEventListener("pointercancel", handlePointerLeave);

    rebuildCurtain();

    return () => {
      destroyed = true;
      cancelAnimationFrame(animationId);
      resizeObserver.disconnect();
      intersectionObserver.disconnect();
      document.removeEventListener(
        "visibilitychange",
        handleVisibilityChange
      );
      canvas.removeEventListener("pointerenter", handlePointerEnter);
      canvas.removeEventListener("pointerdown", handlePointerEnter);
      canvas.removeEventListener("pointermove", handlePointerMove);
      canvas.removeEventListener("pointerleave", handlePointerLeave);
      canvas.removeEventListener("pointercancel", handlePointerLeave);

      if (audioControllerRef.current === audioController) {
        audioControllerRef.current = null;
      }
      for (const voice of Array.from(voices)) {
        stopVoice(voice, true);
      }
      disconnectNode(wetGain);
      disconnectNode(feedbackGain);
      disconnectNode(delayNode);
      disconnectNode(compressor);
      disconnectNode(masterGain);
      try {
        audioContext?.close().catch(() => {});
      } catch {
        // Closing an optional audio context must not disrupt unmount.
      }
      audioContext = null;
      masterGain = null;
      compressor = null;
      delayNode = null;
      feedbackGain = null;
      wetGain = null;
    };
  }, [buildingRef, resetVersion, text]);

  return (
    <canvas
      ref={canvasRef}
      className={styles.curtainCanvas}
      data-curtain-canvas
      aria-hidden="true"
    />
  );
}

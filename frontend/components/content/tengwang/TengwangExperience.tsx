"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useReducedMotion } from "framer-motion";
import {
  RotateCcw,
  SlidersHorizontal,
  Upload,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { tengwangPavilion } from "@/lib/visualAssets";
import { TENGWANG_GE_XU_TEXT } from "@/lib/tengwangText";
import CurtainCanvas from "./CurtainCanvas";
import styles from "./TengwangExperience.module.css";

const ACCEPTED_IMAGE_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);
const MAX_UPLOAD_BYTES = 8 * 1024 * 1024;
const MAX_IMAGE_EDGE = 8192;
const MAX_IMAGE_PIXELS = 8_000_000;
const DEFAULT_SETTINGS = {
  strength: 72,
  reach: 34,
  inertia: 97,
  soundEnabled: false,
} as const;

const FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "input:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(", ");

type Settings = {
  strength: number;
  reach: number;
  inertia: number;
  soundEnabled: boolean;
};

type WebAudioWindow = typeof window & {
  webkitAudioContext?: typeof AudioContext;
};

export default function TengwangExperience() {
  const reduceMotion = useReducedMotion();
  const [curtainText, setCurtainText] = useState(TENGWANG_GE_XU_TEXT);
  const [imageSrc, setImageSrc] = useState(tengwangPavilion);
  const [imageReady, setImageReady] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const [canvasUnavailable, setCanvasUnavailable] = useState(false);
  const [settings, setSettings] = useState<Settings>({ ...DEFAULT_SETTINGS });
  const [resetVersion, setResetVersion] = useState(0);
  const [panelOpen, setPanelOpen] = useState(false);
  const [audioSupported, setAudioSupported] = useState(false);

  const pavilionRef = useRef<HTMLImageElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const settingsButtonRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const ignoreDialogCloseRef = useRef<HTMLDialogElement | null>(null);
  const settingsPanelRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const restoreFocusRef = useRef<HTMLElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const pendingObjectUrlRef = useRef<string | null>(null);
  const pendingImageRef = useRef<HTMLImageElement | null>(null);
  const uploadAttemptRef = useRef(0);
  const imageRequestVersionRef = useRef(0);

  const handleCanvasUnavailable = useCallback(
    () => setCanvasUnavailable(true),
    []
  );

  const revokeAcceptedObjectUrl = useCallback(() => {
    if (!objectUrlRef.current) return;
    URL.revokeObjectURL(objectUrlRef.current);
    objectUrlRef.current = null;
  }, []);

  const releasePendingUpload = useCallback(() => {
    uploadAttemptRef.current += 1;

    if (pendingImageRef.current) {
      pendingImageRef.current.onload = null;
      pendingImageRef.current.onerror = null;
      pendingImageRef.current.removeAttribute("src");
      pendingImageRef.current = null;
    }

    if (pendingObjectUrlRef.current) {
      URL.revokeObjectURL(pendingObjectUrlRef.current);
      pendingObjectUrlRef.current = null;
    }
  }, []);

  const resetFileInput = useCallback(() => {
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  useEffect(() => {
    const webAudioWindow = window as WebAudioWindow;
    const supported = Boolean(
      webAudioWindow.AudioContext || webAudioWindow.webkitAudioContext
    );

    setAudioSupported(supported);
    if (!supported) {
      setSettings((current) =>
        current.soundEnabled ? { ...current, soundEnabled: false } : current
      );
    }
  }, []);

  useEffect(
    () => () => {
      releasePendingUpload();
      revokeAcceptedObjectUrl();
    },
    [releasePendingUpload, revokeAcceptedObjectUrl]
  );

  const closeSettings = useCallback(() => setPanelOpen(false), []);

  const openSettings = useCallback(() => {
    restoreFocusRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : settingsButtonRef.current;
    setPanelOpen(true);
  }, []);

  const handleDialogCancel = useCallback(
    (event: React.SyntheticEvent<HTMLDialogElement>) => {
      event.preventDefault();
      closeSettings();
    },
    [closeSettings]
  );

  const handleDialogClose = useCallback(
    (event: React.SyntheticEvent<HTMLDialogElement>) => {
      if (ignoreDialogCloseRef.current === event.currentTarget) {
        ignoreDialogCloseRef.current = null;
        return;
      }

      setPanelOpen(false);
    },
    []
  );

  const handleDialogBackdropClick = useCallback(
    (event: React.MouseEvent<HTMLDialogElement>) => {
      if (event.currentTarget === event.target) closeSettings();
    },
    [closeSettings]
  );

  useEffect(() => {
    if (
      !panelOpen ||
      !dialogRef.current ||
      !settingsPanelRef.current
    ) {
      return;
    }

    const dialog = dialogRef.current;
    const panel = settingsPanelRef.current;
    const previousOverflow = document.body.style.overflow;
    if (!dialog.open) dialog.showModal();
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    const getFocusableElements = () =>
      Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;

      const focusable = getFocusableElements();
      if (!focusable.length) {
        event.preventDefault();
        panel.focus();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const activeElement = document.activeElement;
      const focusIsOutside =
        !(activeElement instanceof Node) || !panel.contains(activeElement);

      if (event.shiftKey && (activeElement === first || focusIsOutside)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && (activeElement === last || focusIsOutside)) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      if (dialog.open) {
        ignoreDialogCloseRef.current = dialog;
        dialog.close();
      }

      const focusTarget = restoreFocusRef.current;
      restoreFocusRef.current = null;
      if (focusTarget?.isConnected) {
        focusTarget.focus();
      } else {
        settingsButtonRef.current?.focus();
      }
    };
  }, [panelOpen]);

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.currentTarget.files?.[0] ?? null;
    event.currentTarget.value = "";
    releasePendingUpload();

    if (!file) return;

    if (!ACCEPTED_IMAGE_TYPES.has(file.type)) {
      setImageError("请选择 PNG、JPEG 或 WebP 图片。");
      return;
    }

    if (file.size > MAX_UPLOAD_BYTES) {
      setImageError("图片大小不能超过 8 MiB。");
      return;
    }

    let candidateUrl: string;
    try {
      candidateUrl = URL.createObjectURL(file);
    } catch {
      setImageError("无法读取所选图片，请重新选择。");
      return;
    }

    const attempt = uploadAttemptRef.current;
    let candidateImage: HTMLImageElement;
    try {
      candidateImage = new Image();
    } catch {
      URL.revokeObjectURL(candidateUrl);
      setImageError("无法读取所选图片，请重新选择。");
      return;
    }
    pendingObjectUrlRef.current = candidateUrl;
    pendingImageRef.current = candidateImage;
    candidateImage.decoding = "async";

    const revokeCandidateUrl = () => {
      if (pendingObjectUrlRef.current !== candidateUrl) return;
      pendingObjectUrlRef.current = null;
      URL.revokeObjectURL(candidateUrl);
    };

    candidateImage.onload = () => {
      if (attempt !== uploadAttemptRef.current) return;

      candidateImage.onload = null;
      candidateImage.onerror = null;
      if (pendingImageRef.current === candidateImage) {
        pendingImageRef.current = null;
      }

      const validEdges =
        candidateImage.naturalWidth > 0 &&
        candidateImage.naturalHeight > 0 &&
        candidateImage.naturalWidth <= MAX_IMAGE_EDGE &&
        candidateImage.naturalHeight <= MAX_IMAGE_EDGE;
      const validPixelCount =
        candidateImage.naturalWidth * candidateImage.naturalHeight <=
        MAX_IMAGE_PIXELS;

      if (!validEdges || !validPixelCount) {
        revokeCandidateUrl();
        candidateImage.removeAttribute("src");
        setImageError(
          "图片宽高需在 8192 像素以内，且总像素不超过 800 万。"
        );
        return;
      }

      let preparedCanvas: HTMLCanvasElement | null = null;
      try {
        preparedCanvas = document.createElement("canvas");
        preparedCanvas.width = candidateImage.naturalWidth;
        preparedCanvas.height = candidateImage.naturalHeight;
        const context = preparedCanvas.getContext("2d");
        if (!context) throw new Error("Canvas 2D is unavailable");
        context.drawImage(
          candidateImage,
          0,
          0,
          preparedCanvas.width,
          preparedCanvas.height
        );
      } catch {
        if (preparedCanvas) {
          preparedCanvas.width = 0;
          preparedCanvas.height = 0;
        }
        revokeCandidateUrl();
        candidateImage.removeAttribute("src");
        setImageError("无法生成静态 PNG，已保留当前主图。");
        return;
      }

      const staticCanvas = preparedCanvas;
      revokeCandidateUrl();
      candidateImage.removeAttribute("src");

      try {
        staticCanvas.toBlob(
          (staticBlob) => {
            staticCanvas.width = 0;
            staticCanvas.height = 0;

            if (attempt !== uploadAttemptRef.current) return;
            if (!staticBlob || staticBlob.size === 0) {
              setImageError("无法生成静态 PNG，已保留当前主图。");
              return;
            }

            let staticImageUrl: string;
            try {
              staticImageUrl = URL.createObjectURL(staticBlob);
            } catch {
              setImageError("无法读取静态 PNG，已保留当前主图。");
              return;
            }

            if (attempt !== uploadAttemptRef.current) {
              URL.revokeObjectURL(staticImageUrl);
              return;
            }

            imageRequestVersionRef.current += 1;
            revokeAcceptedObjectUrl();
            objectUrlRef.current = staticImageUrl;
            setImageReady(false);
            setImageError(null);
            setImageSrc(staticImageUrl);
          },
          "image/png"
        );
      } catch {
        staticCanvas.width = 0;
        staticCanvas.height = 0;
        if (attempt === uploadAttemptRef.current) {
          setImageError("无法生成静态 PNG，已保留当前主图。");
        }
      }
    };

    candidateImage.onerror = () => {
      if (attempt !== uploadAttemptRef.current) return;

      candidateImage.onload = null;
      candidateImage.onerror = null;
      if (pendingImageRef.current === candidateImage) {
        pendingImageRef.current = null;
      }
      revokeCandidateUrl();
      candidateImage.removeAttribute("src");
      setImageError("图片无法解码，已保留当前主图。");
    };

    try {
      candidateImage.src = candidateUrl;
    } catch {
      candidateImage.onload = null;
      candidateImage.onerror = null;
      if (pendingImageRef.current === candidateImage) {
        pendingImageRef.current = null;
      }
      revokeCandidateUrl();
      setImageError("无法读取所选图片，请重新选择。");
    }
  };

  const handleRestoreDefaults = useCallback(() => {
    imageRequestVersionRef.current += 1;
    releasePendingUpload();
    revokeAcceptedObjectUrl();
    resetFileInput();
    setCurtainText(TENGWANG_GE_XU_TEXT);
    setImageSrc(tengwangPavilion);
    setImageReady(false);
    setImageError(null);
    setCanvasUnavailable(false);
    setSettings({ ...DEFAULT_SETTINGS });
    setResetVersion((version) => version + 1);
  }, [
    releasePendingUpload,
    resetFileInput,
    revokeAcceptedObjectUrl,
  ]);

  const toggleSound = () => {
    if (!audioSupported) return;
    setSettings((current) => ({
      ...current,
      soundEnabled: !current.soundEnabled,
    }));
  };

  const updateNumericSetting = (
    key: "strength" | "reach" | "inertia",
    value: number
  ) => {
    setSettings((current) => ({ ...current, [key]: value }));
  };

  const imageRequestVersion = imageRequestVersionRef.current;
  const effectiveCurtainText = curtainText.trim()
    ? curtainText
    : TENGWANG_GE_XU_TEXT;
  const statusMessage = [
    imageError,
    canvasUnavailable ? "当前浏览器仅展示静态文境。" : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={styles.experience} data-tengwang-experience>
      <div className={styles.paperNoise} aria-hidden="true" />

      <div className={styles.pavilionWrap}>
        <img
          key={`${imageSrc}:${imageRequestVersion}`}
          ref={pavilionRef}
          className={styles.pavilion}
          src={imageSrc}
          width={1280}
          height={823}
          alt={
            imageSrc === tengwangPavilion
              ? "滕王阁建筑立面"
              : "用户自定义的文境主图"
          }
          onLoad={() => {
            if (imageRequestVersion !== imageRequestVersionRef.current) return;
            setImageReady(true);
          }}
          onError={() => {
            if (imageRequestVersion !== imageRequestVersionRef.current) return;
            setImageReady(false);
            setImageError("主图加载失败，已保留文字内容。");
          }}
        />
      </div>

      {!canvasUnavailable && imageReady && (
        <CurtainCanvas
          buildingRef={pavilionRef}
          text={effectiveCurtainText}
          settings={settings}
          resetVersion={resetVersion}
          reducedMotion={Boolean(reduceMotion)}
          onUnavailable={handleCanvasUnavailable}
        />
      )}

      {canvasUnavailable && (
        <div className={styles.staticExcerpt} aria-label="静态帘幕文字">
          <p>{effectiveCurtainText}</p>
        </div>
      )}

      <header className={styles.titleBlock}>
        <p className={styles.author}>/ 王勃</p>
        <h1 aria-label="滕王阁序">滕王阁序</h1>
      </header>

      <p className={styles.caption}>
        《滕王阁序》作于唐上元二年，写洪州胜景、宾主盛会与人生际遇。
      </p>
      {!canvasUnavailable && (
        <p className={styles.srOnly}>{effectiveCurtainText}</p>
      )}

      {statusMessage && (
        <p className={styles.status} role="status" aria-live="polite">
          {statusMessage}
        </p>
      )}

      <button
        ref={settingsButtonRef}
        type="button"
        className={`${styles.iconButton} ${styles.settingsButton}`}
        aria-label="配置文境"
        aria-expanded={panelOpen}
        aria-controls="tengwang-settings"
        title="配置文境"
        onClick={openSettings}
      >
        <SlidersHorizontal size={20} aria-hidden="true" />
      </button>

      {panelOpen && (
        <dialog
          ref={dialogRef}
          className={styles.settingsDialog}
          aria-labelledby="tengwang-settings-title"
          onClick={handleDialogBackdropClick}
          onCancel={handleDialogCancel}
          onClose={handleDialogClose}
        >
          <aside
            id="tengwang-settings"
            ref={settingsPanelRef}
            className={styles.settingsPanel}
            role="dialog"
            aria-modal="true"
            aria-labelledby="tengwang-settings-title"
            tabIndex={-1}
          >
            <div className={styles.panelHeader}>
              <div>
                <p className={styles.panelEyebrow}>文境设置</p>
                <h2 id="tengwang-settings-title">滕王阁序</h2>
              </div>
              <button
                ref={closeButtonRef}
                type="button"
                className={`${styles.iconButton} ${styles.closeButton}`}
                aria-label="关闭设置"
                title="关闭设置"
                onClick={closeSettings}
              >
                <X size={19} aria-hidden="true" />
              </button>
            </div>

            <div className={styles.setting}>
              <div className={styles.settingLabel}>
                <span>文境主图</span>
                <span className={styles.settingMeta}>最大 8 MiB</span>
              </div>
              <label className={styles.uploadControl}>
                <Upload size={17} aria-hidden="true" />
                <span>选择本地图片</span>
                <input
                  ref={fileInputRef}
                  className={styles.fileInput}
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  aria-describedby="tengwang-image-help"
                  onChange={handleImageUpload}
                />
              </label>
              <p id="tengwang-image-help" className={styles.helpText}>
                PNG、JPEG 或 WebP；最大 8 MiB，宽高不超过 8192
                像素且总像素不超过 800 万，导入后转为静态 PNG
              </p>
            </div>

            <div className={styles.setting}>
              <label className={styles.settingLabel} htmlFor="tengwang-text">
                <span>珠帘文字</span>
                <span className={styles.settingMeta}>
                  {curtainText.trim()
                    ? `${curtainText.length}/3000`
                    : "使用默认文本"}
                </span>
              </label>
              <textarea
                id="tengwang-text"
                className={styles.textarea}
                value={curtainText}
                maxLength={3000}
                rows={5}
                onChange={(event) => setCurtainText(event.currentTarget.value)}
              />
            </div>

            {canvasUnavailable ? (
              <p className={styles.canvasNotice}>
                静态模式下，珠帘参数暂不可用。
              </p>
            ) : (
              <>
                <div className={styles.physicsSettings}>
                  <div className={styles.rangeSetting}>
                    <label htmlFor="tengwang-strength">扰动力度</label>
                    <output htmlFor="tengwang-strength">
                      {settings.strength}
                    </output>
                    <input
                      id="tengwang-strength"
                      className={styles.range}
                      type="range"
                      min={20}
                      max={110}
                      value={settings.strength}
                      onChange={(event) =>
                        updateNumericSetting(
                          "strength",
                          Number(event.currentTarget.value)
                        )
                      }
                    />
                  </div>

                  <div className={styles.rangeSetting}>
                    <label htmlFor="tengwang-reach">感应范围</label>
                    <output htmlFor="tengwang-reach">{settings.reach}</output>
                    <input
                      id="tengwang-reach"
                      className={styles.range}
                      type="range"
                      min={18}
                      max={56}
                      value={settings.reach}
                      onChange={(event) =>
                        updateNumericSetting(
                          "reach",
                          Number(event.currentTarget.value)
                        )
                      }
                    />
                  </div>

                  <div className={styles.rangeSetting}>
                    <label htmlFor="tengwang-inertia">回摆惯性</label>
                    <output htmlFor="tengwang-inertia">
                      {settings.inertia}
                    </output>
                    <input
                      id="tengwang-inertia"
                      className={styles.range}
                      type="range"
                      min={86}
                      max={99}
                      value={settings.inertia}
                      onChange={(event) =>
                        updateNumericSetting(
                          "inertia",
                          Number(event.currentTarget.value)
                        )
                      }
                    />
                  </div>
                </div>

                <button
                  type="button"
                  className={`${styles.commandButton} ${
                    settings.soundEnabled ? styles.commandButtonActive : ""
                  }`}
                  aria-pressed={settings.soundEnabled}
                  disabled={!audioSupported}
                  title={
                    audioSupported
                      ? settings.soundEnabled
                        ? "关闭珠帘声音"
                        : "开启珠帘声音"
                      : "当前浏览器不支持声音"
                  }
                  onClick={toggleSound}
                >
                  {settings.soundEnabled && audioSupported ? (
                    <Volume2 size={17} aria-hidden="true" />
                  ) : (
                    <VolumeX size={17} aria-hidden="true" />
                  )}
                  <span>
                    {audioSupported
                      ? settings.soundEnabled
                        ? "关闭珠帘声音"
                        : "开启珠帘声音"
                      : "当前浏览器不支持声音"}
                  </span>
                </button>

                <button
                  type="button"
                  className={styles.commandButton}
                  onClick={() =>
                    setResetVersion((version) => version + 1)
                  }
                >
                  <RotateCcw size={17} aria-hidden="true" />
                  <span>重置珠帘</span>
                </button>
              </>
            )}

            <div className={styles.panelActions}>
              <button
                type="button"
                className={styles.restoreButton}
                onClick={handleRestoreDefaults}
              >
                <RotateCcw size={17} aria-hidden="true" />
                <span>恢复默认</span>
              </button>
            </div>
          </aside>
        </dialog>
      )}
    </section>
  );
}

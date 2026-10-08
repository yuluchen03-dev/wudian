"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { X, ExternalLink, Scroll, AlertCircle } from "lucide-react";
import type { ImageSource } from "@/lib/types";
import { mockImageSources } from "@/lib/comicData";
import useDialogFocus from "@/lib/useDialogFocus";

interface ImageSourceLinkProps {
  /** 按钮文字 */
  label?: string;
  /** 按钮样式：toolbar(工具栏紧凑) | standalone(独立按钮) */
  variant?: "toolbar" | "standalone";
}

export default function ImageSourceLink({
  label = "查看古籍影像",
  variant = "standalone",
}: ImageSourceLinkProps) {
  const [open, setOpen] = useState(false);
  const closeDialog = () => setOpen(false);
  const { dialogRef, rememberTrigger } = useDialogFocus<HTMLDivElement>(open, closeDialog);
  const openDialog = () => {
    rememberTrigger();
    setOpen(true);
  };

  return (
    <>
      {/* 触发按钮 */}
      {variant === "toolbar" ? (
        <button
          onClick={openDialog}
          className="flex h-11 items-center gap-1.5 rounded-md border border-ink-200 bg-rice-50 px-3 text-sm text-ink-700 transition-colors hover:bg-ink-100 dark:border-ink-500 dark:bg-ink-700 dark:text-rice-200"
          aria-label={label}
          title={label}
        >
          <Scroll size={16} />
          <span className="hidden sm:inline">影像</span>
        </button>
      ) : (
        <button
          onClick={openDialog}
          className="seal-btn"
        >
          <Scroll size={16} className="mr-1.5" />
          {label}
        </button>
      )}

      {/* 弹窗 */}
      {typeof document !== "undefined" &&
        createPortal(
          <AnimatePresence>
            {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeDialog}
            className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/50 p-4 backdrop-blur-sm"
          >
            <motion.div
              ref={dialogRef}
              initial={{ scale: 0.95, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby="image-source-dialog-title"
              tabIndex={-1}
              className="max-h-[calc(100dvh-2rem)] w-full max-w-lg overflow-y-auto rounded-[6px] bg-rice-50 shadow-popup dark:bg-ink-800"
            >
              {/* 弹窗头部 */}
              <div className="sticky top-0 z-10 flex items-center justify-between border-b border-ink-100 bg-rice-100/95 px-5 py-3 backdrop-blur-md dark:border-ink-600 dark:bg-ink-700/95">
                <div className="flex items-center gap-2">
                  <Scroll size={20} className="text-cinnabar-600" />
                  <h3 id="image-source-dialog-title" className="font-serif text-lg font-bold text-ink-800 dark:text-rice-50">
                    查看古籍影像底本
                  </h3>
                </div>
                <button
                  onClick={closeDialog}
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md text-ink-400 transition-colors hover:bg-ink-100 hover:text-ink-600 dark:hover:bg-ink-600"
                  aria-label="关闭古籍影像弹窗"
                >
                  <X size={18} />
                </button>
              </div>

              {/* 弹窗内容 */}
              <div className="space-y-4 p-5">
                {/* 说明 */}
                <div className="flex gap-2 rounded-lg bg-bronze-400/10 p-3 text-sm text-ink-600 dark:text-rice-300">
                  <AlertCircle size={16} className="mt-0.5 flex-shrink-0 text-bronze-500" />
                  <p className="leading-relaxed">
                    以下平台提供权威古籍影像底本。点击外链将跳转至对应平台查看，
                    本站不托管影像资源，相关版权归各平台及原始馆藏机构所有。
                  </p>
                </div>

                {/* 外链列表 */}
                <div className="space-y-2.5">
                  {mockImageSources.map((source: ImageSource) => (
                    <a
                      key={source.id}
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group flex items-start gap-3 rounded-xl border border-ink-200 bg-white p-4 transition-all hover:border-cinnabar-400 hover:shadow-scroll dark:border-ink-600 dark:bg-ink-700"
                    >
                      <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-cinnabar-600/10 font-serif text-lg font-bold text-cinnabar-600">
                        {source.name[0]}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className="font-serif font-semibold text-ink-800 dark:text-rice-50">
                            {source.name}
                          </span>
                          <ExternalLink
                            size={13}
                            className="text-ink-400 transition-colors group-hover:text-cinnabar-600"
                          />
                        </div>
                        <p className="mt-1 text-xs leading-relaxed text-ink-500 dark:text-rice-300">
                          {source.description}
                        </p>
                        <p className="mt-1 text-[11px] text-bronze-500">
                          {source.url}
                        </p>
                      </div>
                    </a>
                  ))}
                </div>

                {/* 版权声明 */}
                <p className="text-center text-[11px] leading-relaxed text-ink-400">
                  将跳转到识典古籍等平台查看权威影像底本 · 影像版权归各馆藏机构所有
                </p>
              </div>
            </motion.div>
          </motion.div>
            )}
          </AnimatePresence>,
          document.body
        )}
    </>
  );
}

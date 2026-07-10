"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Heart,
  MessageCircle,
  Quote,
  Award,
  ChevronDown,
  ChevronUp,
  Send,
} from "lucide-react";
import clsx from "clsx";
import type { Note, NoteDetail, Comment } from "@/lib/types";

interface NoteCardProps {
  note: Note;
  onLike?: (noteId: number) => void;
  onComment?: (noteId: number, content: string) => void;
  expanded?: boolean;
  index?: number;
}

export default function NoteCard({
  note,
  onLike,
  onComment,
  expanded = false,
  index = 0,
}: NoteCardProps) {
  const [isExpanded, setIsExpanded] = useState(expanded);
  const [isLiked, setIsLiked] = useState(note.isLiked);
  const [likeCount, setLikeCount] = useState(note.likeCount);
  const [showCommentBox, setShowCommentBox] = useState(false);
  const [commentText, setCommentText] = useState("");

  const handleLike = () => {
    const newLiked = !isLiked;
    setIsLiked(newLiked);
    setLikeCount((prev) => (newLiked ? prev + 1 : prev - 1));
    onLike?.(note.id);
  };

  const handleSubmitComment = () => {
    if (!commentText.trim()) return;
    onComment?.(note.id, commentText);
    setCommentText("");
    setShowCommentBox(false);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 * index }}
      className="paper-card overflow-hidden p-5"
    >
      {/* 作者信息 */}
      <div className="mb-3 flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-cinnabar-600 font-serif text-lg font-bold text-rice-50">
          {note.author.nickname?.[0] || note.author.username[0]}
        </span>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="font-serif font-semibold text-ink-800 dark:text-rice-50">
              {note.author.nickname || note.author.username}
            </span>
            <span className="rounded bg-bronze-500/10 px-1.5 py-0.5 text-[10px] text-bronze-600">
              Lv.{note.author.level}
            </span>
            {note.isEssence && (
              <span className="flex items-center gap-0.5 rounded bg-cinnabar-600/10 px-1.5 py-0.5 text-[10px] text-cinnabar-600">
                <Award size={10} /> 精选
              </span>
            )}
          </div>
          <span className="text-xs text-ink-400">
            {new Date(note.createdAt).toLocaleString("zh-CN", {
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        </div>
      </div>

      {/* 标题 */}
      {note.title && (
        <h3 className="mb-2 font-serif text-lg font-semibold text-ink-800 dark:text-rice-50">
          {note.title}
        </h3>
      )}

      {/* 引用经文 */}
      {note.verseText && (
        <div className="mb-3 flex items-start gap-2 rounded-md border-l-2 border-cinnabar-400 bg-cinnabar-50/50 px-3 py-2 dark:bg-cinnabar-900/20">
          <Quote size={16} className="mt-0.5 shrink-0 text-cinnabar-400" />
          <span className="font-serif text-sm italic text-ink-600 dark:text-rice-300">
            {note.verseText}
          </span>
        </div>
      )}

      {/* 正文 */}
      <div className="mb-3">
        <p
          className={clsx(
            "text-sm leading-relaxed text-ink-700 dark:text-rice-200",
            !isExpanded && "line-clamp-3"
          )}
        >
          {note.content}
        </p>
        {note.content.length > 120 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-1 flex items-center gap-1 text-xs text-cinnabar-600 hover:underline"
          >
            {isExpanded ? (
              <>收起 <ChevronUp size={12} /></>
            ) : (
              <>展开全文 <ChevronDown size={12} /></>
            )}
          </button>
        )}
      </div>

      {/* 标签 */}
      {note.tags.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {note.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-rice-200 px-2 py-0.5 text-xs text-bronze-600 dark:bg-ink-700"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* 互动栏 */}
      <div className="flex items-center gap-4 border-t border-ink-100 pt-3 dark:border-ink-600">
        <button
          onClick={handleLike}
          className={clsx(
            "flex items-center gap-1.5 text-sm transition-colors",
            isLiked ? "text-cinnabar-600" : "text-ink-400 hover:text-cinnabar-600"
          )}
        >
          <Heart size={16} fill={isLiked ? "currentColor" : "none"} />
          <span>{likeCount}</span>
        </button>
        <button
          onClick={() => setShowCommentBox(!showCommentBox)}
          className="flex items-center gap-1.5 text-sm text-ink-400 transition-colors hover:text-bronze-600"
        >
          <MessageCircle size={16} />
          <span>{note.commentCount}</span>
        </button>
      </div>

      {/* 评论框 */}
      <AnimatePresence>
        {showCommentBox && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-3 flex gap-2">
              <input
                type="text"
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSubmitComment()}
                placeholder="写下你的想法..."
                className="flex-1 rounded-md border border-ink-200 bg-rice-50 px-3 py-2 text-sm outline-none focus:border-cinnabar-400 dark:border-ink-500 dark:bg-ink-700"
              />
              <button
                onClick={handleSubmitComment}
                className="flex items-center gap-1 rounded-md bg-cinnabar-600 px-3 py-2 text-sm text-rice-50 transition-colors hover:bg-cinnabar-700"
              >
                <Send size={14} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const root = __dirname;
const htmlPath = path.join(root, '一问见古今-TRAE大赛创意提案.html');
const copyPath = path.join(root, '悟典-TRAE大赛报名帖文案.txt');

function check(condition, message) {
  assert.ok(condition, message);
  console.log(`PASS ${message}`);
}

check(fs.existsSync(htmlPath), 'HTML proposal must exist');
check(fs.existsSync(copyPath), 'Forum copy must exist');

const html = fs.readFileSync(htmlPath, 'utf8');
const forumCopy = fs.readFileSync(copyPath, 'utf8');

check(Buffer.byteLength(html, 'utf8') < 20 * 1024 * 1024, 'HTML stays below the 20 MB forum limit');
check(/<html\s+lang="zh-CN"/i.test(html), 'HTML declares Simplified Chinese');
check(/<meta\s+name="viewport"/i.test(html), 'HTML includes a responsive viewport');
check(/<title>[^<]*一问见古今[^<]*<\/title>/i.test(html), 'Document title names 一问见古今');
check(!/<(?:script|img|source)[^>]+src=["']https?:\/\//i.test(html), 'HTML has no remote runtime or image dependency');
check(!/<link[^>]+rel=["']stylesheet["']/i.test(html), 'HTML has no external stylesheet dependency');
check(!/\b(?:linear|radial|conic)-gradient\s*\(/i.test(html), 'Design avoids CSS gradients');
check(!/\b(?:TBD|TODO)\b|待补充|占位符/i.test(html), 'HTML has no placeholders');

const imageTags = html.match(/<img\b[^>]*>/gi) || [];
const embeddedImages = html.match(/<img\b[^>]+src=["']data:image\/webp;base64,/gi) || [];
check(imageTags.length === 6, 'HTML includes exactly six meaningful images');
check(embeddedImages.length === 6, 'HTML embeds exactly six WebP images');
check(imageTags.every((tag) => /src=["']data:image\/webp;base64,[A-Za-z0-9+/=]{1000,}["']/i.test(tag)), 'Every embedded image contains a real WebP payload');
check(imageTags.every((tag) => /\balt=["'][^"']+["']/i.test(tag)), 'Every image has descriptive alt text');
check(imageTags.every((tag) => /\bwidth=["']\d+["']/i.test(tag) && /\bheight=["']\d+["']/i.test(tag)), 'Every image declares stable dimensions');

for (const id of ['experience', 'problem', 'users', 'trust', 'value', 'trae']) {
  check(new RegExp(`id=["']${id}["']`, 'i').test(html), `HTML includes #${id}`);
}

for (const phrase of [
  '学习工作',
  '可追溯的中国思想问答入口',
  '先检索、再生成',
  '经典原文',
  '目标用户',
  '价值与意义',
  'TRAE'
]) {
  check(html.includes(phrase), `HTML includes required content: ${phrase}`);
}

const caseButtons = html.match(/data-case=["'][^"']+["']/g) || [];
check(caseButtons.length === 3, 'HTML provides exactly three interactive case controls');
check(/aria-pressed=/i.test(html), 'Case controls expose pressed state');
check(/<canvas[\s\S]*?<\/canvas>/i.test(html), 'Hero includes a Canvas visual with fallback content');
check(/prefers-reduced-motion/i.test(html), 'HTML respects reduced-motion preferences');
check(/@media\s+print/i.test(html), 'HTML provides print styles');
check(/window\.print\s*\(/i.test(html), 'HTML includes a print command');

check(forumCopy.startsWith('【学习工作】一问见古今'), 'Forum title follows the selected track');
check(forumCopy.includes('标签：学习工作'), 'Forum copy names the 学习工作 label');
for (const heading of [
  '1. 创意名称 + 创意介绍',
  '2. 目标用户及痛点',
  '3. 价值与意义',
  '4. 随帖附件'
]) {
  check(forumCopy.includes(heading), `Forum copy includes ${heading}`);
}

const chineseCharacters = forumCopy.match(/[\u3400-\u9fff]/g) || [];
check(chineseCharacters.length >= 100, 'Forum body exceeds the 100-Chinese-character minimum');
check(forumCopy.includes('一问见古今-TRAE大赛创意提案.html'), 'Forum copy names the HTML attachment');
check(/思想启发/.test(forumCopy) && /不替代/.test(forumCopy), 'Forum copy states the product safety boundary');
check(!/\b(?:TBD|TODO)\b|待补充|占位符|https?:\/\/example\.com/i.test(forumCopy), 'Forum copy has no placeholders');

console.log('Registration materials validation passed.');

import katex from 'katex'
import 'katex/dist/katex.min.css'

/** 转义 HTML 特殊字符，防止 XSS */
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * 将文本中的 LaTeX 公式渲染为 HTML
 * 支持 $$...$$（行内独立公式）和 $...$（行内公式）
 * 非 LaTeX 部分会先转义 HTML，防止 XSS
 */
export function renderLatex(text) {
  if (!text) return ''

  // 先用占位符替换 LaTeX 公式，再转义剩余文本的 HTML，最后还原公式
  const placeholders = []
  let result = text

  function save(_, formula, displayMode) {
    const idx = placeholders.length
    try {
      placeholders.push(katex.renderToString(formula.trim(), { displayMode, throwOnError: false }))
    } catch {
      placeholders.push(escapeHtml(formula))
    }
    return `__LATEX_${idx}__`
  }

  // 用占位符替换所有 LaTeX 公式
  result = result.replace(/\$\$([\s\S]+?)\$\$/g, (m, f) => save(m, f, true))
  result = result.replace(/(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)/g, (m, f) => save(m, f, false))
  result = result.replace(/\\\((.+?)\\\)/g, (m, f) => save(m, f, false))
  result = result.replace(/\\\[([\s\S]+?)\\\]/g, (m, f) => save(m, f, true))

  // 转义非 LaTeX 部分的 HTML
  result = escapeHtml(result)

  // 还原 LaTeX 公式（KaTeX 输出是安全的 HTML）
  result = result.replace(/__LATEX_(\d+)__/g, (_, idx) => placeholders[parseInt(idx)])

  return result
}

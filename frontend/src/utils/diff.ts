/** 字符级 LCS diff：中文正文并排高亮足够用，不引第三方库。 */
export interface DiffSegment {
  type: 'same' | 'add' | 'del'
  text: string
}

export interface DiffResult {
  left: DiffSegment[]
  right: DiffSegment[]
}

export function diffChars(leftText: string, rightText: string): DiffResult {
  const a = Array.from(leftText || '')
  const b = Array.from(rightText || '')
  const rows = a.length + 1
  const cols = b.length + 1
  // 超过 6000 格退化为前缀/后缀裁剪，避免浏览器卡顿
  if (rows * cols > 6000) {
    return {
      left: [{ type: 'del', text: leftText }],
      right: [{ type: 'add', text: rightText }],
    }
  }
  const lcs: number[][] = Array.from({ length: rows }, () => new Array<number>(cols).fill(0))
  for (let i = a.length - 1; i >= 0; i -= 1) {
    for (let j = b.length - 1; j >= 0; j -= 1) {
      lcs[i][j] =
        a[i] === b[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1])
    }
  }
  const left: DiffSegment[] = []
  const right: DiffSegment[] = []
  const push = (list: DiffSegment[], type: DiffSegment['type'], char: string) => {
    const last = list[list.length - 1]
    if (last && last.type === type) last.text += char
    else list.push({ type, text: char })
  }
  let i = 0
  let j = 0
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      push(left, 'same', a[i])
      push(right, 'same', b[j])
      i += 1
      j += 1
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      push(left, 'del', a[i])
      i += 1
    } else {
      push(right, 'add', b[j])
      j += 1
    }
  }
  while (i < a.length) {
    push(left, 'del', a[i])
    i += 1
  }
  while (j < b.length) {
    push(right, 'add', b[j])
    j += 1
  }
  return { left, right }
}

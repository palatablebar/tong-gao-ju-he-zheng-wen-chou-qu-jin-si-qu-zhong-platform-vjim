import { ref } from 'vue'

export interface ToastItem {
  id: number
  message: string
  tone: 'info' | 'error'
}

const items = ref<ToastItem[]>([])
let seq = 0

export function useToast() {
  function push(message: string, tone: 'info' | 'error' = 'info', ttl = 3200) {
    const item: ToastItem = { id: (seq += 1), message, tone }
    items.value = [...items.value, item]
    window.setTimeout(() => {
      items.value = items.value.filter((entry) => entry.id !== item.id)
    }, ttl)
  }
  function failure(exc: unknown) {
    push(exc instanceof Error ? exc.message : String(exc), 'error', 4200)
  }
  return { items, push, failure }
}

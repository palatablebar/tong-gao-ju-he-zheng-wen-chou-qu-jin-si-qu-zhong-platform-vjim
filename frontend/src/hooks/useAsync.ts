import { ref, type Ref } from 'vue'

/** 轻量异步状态：loading / error / data / run（三个页面复用） */
export function useAsync<T>(task: () => Promise<T>, options: { immediate?: boolean } = {}) {
  const loading = ref(false)
  const error = ref<string | null>(null)
  const data = ref(null) as Ref<T | null>

  async function run(): Promise<T | null> {
    loading.value = true
    error.value = null
    try {
      const result = await task()
      data.value = result
      return result
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
      return null
    } finally {
      loading.value = false
    }
  }

  if (options.immediate) {
    void run()
  }

  return { loading, error, data, run }
}

<template>
  <section class="body-diff">
    <div class="body-diff__col">
      <header class="body-diff__head">
        <span class="body-diff__title">{{ leftTitle }}</span>
        <span class="mono" style="color: var(--ink-faint)">{{ leftText.length }} 字</span>
      </header>
      <pre v-if="mode === 'diff'" class="body-diff__text"><template
        v-for="(segment, index) in diff.left"
        :key="`l-${index}`"
      ><mark v-if="segment.type === 'del'" class="del">{{ segment.text }}</mark><template v-else>{{ segment.text }}</template></template></pre>
      <pre v-else class="body-diff__text">{{ leftText }}</pre>
    </div>

    <div class="body-diff__col">
      <header class="body-diff__head">
        <span class="body-diff__title">{{ rightTitle }}</span>
        <span class="mono" style="color: var(--ink-faint)">{{ rightText.length }} 字</span>
      </header>

      <pre v-if="mode === 'diff'" class="body-diff__text"><template
        v-for="(segment, index) in diff.right"
        :key="`r-${index}`"
      ><mark v-if="segment.type === 'add'">{{ segment.text }}</mark><template v-else>{{ segment.text }}</template></template></pre>

      <textarea
        v-else
        v-model="draft"
        class="body-diff__editor"
        :readonly="!editable"
        data-testid="body-editor"
        spellcheck="false"
      />

      <div v-if="mode === 'correct'" class="export-actions">
        <button
          v-if="editable"
          class="btn btn--seal seal-button"
          type="button"
          data-testid="save-correct"
          :disabled="saving || !draft.trim()"
          @click="emitSave"
        >
          {{ saving ? '保存中…' : '保存校正' }}
        </button>
        <span v-else class="mono" style="color: var(--ink-faint)">只读角色不可校正正文</span>
      </div>
    </div>
  </section>

  <div v-if="mode === 'correct' && candidates.length" class="candidate-list">
    <div class="mono" style="color: var(--ink-faint); letter-spacing: 0.12em">
      抽取候选片段（点击可并入正文）
    </div>
    <div
      v-for="candidate in candidates"
      :key="candidate.block_id"
      class="candidate"
      data-testid="candidate-block"
    >
      <span class="candidate__id">{{ candidate.block_id }}</span>
      <span>{{ candidate.text }}</span>
      <button
        v-if="editable"
        class="btn btn--ghost"
        type="button"
        style="padding: 0.15rem 0.5rem"
        @click="appendCandidate(candidate.text)"
      >
        并入
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { diffChars } from '../../utils/diff'
import type { CandidateBlock } from '../../types'

const props = withDefaults(
  defineProps<{
    mode: 'correct' | 'diff'
    leftTitle: string
    leftText: string
    rightTitle: string
    rightText: string
    editable?: boolean
    saving?: boolean
    candidates?: CandidateBlock[]
  }>(),
  { editable: false, saving: false, candidates: () => [] },
)

const emit = defineEmits<{ (event: 'save', body: string): void }>()

const draft = ref(props.rightText)
watch(
  () => props.rightText,
  (value) => {
    draft.value = value
  },
)

const diff = computed(() => {
  const raw = diffChars(props.leftText, props.rightText)
  const calm = (segments: Array<{ type: string; text: string }>) =>
    segments.map((segment) =>
      segment.type !== 'same' && segment.text.length < 4 ? { ...segment, type: 'same' } : segment,
    )
  return { left: calm(raw.left), right: calm(raw.right) }
})

function appendCandidate(text: string) {
  const current = draft.value.trim()
  draft.value = current ? `${current}\n${text}` : text
}

function emitSave() {
  emit('save', draft.value.trim())
}
</script>

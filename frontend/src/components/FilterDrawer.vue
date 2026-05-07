// Author: Oleg Andriichuk, xandri07
// Bachelor's thesis - Web Application for Image Stitching, FIT VUT Brno, 2026

<template>
  <Teleport to="body">
    <!-- Backdrop -->
    <Transition name="fade">
      <div v-if="open" class="fixed inset-0 z-40 bg-black/30" @click="emit('close')" />
    </Transition>

    <!-- Drawer -->
    <Transition name="slide">
      <aside
        v-if="open"
        class="fixed top-0 right-0 z-50 h-full w-[30%] bg-white shadow-2xl flex flex-col"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-5 py-4 border-b border-[#e5e7eb] shrink-0">
          <div class="flex items-center gap-2">
            <h2 class="m-0 text-[15px] font-semibold text-[#111827]">Filter Projects</h2>
            <span
              v-if="activeCount > 0"
              class="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-full bg-[#4954E7] text-white text-[11px] font-bold"
            >{{ activeCount }}</span>
          </div>
          <button
            class="w-7 h-7 flex items-center justify-center rounded-lg text-[#6b7280] hover:bg-[#f3f4f6] transition-colors text-[18px] leading-none"
            @click="emit('close')"
          >×</button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-3">

          <!-- Condition rows -->
          <div
            v-if="conditions.length === 0"
            class="text-[13px] text-[#9ca3af] text-center py-3"
          >
            No filters applied. Add a condition below.
          </div>

          <!-- Condition rows: flex-col wrapper so error message sits below the row -->
          <div
            v-for="(cond, idx) in conditions"
            :key="cond.key"
            class="flex flex-col gap-1 p-2 rounded-lg border transition"
            :class="conditionErrors[cond.key] || isValueTooLong(cond) ? 'bg-[#fff8f8] border-[#ef4444]' : 'bg-[#f9fafb] border-[#e5e7eb]'"
          >
            <!-- Single horizontal row: index · field · operator · value · remove -->
            <div class="flex flex-row items-center gap-2">
              <span class="text-[11px] font-bold text-[#6b7280] w-4 shrink-0 text-center">{{ idx + 1 }}</span>

              <!-- Field dropdown (~29%) -->
              <select
                v-model="cond.field"
                @change="onFieldChange(cond)"
                class="w-[29%] shrink-0 h-8 px-2 rounded border border-[#e5e7eb] text-[13px] text-[#111827] bg-white focus:outline-none focus:border-[#3b82f6] transition cursor-pointer"
              >
                <option v-for="f in FIELD_OPTIONS" :key="f.value" :value="f.value">{{ f.label }}</option>
              </select>

              <!-- Operator dropdown (~25%) -->
              <select
                v-model="cond.operator"
                @change="onOperatorChange(cond)"
                class="w-[25%] shrink-0 h-8 px-2 rounded border border-[#e5e7eb] text-[13px] text-[#111827] bg-white focus:outline-none focus:border-[#3b82f6] transition cursor-pointer"
              >
                <option v-for="op in operatorsFor(cond.field)" :key="op.value" :value="op.value">{{ op.label }}</option>
              </select>

              <!-- Value input (flex-1, hidden for null operators) -->
              <template v-if="!NULL_OPS.has(cond.operator)">
                <input
                  v-if="cond.field === 'year'"
                  v-model.number="cond.value"
                  type="number"
                  placeholder="e.g. 1943"
                  min="1000"
                  max="9999"
                  class="flex-1 min-w-0 h-8 px-2 rounded border text-[13px] text-[#111827] bg-white focus:outline-none transition"
                  :class="conditionErrors[cond.key] ? 'border-[#ef4444] focus:border-[#ef4444]' : 'border-[#e5e7eb] focus:border-[#3b82f6]'"
                  @input="clearConditionError(cond.key)"
                />
                <select
                  v-else-if="cond.field === 'document_type'"
                  v-model="cond.value"
                  class="flex-1 min-w-0 h-8 px-2 rounded border text-[13px] text-[#111827] bg-white focus:outline-none transition cursor-pointer"
                  :class="conditionErrors[cond.key] ? 'border-[#ef4444] focus:border-[#ef4444]' : 'border-[#e5e7eb] focus:border-[#3b82f6]'"
                  @change="clearConditionError(cond.key)"
                >
                  <option value="">— select —</option>
                  <option v-for="dt in DOCUMENT_TYPES" :key="dt" :value="dt">{{ dt }}</option>
                </select>
                <input
                  v-else
                  v-model="cond.value"
                  type="text"
                  :placeholder="valuePlaceholder(cond.field)"
                  class="flex-1 min-w-0 h-8 px-2 rounded border text-[13px] text-[#111827] bg-white focus:outline-none transition"
                  :class="conditionErrors[cond.key] || isValueTooLong(cond) ? 'border-[#ef4444] focus:border-[#ef4444]' : 'border-[#e5e7eb] focus:border-[#3b82f6]'"
                  @input="clearConditionError(cond.key)"
                />
              </template>
              <!-- Spacer when value is hidden -->
              <div v-else class="flex-1" />

              <button
                type="button"
                @click="removeCondition(cond.key)"
                class="w-6 h-6 shrink-0 flex items-center justify-center rounded text-[#9ca3af] hover:text-[#ef4444] hover:bg-[#fef2f2] transition-colors text-[16px] leading-none cursor-pointer border-0 bg-transparent p-0"
              >×</button>
            </div>

            <!-- Per-condition feedback: error OR live character counter -->
            <div class="flex items-center justify-between pl-6">
              <p v-if="conditionErrors[cond.key]" class="text-[11px] text-[#ef4444] m-0">
                {{ conditionErrors[cond.key] }}
              </p>
              <span v-else class="block" />
              <span
                v-if="maxLengthFor(cond.field) && !NULL_OPS.has(cond.operator) && typeof cond.value === 'string' && cond.value.length > 0"
                class="text-[11px] shrink-0"
                :class="isValueTooLong(cond) ? 'text-[#ef4444]' : 'text-[#9ca3af]'"
              >{{ (cond.value as string).length }}/{{ maxLengthFor(cond.field) }}</span>
            </div>
          </div>

          <!-- Add condition -->
          <button
            type="button"
            @click="addCondition"
            class="w-full h-9 rounded-md border border-dashed border-[#4954E7] text-[#4954E7] text-[13px] font-medium hover:bg-[#f0f0fd] transition-colors cursor-pointer bg-transparent"
          >
            + Add condition
          </button>

          <!-- Logic section (only when 2+ conditions) -->
          <div
            v-if="conditions.length >= 2"
            class="flex flex-col gap-2 p-3 bg-[#f0f0fd] rounded-lg border border-[#c7c9f5]"
          >
            <div class="flex items-center justify-between">
              <span class="text-[13px] font-medium text-[#374151]">Custom filter logic</span>
              <!-- Toggle switch -->
              <button
                type="button"
                @click="toggleCustomLogic"
                class="relative inline-flex w-9 h-5 rounded-full transition-colors cursor-pointer border-0 p-0 shrink-0"
                :class="customLogicEnabled ? 'bg-[#4954E7]' : 'bg-[#d1d5db]'"
              >
                <span
                  class="absolute top-[2px] w-4 h-4 rounded-full bg-white shadow transition-all"
                  :class="customLogicEnabled ? 'left-[18px]' : 'left-[2px]'"
                />
              </button>
            </div>

            <!-- Default AND label -->
            <div
              v-if="!customLogicEnabled"
              class="text-[12px] text-[#6b7280] font-mono tracking-wide"
            >
              {{ defaultLogicLabel }}
            </div>

            <!-- Custom expression input -->
            <div v-else class="flex flex-col gap-1">
              <input
                v-model="customLogicExpr"
                type="text"
                :placeholder="`e.g. (1 OR 2) AND NOT 3`"
                class="w-full h-8 px-2 rounded border text-[13px] font-mono bg-white focus:outline-none transition"
                :class="logicError ? 'border-[#ef4444] focus:border-[#ef4444]' : 'border-[#e5e7eb] focus:border-[#3b82f6]'"
                @input="onLogicInput"
              />
              <p v-if="logicError" class="text-[11px] text-[#ef4444] m-0">{{ logicError }}</p>
              <p v-else class="text-[11px] text-[#6b7280] m-0">
                Use numbers ({{ conditionNumbers }}) with AND, OR, NOT and parentheses.
              </p>
            </div>
          </div>

          <!-- Divider -->
          <div class="h-px bg-[#e5e7eb] -mx-5" />

          <!-- Visibility (standalone filter) -->
          <div class="flex flex-col gap-1.5">
            <label class="text-[13px] font-medium text-[#374151]">Visibility</label>
            <div class="flex gap-2">
              <button
                v-for="opt in VISIBILITY_OPTIONS"
                :key="opt.label"
                type="button"
                @click="localIsPrivate = opt.value"
                :class="localIsPrivate === opt.value
                  ? 'bg-[#4954E7] text-white border-[#4954E7]'
                  : 'bg-white text-[#374151] border-[#e5e7eb] hover:border-[#4954E7] hover:text-[#4954E7]'"
                class="flex-1 h-8 rounded-md border text-[13px] font-medium transition-colors cursor-pointer"
              >{{ opt.label }}</button>
            </div>
          </div>

        </div>

        <!-- Footer -->
        <div class="px-5 py-4 border-t border-[#e5e7eb] flex gap-2 shrink-0">
          <button
            type="button"
            @click="clearAll"
            class="flex-1 h-9 rounded-md border border-[#e5e7eb] bg-white text-sm text-[#6b7280] hover:bg-[#f9fafb] transition-colors cursor-pointer"
          >Clear all</button>
          <button
            type="button"
            @click="apply"
            class="flex-1 h-9 rounded-md bg-[#4954E7] hover:bg-[#3a44d4] text-white text-sm font-medium transition-colors cursor-pointer border-none"
          >Apply</button>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  DOCUMENT_TYPES,
  type ProjectFilters,
  type FilterField,
  type FilterCondition,
} from '@/types/project'

const props = defineProps<{
  open: boolean
  filters: ProjectFilters
}>()

const emit = defineEmits<{
  close: []
  apply: [filters: ProjectFilters]
}>()

// ── Types ────────────────────────────────────────────────────────────────────

interface ConditionDraft {
  key: number
  field: FilterField
  operator: string
  value: string | number | ''
}

// ── Constants ────────────────────────────────────────────────────────────────

const NULL_OPS = new Set(['is_null', 'is_not_null'])

const FIELD_OPTIONS: { value: FilterField; label: string }[] = [
  { value: 'name', label: 'Name' },
  { value: 'description', label: 'Description' },
  { value: 'region', label: 'Region' },
  { value: 'year', label: 'Year' },
  { value: 'institution', label: 'Institution' },
  { value: 'collection', label: 'Collection' },
  { value: 'document_type', label: 'Document Type' },
]

const STRING_OPS = [
  { value: 'contains', label: 'contains' },
  { value: 'equals', label: 'equals' },
  { value: 'not_equal', label: 'not equal to' },
  { value: 'not_contains', label: 'does not contain' },
  { value: 'is_null', label: 'is null' },
  { value: 'is_not_null', label: 'is not null' },
]

const INTEGER_OPS = [
  { value: 'equals', label: 'equals' },
  { value: 'gt', label: 'greater than' },
  { value: 'lt', label: 'less than' },
  { value: 'not_equal', label: 'not equal to' },
  { value: 'is_null', label: 'is null' },
  { value: 'is_not_null', label: 'is not null' },
]

const ENUM_OPS = [
  { value: 'equals', label: 'equals' },
  { value: 'not_equal', label: 'not equal to' },
  { value: 'is_null', label: 'is null' },
  { value: 'is_not_null', label: 'is not null' },
]

const OPERATOR_MAP: Record<FilterField, typeof STRING_OPS> = {
  name: STRING_OPS,
  description: STRING_OPS,
  region: STRING_OPS,
  institution: STRING_OPS,
  collection: STRING_OPS,
  year: INTEGER_OPS,
  document_type: ENUM_OPS,
}

const VALUE_PLACEHOLDERS: Partial<Record<FilterField, string>> = {
  name: 'e.g. Kyiv 1943',
  description: 'e.g. aerial survey',
  region: 'e.g. Kyiv Oblast',
  institution: 'e.g. National Archive',
  collection: 'e.g. Soviet topographic',
}

const VISIBILITY_OPTIONS: { label: string; value: boolean | undefined }[] = [
  { label: 'All', value: undefined },
  { label: 'Public', value: false },
  { label: 'Private', value: true },
]

// ── State ────────────────────────────────────────────────────────────────────

let nextKey = 0
const conditions = ref<ConditionDraft[]>([])
const conditionErrors = ref<Record<number, string>>({})
const customLogicEnabled = ref(false)
const customLogicExpr = ref('')
const logicError = ref('')
const localIsPrivate = ref<boolean | undefined>(undefined)

// ── Computed ─────────────────────────────────────────────────────────────────

const defaultLogicLabel = computed(() =>
  conditions.value.map((_, i) => i + 1).join(' AND ')
)

const conditionNumbers = computed(() =>
  conditions.value.map((_, i) => i + 1).join(', ')
)

const activeCount = computed(() => {
  const f = props.filters
  return (f.conditions?.length ?? 0) + (f.is_private !== undefined ? 1 : 0)
})

// ── Helpers ──────────────────────────────────────────────────────────────────

const operatorsFor = (field: FilterField) => OPERATOR_MAP[field] ?? STRING_OPS
const defaultOpFor = (field: FilterField) => operatorsFor(field)[0]!.value
const valuePlaceholder = (field: FilterField) => VALUE_PLACEHOLDERS[field] ?? ''

const maxLengthFor = (field: FilterField): number | null => {
  if (field === 'description') return 500
  if (['name', 'region', 'institution', 'collection'].includes(field)) return 100
  return null
}

const isValueTooLong = (cond: ConditionDraft): boolean => {
  const max = maxLengthFor(cond.field)
  return max !== null && typeof cond.value === 'string' && cond.value.length > max
}

// ── Sync from props when drawer opens ────────────────────────────────────────

watch(() => props.open, (val) => {
  if (!val) return
  const incoming = props.filters.conditions ?? []
  conditions.value = incoming.map(c => ({
    key: nextKey++,
    field: c.field,
    operator: c.operator,
    value: c.value ?? '',
  }))
  const storedLogic = props.filters.logic ?? ''
  const isDefault = !storedLogic || storedLogic === incoming.map((_, i) => i + 1).join(' AND ')
  customLogicEnabled.value = !isDefault && incoming.length >= 2
  customLogicExpr.value = customLogicEnabled.value ? storedLogic : ''
  conditionErrors.value = {}
  logicError.value = ''
  localIsPrivate.value = props.filters.is_private
})

// ── Condition management ─────────────────────────────────────────────────────

const addCondition = () => {
  conditions.value.push({ key: nextKey++, field: 'name', operator: 'contains', value: '' })
}

const removeCondition = (key: number) => {
  conditions.value = conditions.value.filter(c => c.key !== key)
  delete conditionErrors.value[key]
  // custom logic expression references old indices — reset to safe default
  if (customLogicEnabled.value) {
    customLogicEnabled.value = false
    customLogicExpr.value = ''
    logicError.value = ''
  }
}

const onFieldChange = (cond: ConditionDraft) => {
  cond.operator = defaultOpFor(cond.field)
  cond.value = ''
  delete conditionErrors.value[cond.key]
}

const onOperatorChange = (cond: ConditionDraft) => {
  if (NULL_OPS.has(cond.operator)) cond.value = ''
  delete conditionErrors.value[cond.key]
}

const clearConditionError = (key: number) => {
  delete conditionErrors.value[key]
}

const toggleCustomLogic = () => {
  customLogicEnabled.value = !customLogicEnabled.value
  logicError.value = ''
  if (!customLogicEnabled.value) customLogicExpr.value = ''
}

// ── Validation ───────────────────────────────────────────────────────────────

/** Operators that require a non-empty value */
const REQUIRED_VALUE_OPS = new Set(['contains', 'not_contains', 'equals', 'not_equal', 'gt', 'lt'])

const validateCustomLogic = (): string | null => {
  const expr = customLogicExpr.value.trim()
  if (!expr) return 'Logic expression cannot be empty.'
  const n = conditions.value.length

  // Check for illegal characters first
  const stripped = expr.toUpperCase().replace(/AND|OR|NOT|[()]|\d+|\s+/g, '')
  if (stripped.length > 0) return 'Field format is invalid.'

  // Recursive-descent parser to catch structural issues:
  // incomplete expressions (e.g. "1 AND"), unmatched parens, out-of-range numbers
  const tokens = expr.toUpperCase().match(/AND|OR|NOT|[()]|\d+/g) ?? []
  const pos = [0]
  const peek = () => tokens[pos[0]!] ?? null
  const consume = () => tokens[pos[0]!++]

  const parseOr = (): void => { parseAnd(); while (peek() === 'OR') { consume(); parseAnd() } }
  const parseAnd = (): void => { parseNot(); while (peek() === 'AND') { consume(); parseNot() } }
  const parseNot = (): void => {
    if (peek() === 'NOT') { consume(); parseNot() } else parseAtom()
  }
  const parseAtom = (): void => {
    const tok = peek()
    if (!tok) throw new Error('incomplete')
    consume()
    if (tok === '(') {
      parseOr()
      if (peek() !== ')') throw new Error('unmatched parenthesis')
      consume()
    } else if (/^\d+$/.test(tok)) {
      const ref = parseInt(tok)
      if (ref < 1 || ref > n) throw new Error(`Condition ${tok} does not exist (valid: 1–${n}).`)
    } else {
      throw new Error('unexpected token')
    }
  }

  try {
    parseOr()
    if (pos[0]! < tokens.length) throw new Error('unexpected token')
  } catch (e: any) {
    const msg: string = e.message
    if (msg.startsWith('Condition')) return msg
    return 'Field format is invalid.'
  }
  return null
}

/** Real-time logic validation: only flag invalid characters, not "empty" while typing */
const onLogicInput = () => {
  const expr = customLogicExpr.value.trim()
  if (!expr) { logicError.value = ''; return }
  const stripped = expr.toUpperCase().replace(/AND|OR|NOT|[()]|\d+|\s+/g, '')
  logicError.value = stripped.length > 0 ? 'Field format is invalid.' : ''
}

// ── Apply / Clear ─────────────────────────────────────────────────────────────

const apply = () => {
  // Validate conditions
  const newErrors: Record<number, string> = {}
  for (const cond of conditions.value) {
    if (!NULL_OPS.has(cond.operator)) {
      if (REQUIRED_VALUE_OPS.has(cond.operator) && (cond.value === '' || cond.value === null || cond.value === undefined || (typeof cond.value === 'string' && cond.value.trim() === '') || (typeof cond.value === 'number' && isNaN(cond.value)))) {
        newErrors[cond.key] = 'The field is required.'
      } else if (isValueTooLong(cond)) {
        const max = maxLengthFor(cond.field)
        newErrors[cond.key] = `Must not exceed ${max} characters.`
      }
    }
  }
  conditionErrors.value = newErrors
  if (Object.keys(newErrors).length > 0) return

  if (customLogicEnabled.value) {
    const err = validateCustomLogic()
    if (err) { logicError.value = err; return }
  }

  const conditionsOut: FilterCondition[] = conditions.value.map(c => ({
    field: c.field,
    operator: c.operator,
    value: NULL_OPS.has(c.operator) ? null : (c.value === '' ? null : c.value as string | number),
  }))

  const filters: ProjectFilters = {}
  if (conditionsOut.length > 0) {
    filters.conditions = conditionsOut
    if (conditions.value.length > 1) {
      filters.logic = customLogicEnabled.value
        ? customLogicExpr.value.trim()
        : defaultLogicLabel.value
    }
  }
  if (localIsPrivate.value !== undefined) filters.is_private = localIsPrivate.value

  emit('apply', filters)
  emit('close')
}

const clearAll = () => {
  conditions.value = []
  conditionErrors.value = {}
  customLogicEnabled.value = false
  customLogicExpr.value = ''
  logicError.value = ''
  localIsPrivate.value = undefined
  emit('apply', {})
  emit('close')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>

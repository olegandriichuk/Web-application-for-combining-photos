<template>
  <form @submit.prevent="onSubmit" class="flex flex-col gap-[10px]">

    <!-- Row 1: Experiment Name (×2) | Preset Configuration | Reference Image -->
    <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-[10px]">
      <div class="flex flex-col gap-[6px] lg:col-span-2">
        <label for="exp_name" class="text-[13px] font-semibold text-[#0f172a]">
          Experiment Name <span class="text-[#ef4444] ml-[2px]">*</span>
        </label>
        <input
          id="exp_name"
          v-model="form.exp_name"
          type="text"
          class="h-[40px] px-[14px] border rounded-[10px] text-[14px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
          :class="expNameOver
            ? 'border-[#ef4444] focus:border-[#ef4444]'
            : 'border-[rgba(15,23,42,0.12)] focus:border-[rgba(73,84,231,0.5)]'"
          placeholder="e.g., map_stitch_1890"
        />
        <div class="flex items-center justify-between">
          <p class="m-0 text-[11px] text-[#94a3b8]">Name under which the output result will be stored</p>
          <span class="text-[11px] shrink-0 ml-2" :class="expNameOver ? 'text-[#ef4444] font-semibold' : 'text-[#94a3b8]'">
            {{ form.exp_name.length }}/{{ EXP_NAME_MAX }}
          </span>
        </div>
        <p v-if="expNameOver" class="m-0 text-[11px] text-[#ef4444]">Maximum {{ EXP_NAME_MAX }} characters</p>
      </div>

      <div class="flex flex-col gap-[6px]">
        <label class="text-[13px] font-semibold text-[#0f172a] flex items-center gap-1">
          Preset Configuration
          <span class="relative group ml-0.5 inline-flex items-center cursor-default">
            <svg class="text-[#94a3b8] hover:text-[#64748b] transition-colors" width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 7.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="8" cy="5.25" r="0.85" fill="currentColor"/>
            </svg>
            <div class="absolute top-full left-0 mt-2 w-[272px] px-3 py-2.5 rounded-[8px] bg-[#1e293b] text-white text-[12px] leading-[1.6] font-normal opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 shadow-lg whitespace-normal">
              <div class="absolute bottom-full left-[10px] border-[5px] border-transparent border-b-[#1e293b]"></div>
              <span class="block font-semibold mb-1">Auto-selected based on final resolution:</span>
              <span class="block">· &lt; 150 MPx → <b>100 MPx</b></span>
              <span class="block">· 150–300 MPx → <b>200 MPx</b></span>
              <span class="block">· ≥ 300 MPx → <b>400 MPx</b></span>
            </div>
          </span>
        </label>
        <div class="h-[40px] px-[14px] flex items-center rounded-[10px] bg-[rgba(248,250,252,0.9)] border border-[rgba(15,23,42,0.12)]">
          <span class="text-[14px] font-medium text-[#0f172a]">{{ presetLabel }}</span>
        </div>
        <p class="m-0 text-[11px] text-[#94a3b8]">Auto-selected · hover <svg class="inline" width="10" height="10" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="#94a3b8" stroke-width="1.5"/><path d="M8 7.5v4" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round"/><circle cx="8" cy="5.25" r="0.85" fill="#94a3b8"/></svg> to see all values</p>
      </div>

      <div class="flex flex-col gap-[6px]">
        <label class="text-[13px] font-semibold text-[#0f172a] flex items-center gap-1">
          Reference Image<span class="text-[#ef4444] ml-[2px]">*</span>
          <span class="relative group ml-0.5 inline-flex items-center cursor-default">
            <svg class="text-[#94a3b8] hover:text-[#64748b] transition-colors" width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 7.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="8" cy="5.25" r="0.85" fill="currentColor"/>
            </svg>
            <div class="absolute top-full left-0 mt-2 w-[272px] px-3 py-2.5 rounded-[8px] bg-[#1e293b] text-white text-[12px] leading-[1.6] font-normal opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 shadow-lg whitespace-normal">
              <div class="absolute bottom-full left-[10px] border-[5px] border-transparent border-b-[#1e293b]"></div>
              The reference image is the main photo that all other images will be aligned to during stitching. 
            </div>
          </span>
        </label>
        <div class="h-[40px] px-[14px] flex items-center rounded-[10px] bg-[rgba(248,250,252,0.9)] border border-[rgba(15,23,42,0.12)]">
          <span v-if="refPhotoName" class="text-[13px] font-medium text-[#059669] truncate">{{ refPhotoName }}</span>
          <span v-else class="text-[13px] text-[#94a3b8]">Select a photo card above</span>
        </div>
        <p class="m-0 text-[11px] text-[#94a3b8]">Click the circle on a photo card to set as reference</p>
      </div>
    </div>

    <!-- Row 2: Final Height | Final Width | Output Format | Relative Scale -->
    <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-[10px]">
      <div class="flex flex-col gap-[6px]">
        <label for="final_res_height" class="text-[13px] font-semibold text-[#0f172a] flex items-center gap-1">
          Final Height (px) <span class="text-[#ef4444] ml-[2px]">*</span>
          <span class="relative group ml-0.5 inline-flex items-center cursor-default">
            <svg class="text-[#94a3b8] hover:text-[#64748b] transition-colors" width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 7.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="8" cy="5.25" r="0.85" fill="currentColor"/>
            </svg>
            <div class="absolute top-full left-0 mt-2 w-[272px] px-3 py-2.5 rounded-[8px] bg-[#1e293b] text-white text-[12px] leading-[1.6] font-normal opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 shadow-lg whitespace-normal">
              <div class="absolute bottom-full left-[10px] border-[5px] border-transparent border-b-[#1e293b]"></div>
              <span class="block">Final resolution defines the size of the output image in pixels.</span>
              <span class="block mt-1.5 text-[#94a3b8]">Format: [height, width]</span>
              <span class="block mt-1.5">Example: [6000, 8000] means the image will be 6000 px tall and 8000 px wide.</span>
            </div>
          </span>
        </label>
        <input
          id="final_res_height"
          v-model.number="form.final_res_height"
          type="number"
          min="1"
          step="1"
          class="h-[40px] px-[14px] border rounded-[10px] text-[14px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
          :class="heightInvalid
            ? 'border-[#ef4444] focus:border-[#ef4444]'
            : 'border-[rgba(15,23,42,0.12)] focus:border-[rgba(73,84,231,0.5)]'"
          placeholder="12000"
        />
        <p v-if="heightInvalid" class="m-0 text-[11px] text-[#ef4444]">Must be a positive number</p>
      </div>

      <div class="flex flex-col gap-[6px]">
        <label for="final_res_width" class="text-[13px] font-semibold text-[#0f172a] flex items-center gap-1">
          Final Width (px) <span class="text-[#ef4444] ml-[2px]">*</span>
          <span class="relative group ml-0.5 inline-flex items-center cursor-default">
            <svg class="text-[#94a3b8] hover:text-[#64748b] transition-colors" width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 7.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="8" cy="5.25" r="0.85" fill="currentColor"/>
            </svg>
            <div class="absolute top-full left-0 mt-2 w-[272px] px-3 py-2.5 rounded-[8px] bg-[#1e293b] text-white text-[12px] leading-[1.6] font-normal opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 shadow-lg whitespace-normal">
              <div class="absolute bottom-full left-[10px] border-[5px] border-transparent border-b-[#1e293b]"></div>
              <span class="block">Final resolution defines the size of the output image in pixels.</span>
              <span class="block mt-1.5 text-[#94a3b8]">Format: [height, width]</span>
              <span class="block mt-1.5">Example: [6000, 8000] means the image will be 6000 px tall and 8000 px wide.</span>
            </div>
          </span>
        </label>
        <input
          id="final_res_width"
          v-model.number="form.final_res_width"
          type="number"
          min="1"
          step="1"
          class="h-[40px] px-[14px] border rounded-[10px] text-[14px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
          :class="widthInvalid
            ? 'border-[#ef4444] focus:border-[#ef4444]'
            : 'border-[rgba(15,23,42,0.12)] focus:border-[rgba(73,84,231,0.5)]'"
          placeholder="18000"
        />
        <p v-if="widthInvalid" class="m-0 text-[11px] text-[#ef4444]">Must be a positive number</p>
      </div>

      <div class="flex flex-col gap-[6px]">
        <label for="save_format" class="text-[13px] font-semibold text-[#0f172a] flex items-center gap-1">
          Output Format <span class="text-[#ef4444] ml-[2px]">*</span>
          <span class="relative group ml-0.5 inline-flex items-center cursor-default">
            <svg class="text-[#94a3b8] hover:text-[#64748b] transition-colors" width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 7.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="8" cy="5.25" r="0.85" fill="currentColor"/>
            </svg>
            <div class="absolute top-full left-0 mt-2 w-[300px] px-3 py-2.5 rounded-[8px] bg-[#1e293b] text-white text-[12px] leading-[1.6] font-normal opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 shadow-lg whitespace-normal">
              <div class="absolute bottom-full left-[10px] border-[5px] border-transparent border-b-[#1e293b]"></div>
              <p class="m-0 mb-1.5 font-semibold text-[#e2e8f0]">Output formats</p>
              <p class="m-0 mb-1"><span class="font-semibold text-[#93c5fd]">.JP2</span> — JPEG 2000 file. Excellent compression with no visible quality loss; best for large orthomosaics and GIS workflows.</p>
              <p class="m-0 mb-1"><span class="font-semibold text-[#93c5fd]">.J2K</span> — Raw JPEG 2000 codestream. Same compression as JP2 but without the file-format wrapper; used when downstream tools expect a bare stream.</p>
              <p class="m-0 mb-1"><span class="font-semibold text-[#93c5fd]">.TIFF / .TIF</span> — Tagged Image File Format. Lossless, universally supported by GIS and imaging software; larger file size than JP2.</p>
            </div>
          </span>
        </label>
        <div class="relative">
          <select
            id="save_format"
            v-model="form.save_format"
            class="w-full h-[40px] pl-[14px] pr-[36px] border border-[rgba(15,23,42,0.12)] rounded-[10px] text-[14px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:border-[rgba(73,84,231,0.5)] focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)] appearance-none cursor-pointer"
            required
          >
            <option v-for="opt in SAVE_FORMAT_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <svg class="pointer-events-none absolute right-[12px] top-1/2 -translate-y-1/2 text-[#94a3b8]" width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>

      <div class="flex flex-col gap-[6px]">
        <label class="text-[13px] font-semibold text-[#0f172a] flex items-center gap-1">
          Relative Scale
          <span class="relative group ml-0.5 inline-flex items-center cursor-default">
            <svg class="text-[#94a3b8] hover:text-[#64748b] transition-colors" width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 7.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="8" cy="5.25" r="0.85" fill="currentColor"/>
            </svg>
            <div class="absolute top-full left-0 mt-2 w-[272px] px-3 py-2.5 rounded-[8px] bg-[#1e293b] text-white text-[12px] leading-[1.6] font-normal opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 shadow-lg whitespace-normal">
              <div class="absolute bottom-full left-[10px] border-[5px] border-transparent border-b-[#1e293b]"></div>
              How much smaller each fragment is compared to the full document. Estimated as ⌈√N⌉ where N is the number of uploaded photos (e.g. 4 photos → scale 2, 9 photos → scale 3).
            </div>
          </span>
        </label>
        <div class="h-[40px] px-[14px] flex items-center rounded-[10px] bg-[rgba(248,250,252,0.9)] border border-[rgba(15,23,42,0.12)]">
          <span class="text-[14px] font-medium text-[#0f172a]">{{ autoScale }}</span>
        </div>
        <p class="m-0 text-[11px] text-[#94a3b8]">Auto-calculated from {{ props.photoIds.length }} photo{{ props.photoIds.length === 1 ? '' : 's' }}</p>
      </div>
    </div>

    <!-- Image Point Selector + Corner Points: unified two-column block -->
    <div class="rounded-[12px] border border-[rgba(15,23,42,0.12)] bg-[rgba(248,250,252,0.5)] p-4">
      <div class="grid grid-cols-2 gap-5 items-start">

      <!-- Left column: canvas -->
      <ImagePointSelector
        :ref-image-src="props.refPhotoUrl"
        :original-width="props.refPhotoOriginalWidth"
        :original-height="props.refPhotoOriginalHeight"
        :current-points="form.corner_points"
        @points-updated="onPointsUpdated"
      />

      <!-- Right column: corner point inputs -->
      <div class="flex flex-col gap-[6px]">
        <label class="text-[13px] font-semibold text-[#0f172a] flex items-center gap-1">
          Corner Points <span class="text-[#ef4444] ml-[2px]">*</span>
          <span class="relative group ml-0.5 inline-flex items-center cursor-default">
            <svg class="text-[#94a3b8] hover:text-[#64748b] transition-colors" width="13" height="13" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 7.5v4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <circle cx="8" cy="5.25" r="0.85" fill="currentColor"/>
            </svg>
            <div class="absolute top-full left-0 mt-2 w-[272px] px-3 py-2.5 rounded-[8px] bg-[#1e293b] text-white text-[12px] leading-[1.6] font-normal opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-150 z-50 shadow-lg whitespace-normal">
              <div class="absolute bottom-full left-[10px] border-[5px] border-transparent border-b-[#1e293b]"></div>
              Corner points define the selected area of the reference image. This area is used as the base for aligning all other images in the final result.
            </div>
          </span>
        </label>
        <div class="flex flex-col gap-[6px]">
          <div v-for="(point, idx) in form.corner_points" :key="idx" class="flex items-center gap-2">
            <span class="text-[12px] text-[#64748b] shrink-0 min-w-[52px]">Point {{ idx + 1 }}:</span>
            <input
              v-model.number="point[0]"
              type="number"
              min="0"
              step="1"
              class="w-full h-[34px] px-[10px] border rounded-[8px] text-[13px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
              :class="attempted && coordInvalid(point[0])
                ? 'border-[#ef4444] focus:border-[#ef4444]'
                : 'border-[rgba(15,23,42,0.12)] focus:border-[rgba(73,84,231,0.5)]'"
              placeholder="X"
            />
            <input
              v-model.number="point[1]"
              type="number"
              min="0"
              step="1"
              class="w-full h-[34px] px-[10px] border rounded-[8px] text-[13px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
              :class="attempted && coordInvalid(point[1])
                ? 'border-[#ef4444] focus:border-[#ef4444]'
                : 'border-[rgba(15,23,42,0.12)] focus:border-[rgba(73,84,231,0.5)]'"
              placeholder="Y"
            />
          </div>
        </div>
        <p class="m-0 text-[11px] text-[#94a3b8]">Corner coordinates [x, y] of the reference image (non-negative numbers)</p>
        <p v-if="attempted && !cornerPointsValid" class="m-0 text-[11px] text-[#ef4444]">All coordinates must be non-negative numbers</p>
      </div>

      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="p-3 rounded-[10px] bg-[rgba(239,68,68,0.08)] border border-[rgba(239,68,68,0.2)] text-[#ef4444] text-[13px] font-medium">
      {{ error }}
    </div>

    <!-- Submit -->
    <div class="flex justify-center mt-2">
      <button
        type="submit"
        :disabled="isSubmitting || !isFormValid"
        class="w-[199px] h-[60px] px-8 py-4 border-none rounded-[14px] font-bold text-[14px] text-white bg-[#4954E7] hover:bg-[#3a44d4] shadow-[0_4px_14px_rgba(73,84,231,0.35)] cursor-pointer transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ isSubmitting ? 'Running…' : 'Run stitching job' }}
      </button>
    </div>
  <p v-if="!refPhotoName" class="m-0 text-center text-[11px] text-red-500">
  Select a reference image from the photo cards above before running
</p>

  </form>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { createStitchJob } from '../api/stitchJobs'
import ImagePointSelector from './ImagePointSelector.vue'
import { showToast } from '@/lib/toast'
import {
  PRESET_OPTIONS,
  SAVE_FORMAT_OPTIONS,
  type PresetName,
  type SaveFormat,
  type StitchJob,
  type StitchJobCreate,
} from '../types/stitchJob'

const props = defineProps<{
  projectId: string
  photoIds: string[]
  refPhotoName: string | null
  refPhotoUrl: string | null
  refPhotoOriginalWidth: number | null
  refPhotoOriginalHeight: number | null
}>()

const emit = defineEmits<{
  (e: 'created', job: StitchJob): void
}>()

const EXP_NAME_MAX = 20

const form = reactive({
  exp_name: '',
  final_res_height: 5000,
  final_res_width: 7500,
  save_format: 'tiff' as SaveFormat,
  corner_points: [
    [NaN, NaN],
    [NaN, NaN],
    [NaN, NaN],
    [NaN, NaN],
  ] as [number, number][],
})

// Auto-computed preset based on final resolution
const autoPreset = computed((): PresetName => {
  const mpx = form.final_res_height * form.final_res_width
  if (mpx < 150_000_000) return 'p_100mpx'
  if (mpx < 300_000_000) return 'p_200mpx'
  return 'p_400mpx'
})

const presetLabel = computed(() =>
  PRESET_OPTIONS.find(o => o.value === autoPreset.value)?.label ?? autoPreset.value
)

// Auto-computed relative scale: ceil(sqrt(number of photos))
const autoScale = computed(() =>
  Math.max(1, Math.ceil(Math.sqrt(props.photoIds.length)))
)

const onPointsUpdated = (pts: [[number, number], [number, number], [number, number], [number, number]]) => {
  pts.forEach(([x, y], i) => {
    const pt = form.corner_points[i]
    if (pt) { pt[0] = x; pt[1] = y }
  })
}

watch(() => props.refPhotoUrl, (url) => {
  if (!url) form.corner_points.forEach(pt => { pt[0] = NaN; pt[1] = NaN })
})

const isSubmitting = ref(false)
const error = ref<string | null>(null)
const attempted = ref(false)

const expNameOver = computed(() => form.exp_name.length > EXP_NAME_MAX)
const heightInvalid = computed(() => isNaN(form.final_res_height) || form.final_res_height <= 0)
const widthInvalid = computed(() => isNaN(form.final_res_width) || form.final_res_width <= 0)
const coordInvalid = (val: number) => isNaN(val) || val < 0
const cornerPointsValid = computed(() =>
  form.corner_points.every(p => !coordInvalid(p[0]) && !coordInvalid(p[1]))
)

const isFormValid = computed(() =>
  form.exp_name.trim().length > 0 &&
  !expNameOver.value &&
  !heightInvalid.value &&
  !widthInvalid.value &&
  cornerPointsValid.value &&
  !!props.refPhotoName
)

const onSubmit = async () => {
  attempted.value = true
  if (!props.refPhotoName) {
    error.value = 'Please select a reference image from the photo cards above.'
    return
  }
  if (props.photoIds.length === 0) {
    error.value = 'At least one photo is required.'
    return
  }

  error.value = null
  isSubmitting.value = true

  try {
    const data: StitchJobCreate = {
      photo_ids: props.photoIds,
      exp_name: form.exp_name,
      ref_name: props.refPhotoName,
      preset_name: autoPreset.value,
      final_res: [form.final_res_height, form.final_res_width],
      save_format: form.save_format,
      corner_points: form.corner_points,
      relative_scale: autoScale.value,
    }

    const job = await createStitchJob(props.projectId, data)
    showToast('Exposea job started successfully')
    emit('created', job)
    form.exp_name = ''
  } catch (e: any) {
    console.error('Failed to create stitch job:', e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to create job'
  } finally {
    isSubmitting.value = false
  }
}
</script>

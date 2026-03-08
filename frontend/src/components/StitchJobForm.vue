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
        <label for="preset_name" class="text-[13px] font-semibold text-[#0f172a]">
          Preset Configuration <span class="text-[#ef4444] ml-[2px]">*</span>
        </label>
        <select
          id="preset_name"
          v-model="form.preset_name"
          class="h-[40px] px-[14px] border border-[rgba(15,23,42,0.12)] rounded-[10px] text-[14px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:border-[rgba(73,84,231,0.5)] focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
          required
        >
          <option v-for="opt in PRESET_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <p class="m-0 text-[11px] text-[#94a3b8]">Algorithm parameters for different image resolutions</p>
      </div>

      <div class="flex flex-col gap-[6px]">
        <label class="text-[13px] font-semibold text-[#0f172a]">Reference Image</label>
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
        <label for="final_res_height" class="text-[13px] font-semibold text-[#0f172a]">
          Final Height (px) <span class="text-[#ef4444] ml-[2px]">*</span>
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
        <p v-if="heightInvalid" class="m-0 text-[11px] text-[#ef4444]">Must be a positive integer</p>
      </div>

      <div class="flex flex-col gap-[6px]">
        <label for="final_res_width" class="text-[13px] font-semibold text-[#0f172a]">
          Final Width (px) <span class="text-[#ef4444] ml-[2px]">*</span>
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
        <p v-if="widthInvalid" class="m-0 text-[11px] text-[#ef4444]">Must be a positive integer</p>
      </div>

      <div class="flex flex-col gap-[6px]">
        <label for="save_format" class="text-[13px] font-semibold text-[#0f172a]">
          Output Format <span class="text-[#ef4444] ml-[2px]">*</span>
        </label>
        <select
          id="save_format"
          v-model="form.save_format"
          class="h-[40px] px-[14px] border border-[rgba(15,23,42,0.12)] rounded-[10px] text-[14px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:border-[rgba(73,84,231,0.5)] focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
          required
        >
          <option v-for="opt in SAVE_FORMAT_OPTIONS" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>

      <div class="flex flex-col gap-[6px]">
        <label for="relative_scale" class="text-[13px] font-semibold text-[#0f172a]">
          Relative Scale <span class="text-[#ef4444] ml-[2px]">*</span>
        </label>
        <input
          id="relative_scale"
          v-model.number="form.relative_scale"
          type="number"
          step="1"
          min="1"
          class="h-[40px] px-[14px] border rounded-[10px] text-[14px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
          :class="scaleInvalid
            ? 'border-[#ef4444] focus:border-[#ef4444]'
            : 'border-[rgba(15,23,42,0.12)] focus:border-[rgba(73,84,231,0.5)]'"
          placeholder="2"
        />
        <p class="m-0 text-[11px] text-[#94a3b8]">Scale multiplier (4 fragments = scale 2, 9 = scale 3)</p>
        <p v-if="scaleInvalid" class="m-0 text-[11px] text-[#ef4444]">Must be a positive integer</p>
      </div>
    </div>

    <!-- Corner Points -->
    <div class="flex flex-col gap-[6px]">
      <label class="text-[13px] font-semibold text-[#0f172a]">
        Corner Points <span class="text-[#ef4444] ml-[2px]">*</span>
      </label>
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-[10px]">
        <div v-for="(point, idx) in form.corner_points" :key="idx" class="flex items-center gap-2">
          <span class="text-[12px] text-[#64748b] shrink-0 min-w-[52px]">Point {{ idx + 1 }}:</span>
          <input
            v-model.number="point[0]"
            type="number"
            min="0"
            step="1"
            class="w-full h-[40px] px-[14px] border rounded-[10px] text-[14px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
            :class="coordInvalid(point[0])
              ? 'border-[#ef4444] focus:border-[#ef4444]'
              : 'border-[rgba(15,23,42,0.12)] focus:border-[rgba(73,84,231,0.5)]'"
            placeholder="X"
          />
          <input
            v-model.number="point[1]"
            type="number"
            min="0"
            step="1"
            class="w-full h-[40px] px-[14px] border rounded-[10px] text-[14px] text-[#0f172a] bg-[rgba(248,250,252,0.9)] transition focus:outline-none focus:shadow-[0_0_0_3px_rgba(73,84,231,0.1)]"
            :class="coordInvalid(point[1])
              ? 'border-[#ef4444] focus:border-[#ef4444]'
              : 'border-[rgba(15,23,42,0.12)] focus:border-[rgba(73,84,231,0.5)]'"
            placeholder="Y"
          />
        </div>
      </div>
      <p class="m-0 text-[11px] text-[#94a3b8]">Corner coordinates [x, y] of the output image (non-negative integers)</p>
      <p v-if="!cornerPointsValid" class="m-0 text-[11px] text-[#ef4444]">All coordinates must be non-negative integers</p>
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
    <p v-if="!refPhotoName" class="m-0 text-center text-[11px] text-[#94a3b8]">
      Select a reference image from the photo cards above before running
    </p>

  </form>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { createStitchJob } from '../api/stitchJobs'
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
}>()

const emit = defineEmits<{
  (e: 'created', job: StitchJob): void
}>()

const EXP_NAME_MAX = 20

const form = reactive({
  exp_name: '',
  preset_name: 'default' as PresetName,
  final_res_height: 12000,
  final_res_width: 18000,
  save_format: 'tiff' as SaveFormat,
  relative_scale: 2,
  corner_points: [
    [0, 0],
    [18000, 0],
    [18000, 12000],
    [0, 12000],
  ] as [number, number][],
})

const isSubmitting = ref(false)
const error = ref<string | null>(null)

const expNameOver = computed(() => form.exp_name.length > EXP_NAME_MAX)
const heightInvalid = computed(() => isNaN(form.final_res_height) || form.final_res_height <= 0)
const widthInvalid = computed(() => isNaN(form.final_res_width) || form.final_res_width <= 0)
const scaleInvalid = computed(() => isNaN(form.relative_scale) || form.relative_scale <= 0)
const coordInvalid = (val: number) => isNaN(val) || val < 0
const cornerPointsValid = computed(() =>
  form.corner_points.every(p => !coordInvalid(p[0]) && !coordInvalid(p[1]))
)

const isFormValid = computed(() =>
  form.exp_name.trim().length > 0 &&
  !expNameOver.value &&
  !heightInvalid.value &&
  !widthInvalid.value &&
  !scaleInvalid.value &&
  cornerPointsValid.value &&
  !!props.refPhotoName
)

const onSubmit = async () => {
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
      preset_name: form.preset_name,
      final_res: [form.final_res_height, form.final_res_width],
      save_format: form.save_format,
      corner_points: form.corner_points,
      relative_scale: form.relative_scale,
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

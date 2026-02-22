<template>
  <div class="stitch-form-card">
    <div class="card-head">
      <h2 class="card-title">Create Stitch Job</h2>
      <p class="card-subtitle">Configure parameters for the stitching process</p>
    </div>

    <form @submit.prevent="onSubmit" class="stitch-form">
      <!-- Experiment Name -->
      <div class="form-group">
        <label for="exp_name" class="form-label">
          Experiment Name
          <span class="required">*</span>
        </label>
        <input
          id="exp_name"
          v-model="form.exp_name"
          type="text"
          class="form-input"
          placeholder="e.g., map_stitch_1890"
          required
        />
        <p class="form-hint">Name under which the output result will be stored</p>
      </div>

      <!-- Reference Image Name -->
      <div class="form-group">
        <label for="ref_name" class="form-label">
          Reference Image
          <span class="required">*</span>
        </label>
        <input
          id="ref_name"
          v-model="form.ref_name"
          type="text"
          class="form-input"
          placeholder="e.g., ref_01.tif"
          required
        />
        <p class="form-hint">Name of the reference image file in the project folder</p>
      </div>

      <!-- Preset Selection -->
      <div class="form-group">
        <label for="preset_name" class="form-label">
          Preset Configuration
          <span class="required">*</span>
        </label>
        <select id="preset_name" v-model="form.preset_name" class="form-select" required>
          <option v-for="opt in PRESET_OPTIONS" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
        <p class="form-hint">Algorithm parameters for different image resolutions</p>
      </div>

      <!-- Final Resolution -->
      <div class="form-row">
        <div class="form-group">
          <label for="final_res_height" class="form-label">
            Final Height (px)
            <span class="required">*</span>
          </label>
          <input
            id="final_res_height"
            v-model.number="form.final_res_height"
            type="number"
            min="1"
            class="form-input"
            placeholder="12000"
            required
          />
        </div>
        <div class="form-group">
          <label for="final_res_width" class="form-label">
            Final Width (px)
            <span class="required">*</span>
          </label>
          <input
            id="final_res_width"
            v-model.number="form.final_res_width"
            type="number"
            min="1"
            class="form-input"
            placeholder="18000"
            required
          />
        </div>
      </div>

      <!-- Save Format -->
      <div class="form-group">
        <label for="save_format" class="form-label">
          Output Format
          <span class="required">*</span>
        </label>
        <select id="save_format" v-model="form.save_format" class="form-select" required>
          <option v-for="opt in SAVE_FORMAT_OPTIONS" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
      </div>

      <!-- Relative Scale -->
      <div class="form-group">
        <label for="relative_scale" class="form-label">
          Relative Scale
          <span class="required">*</span>
        </label>
        <input
          id="relative_scale"
          v-model.number="form.relative_scale"
          type="number"
          step="0.1"
          min="0.1"
          class="form-input"
          placeholder="2.5"
          required
        />
        <p class="form-hint">
          Scale multiplier: how many times fragments are smaller than reference
          (4 fragments = scale 2, 9 = scale 3)
        </p>
      </div>

      <!-- Corner Points -->
      <div class="form-group">
        <label class="form-label">
          Corner Points
          <span class="required">*</span>
        </label>
        <div class="corner-points-grid">
          <div v-for="(point, idx) in form.corner_points" :key="idx" class="corner-point">
            <span class="corner-label">Point {{ idx + 1 }}:</span>
            <input
              v-model.number="point[0]"
              type="number"
              class="form-input corner-input"
              placeholder="X"
              required
            />
            <input
              v-model.number="point[1]"
              type="number"
              class="form-input corner-input"
              placeholder="Y"
              required
            />
          </div>
        </div>
        <p class="form-hint">Corner coordinates [x, y] of the output image</p>
      </div>

      <!-- Selected Photos -->
      <div class="form-group">
        <label class="form-label">
          Selected Photos
          <span class="required">*</span>
        </label>
        <div class="selected-photos-info">
          <span v-if="selectedPhotoIds.length > 0" class="photo-count">
            {{ selectedPhotoIds.length }} photo(s) selected
          </span>
          <span v-else class="photo-count photo-count-empty">
            No photos selected - all project photos will be used
          </span>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="form-error">
        {{ error }}
      </div>

      <!-- Submit Button -->
      <div class="form-actions">
        <button type="submit" class="submit-btn" :disabled="isSubmitting">
          <span v-if="isSubmitting">Creating Job...</span>
          <span v-else>Create Stitch Job</span>
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { createStitchJob } from '../api/stitchJobs'
import {
  PRESET_OPTIONS,
  SAVE_FORMAT_OPTIONS,
  type PresetName,
  type SaveFormat,
  type StitchJobCreate,
} from '../types/stitchJob'

const props = defineProps<{
  projectId: string
  photoIds: string[]
}>()

const emit = defineEmits<{
  (e: 'created'): void
}>()

const form = reactive({
  exp_name: '',
  ref_name: '',
  preset_name: 'default' as PresetName,
  final_res_height: 12000,
  final_res_width: 18000,
  save_format: 'tiff' as SaveFormat,
  relative_scale: 2.0,
  corner_points: [
    [0, 0],
    [18000, 0],
    [18000, 12000],
    [0, 12000],
  ] as [number, number][],
})

const isSubmitting = ref(false)
const error = ref<string | null>(null)

const selectedPhotoIds = computed(() => props.photoIds)

const updateCornerPointsFromResolution = () => {
  const w = form.final_res_width || 0
  const h = form.final_res_height || 0
  form.corner_points = [
    [0, 0],
    [w, 0],
    [w, h],
    [0, h],
  ]
}

const onSubmit = async () => {
  error.value = null
  isSubmitting.value = true

  try {
    const photoIds = selectedPhotoIds.value.length > 0
      ? selectedPhotoIds.value
      : props.photoIds

    if (photoIds.length === 0) {
      throw new Error('At least one photo is required')
    }

    const data: StitchJobCreate = {
      photo_ids: photoIds,
      exp_name: form.exp_name,
      ref_name: form.ref_name,
      preset_name: form.preset_name,
      final_res: [form.final_res_height, form.final_res_width],
      save_format: form.save_format,
      corner_points: form.corner_points,
      relative_scale: form.relative_scale,
    }

    await createStitchJob(props.projectId, data)
    emit('created')

    // Reset form
    form.exp_name = ''
    form.ref_name = ''
  } catch (e: any) {
    console.error('Failed to create stitch job:', e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to create job'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.stitch-form-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(15, 23, 42, 0.06);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.1), 0 1px 0 rgba(255, 255, 255, 0.6) inset;
  padding: 22px;
  backdrop-filter: blur(8px);
  max-width: 980px;
  margin: 0 auto;
}

.card-head {
  margin-bottom: 20px;
}

.card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.card-subtitle {
  margin: 6px 0 0;
  font-size: 12px;
  color: #64748b;
}

.stitch-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
}

.required {
  color: #ef4444;
  margin-left: 2px;
}

.form-input,
.form-select {
  padding: 10px 12px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  border-radius: 10px;
  font-size: 14px;
  color: #0f172a;
  background: rgba(248, 250, 252, 0.9);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: rgba(168, 85, 247, 0.5);
  box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.1);
}

.form-hint {
  margin: 0;
  font-size: 11px;
  color: #94a3b8;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.corner-points-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.corner-point {
  display: flex;
  align-items: center;
  gap: 8px;
}

.corner-label {
  font-size: 12px;
  color: #64748b;
  min-width: 60px;
}

.corner-input {
  width: 80px;
}

.selected-photos-info {
  padding: 12px;
  border-radius: 10px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.photo-count {
  font-size: 13px;
  font-weight: 500;
  color: #059669;
}

.photo-count-empty {
  color: #94a3b8;
}

.form-error {
  padding: 12px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #ef4444;
  font-size: 13px;
  font-weight: 500;
}

.form-actions {
  margin-top: 8px;
}

.submit-btn {
  width: 100%;
  padding: 12px 18px;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 13px;
  color: #fff;
  background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
  box-shadow: 0 14px 28px rgba(236, 72, 153, 0.22);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 18px 34px rgba(236, 72, 153, 0.28);
}

.submit-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .corner-points-grid {
    grid-template-columns: 1fr;
  }
}
</style>

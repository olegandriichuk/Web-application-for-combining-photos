<template>
  <div class="wrap">
    <div class="row">
      <div class="count">
        Selected: <b>{{ files.length }}</b> / 6
      </div>
      <div class="actions">
        <button class="miniBtn" type="button" :disabled="disabled" @click="$emit('clear')">
          Clear all
        </button>
      </div>
    </div>

    <div class="grid">
      <div v-for="(f, idx) in files" :key="keyOf(f, idx)" class="tile">
        <img class="img" :src="preview(f)" :alt="f.name" />
        <button class="remove" type="button" :disabled="disabled" @click="$emit('remove', idx)">×</button>
        <div class="meta" :title="f.name">{{ f.name }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  files: File[]
  disabled?: boolean
}>()

defineEmits<{
  (e: 'remove', index: number): void
  (e: 'clear'): void
}>()

const urlCache = new WeakMap<File, string>()

const preview = (f: File) => {
  if (!urlCache.has(f)) urlCache.set(f, URL.createObjectURL(f))
  return urlCache.get(f)!
}

const keyOf = (f: File, idx: number) => `${f.name}-${f.size}-${idx}`
</script>

<style scoped>
.wrap{ margin: 10px 6px 0; }

.row{
  display:flex;
  justify-content: space-between;
  align-items:center;
  margin-bottom: 10px;
}
.count{ font-size: 12px; color:#64748b; }
.actions{ display:flex; gap: 8px; }

.miniBtn{
  border: 1px solid rgba(148,163,184,.35);
  background: white;
  border-radius: 10px;
  padding: 8px 10px;
  font-weight: 600;
  cursor: pointer;
}
.miniBtn:disabled{ opacity:.6; cursor:not-allowed; }

.grid{
  display:grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 12px;
}
.tile{
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(148,163,184,.25);
  background: white;
}
.img{ width: 100%; height: 130px; object-fit: cover; display:block; }
.remove{
  position:absolute;
  top: 8px; right: 8px;
  width: 30px; height: 30px;
  border-radius: 999px;
  border: none;
  background: rgba(15,23,42,.65);
  color: white;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
}
.remove:disabled{ opacity:.6; cursor:not-allowed; }
.meta{
  padding: 8px 10px;
  font-size: 12px;
  color: #475569;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>

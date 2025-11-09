<!-- frontend/src/App.vue -->
<template>
  <div class="app-container">
    <header class="header">
      <h1 class="title">Content Manager</h1>
      <p class="subtitle">Manage your items and photos in one place</p>
    </header>

    <div class="tabs-container">
      <div class="tabs">
        <button
          @click="activeTab = 'items'"
          :class="['tab', { active: activeTab === 'items' }]"
        >
          <span class="tab-icon">📝</span>
          Items
        </button>
        <button
          @click="activeTab = 'photos'"
          :class="['tab', { active: activeTab === 'photos' }]"
        >
          <span class="tab-icon">📷</span>
          Photos
        </button>
      </div>
    </div>

    <!-- Items Tab -->
    <div v-show="activeTab === 'items'" class="content">
      <section class="create-section">
        <h2 class="section-title">Create New Item</h2>
        <div class="input-group">
          <input
            v-model="newTitle"
            placeholder="Enter title..."
            class="input input-title"
            @keypress.enter="add"
          />
          <input
            v-model="newDesc"
            placeholder="Enter description..."
            class="input input-desc"
            @keypress.enter="add"
          />
          <button @click="add" class="btn btn-primary">
            <span class="btn-icon">+</span>
            Add Item
          </button>
        </div>
      </section>

      <section class="list-section">
        <h2 class="section-title">All Items ({{ items.length }})</h2>
        <div v-if="items.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <p>No items yet. Create your first item above!</p>
        </div>
        <div v-else class="items-grid">
          <div v-for="it in items" :key="it.id" class="item-card">
            <template v-if="editing && editing.id === it.id">
              <div class="edit-form">
                <input v-model="editing.title" class="input" placeholder="Title" />
                <input v-model="editing.description" class="input" placeholder="Description" />
                <div class="edit-actions">
                  <button @click="saveEdit" class="btn btn-success">Save</button>
                  <button @click="cancelEdit" class="btn btn-secondary">Cancel</button>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="item-content">
                <h3 class="item-title">{{ it.title }}</h3>
                <p class="item-description">{{ it.description || 'No description' }}</p>
              </div>
              <div class="item-actions">
                <button @click="startEdit(it)" class="btn-icon-action edit">✏️</button>
                <button @click="removeIt(it.id)" class="btn-icon-action delete">🗑️</button>
              </div>
            </template>
          </div>
        </div>
      </section>
    </div>

    <!-- Photos Tab -->
    <div v-show="activeTab === 'photos'" class="content">
      <section class="upload-section">
        <h2 class="section-title">Upload Photos</h2>
        <div class="upload-controls">
          <label class="upload-label">
            <input
              type="file"
              multiple
              accept="image/*"
              @change="onFilesSelected"
              :disabled="isLoading"
            />
            <span class="upload-icon">📁</span>
            Choose Files
          </label>
          <button @click="refresh" :disabled="isLoading" class="btn btn-secondary">
            <span class="btn-icon">🔄</span>
            Refresh
          </button>
        </div>
        <div v-if="isLoading" class="status-loading">Loading...</div>
        <div v-if="error" class="status-error">{{ error }}</div>
      </section>

      <section class="gallery-section">
        <h2 class="section-title">Gallery ({{ photos.length }} photos)</h2>
        <div v-if="photos.length === 0" class="empty-state">
          <div class="empty-icon">🖼️</div>
          <p>No photos uploaded yet. Upload your first photo above!</p>
        </div>
        <div v-else class="photos-grid">
          <article v-for="p in photos" :key="p.id" class="photo-card">
            <a :href="photoUrl(p.id)" target="_blank" rel="noopener" class="photo-link">
              <img :src="photoUrl(p.id)" :alt="p.original_name" class="photo-img" />
              <div class="photo-overlay">
                <span class="view-icon">👁️</span>
              </div>
            </a>
            <div class="photo-meta">
              <div class="photo-name" :title="p.original_name">
                {{ p.original_name }}
              </div>
              <div class="photo-info">
                {{ (p.size / 1024).toFixed(1) }} KB • {{ formatDate(p.created_at) }}
              </div>
            </div>
            <div class="photo-actions">
              <a
                :href="photoUrl(p.id)"
                :download="p.original_name"
                class="photo-action-btn download"
                title="Download"
              >⬇️</a>
              <button
                @click="onDelete(p.id)"
                class="photo-action-btn delete"
                title="Delete"
              >🗑️</button>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Items API
import { listItems, createItem, updateItem, deleteItem, type Item } from './api/items'

// Photos API
import {
  listPhotos as apiListPhotos,
  uploadPhotos as apiUploadPhotos,
  deletePhoto as apiDeletePhoto,
  photoUrl,
  type PhotoItem,
} from './api/photos'

// Tabs
const activeTab = ref<'items' | 'photos'>('items')

// ---------- Items state & methods ----------
const items = ref<Item[]>([])
const newTitle = ref('')
const newDesc = ref('')
const editing = ref<Item | null>(null)

const load = async () => { items.value = await listItems() }

const add = async () => {
  if (!newTitle.value.trim()) return
  await createItem({ title: newTitle.value, description: newDesc.value })
  newTitle.value = ''
  newDesc.value = ''
  await load()
}

const startEdit = (it: Item) => { editing.value = { ...it } }

const saveEdit = async () => {
  if (!editing.value) return
  await updateItem(editing.value.id, {
    title: editing.value.title,
    description: editing.value.description
  })
  editing.value = null
  await load()
}

const cancelEdit = () => { editing.value = null }

const removeIt = async (id: number) => {
  if (!confirm('Delete this item?')) return
  await deleteItem(id)
  await load()
}

// ---------- Photos state & methods ----------
const photos = ref<PhotoItem[]>([])
const isLoading = ref(false)
const error = ref<string | null>(null)

const refresh = async () => {
  isLoading.value = true
  error.value = null
  try {
    photos.value = await apiListPhotos(100, 0)
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to load photos'
  } finally {
    isLoading.value = false
  }
}

const onFilesSelected = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  isLoading.value = true
  error.value = null
  try {
    await apiUploadPhotos(Array.from(input.files))
    await refresh()
    input.value = ''
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Upload failed'
  } finally {
    isLoading.value = false
  }
}

const onDelete = async (id: string) => {
  if (!confirm('Delete this photo?')) return
  isLoading.value = true
  error.value = null
  try {
    await apiDeletePhoto(id)
    photos.value = photos.value.filter(p => p.id !== id)
  } catch (e: any) {
    console.error(e)
    error.value = e?.response?.data?.detail ?? e?.message ?? 'Failed to delete'
  } finally {
    isLoading.value = false
  }
}

const formatDate = (iso?: string) => {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}

// Init
onMounted(() => {
  load()
  refresh()
})
</script>

<style scoped>
* { box-sizing: border-box; }

.app-container {
  min-height: 100vh;
  background: linear-gradient(to bottom, #f8fafc, #f1f5f9);
  padding: 2rem 1rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
}

.header { text-align: center; margin-bottom: 2rem; }

.title {
  font-size: 2.5rem; font-weight: 700; margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.subtitle { font-size: 1rem; color: #64748b; margin: .5rem 0 0; }

.tabs-container { max-width: 1200px; margin: 0 auto 2rem; }
.tabs {
  display: flex; gap: .5rem; background: white; padding: .5rem;
  border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.05);
}
.tab {
  flex: 1; padding: .875rem 1.5rem; border: none; background: transparent; border-radius: 8px;
  font-size: 1rem; font-weight: 500; color: #64748b; cursor: pointer; transition: all .2s;
  display: flex; align-items: center; justify-content: center; gap: .5rem;
}
.tab:hover { background: #f8fafc; color: #334155; }
.tab.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white; box-shadow: 0 4px 12px rgba(102,126,234,.4);
}
.tab-icon { font-size: 1.25rem; }

.content { max-width: 1200px; margin: 0 auto; }

.section-title { font-size: 1.5rem; font-weight: 600; color: #1e293b; margin: 0 0 1rem; }

.create-section, .upload-section {
  background: white; padding: 1.5rem; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.05); margin-bottom: 2rem;
}

.input-group { display: flex; gap: .75rem; flex-wrap: wrap; }
.input {
  padding: .75rem 1rem; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 1rem;
  transition: all .2s; background: #f8fafc;
}
.input:focus { outline: none; border-color: #667eea; background: white; }
.input-title { flex: 1; min-width: 200px; }
.input-desc { flex: 2; min-width: 300px; }

.btn {
  padding: .75rem 1.5rem; border: none; border-radius: 8px; font-size: 1rem; font-weight: 500;
  cursor: pointer; transition: all .2s; display: flex; align-items: center; gap: .5rem;
}
.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
  box-shadow: 0 4px 12px rgba(102,126,234,.3);
}
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(102,126,234,.4); }
.btn-secondary { background: #f1f5f9; color: #475569; }
.btn-secondary:hover { background: #e2e8f0; }
.btn-success { background: #10b981; color: white; }
.btn-success:hover { background: #059669; }
.btn-icon { font-size: 1.125rem; }

.list-section, .gallery-section { margin-bottom: 2rem; }
.empty-state { text-align: center; padding: 3rem 1rem; color: #94a3b8; }
.empty-icon { font-size: 4rem; margin-bottom: 1rem; }

.items-grid {
  display: grid; gap: 1rem; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
}
.item-card {
  background: white; padding: 1.5rem; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.05); transition: all .2s;
}
.item-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.1); }
.item-content { margin-bottom: 1rem; }
.item-title { font-size: 1.25rem; font-weight: 600; color: #1e293b; margin: 0 0 .5rem; }
.item-description { color: #64748b; margin: 0; line-height: 1.6; }
.item-actions { display: flex; gap: .5rem; }
.btn-icon-action { padding: .5rem .75rem; border: none; border-radius: 6px; font-size: 1.125rem; cursor: pointer; transition: all .2s; }
.btn-icon-action.edit { background: #e0e7ff; }
.btn-icon-action.edit:hover { background: #c7d2fe; }
.btn-icon-action.delete { background: #fee2e2; }
.btn-icon-action.delete:hover { background: #fecaca; }
.edit-form { display: flex; flex-direction: column; gap: .75rem; }
.edit-actions { display: flex; gap: .5rem; }

.upload-controls { display: flex; gap: .75rem; flex-wrap: wrap; margin-bottom: 1rem; }
.upload-label {
  display: flex; align-items: center; gap: .5rem; padding: .75rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
  border-radius: 8px; cursor: pointer; font-weight: 500; transition: all .2s;
  box-shadow: 0 4px 12px rgba(102,126,234,.3);
}
.upload-label:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(102,126,234,.4); }
.upload-label input[type="file"] { display: none; }
.upload-icon { font-size: 1.125rem; }
.status-loading { color: #667eea; font-weight: 500; }
.status-error { color: #ef4444; font-weight: 500; padding: .75rem; background: #fee2e2; border-radius: 8px; }

.photos-grid {
  display: grid; gap: 1.5rem; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
}
.photo-card {
  background: white; border-radius: 12px; overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,.05); transition: all .2s;
}
.photo-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,.15); }
.photo-link { display: block; position: relative; overflow: hidden; }
.photo-img { width: 100%; height: 200px; object-fit: cover; display: block; transition: transform .3s; }
.photo-link:hover .photo-img { transform: scale(1.05); }
.photo-overlay {
  position: absolute; inset: 0; background: rgba(0,0,0,.5);
  display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity .2s;
}
.photo-link:hover .photo-overlay { opacity: 1; }
.view-icon { font-size: 2rem; }
.photo-meta { padding: 1rem; }
.photo-name {
  font-weight: 500; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: .25rem;
}
.photo-info { font-size: .875rem; color: #94a3b8; }
.photo-actions { display: flex; gap: .5rem; padding: 0 1rem 1rem; }
.photo-action-btn {
  flex: 1; padding: .5rem; border: none; border-radius: 6px; font-size: 1.125rem; cursor: pointer; text-align: center; text-decoration: none; transition: all .2s;
}
.photo-action-btn.download { background: #dbeafe; color: #1e40af; }
.photo-action-btn.download:hover { background: #bfdbfe; }
.photo-action-btn.delete { background: #fee2e2; color: #991b1b; }
.photo-action-btn.delete:hover { background: #fecaca; }

@media (max-width: 768px) {
  .title { font-size: 2rem; }
  .input-group { flex-direction: column; }
  .input-title, .input-desc { width: 100%; }
  .items-grid, .photos-grid { grid-template-columns: 1fr; }
}
</style>

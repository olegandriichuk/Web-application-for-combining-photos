<script setup lang="ts">
import { ref, onMounted } from "vue";
import { listItems, createItem, updateItem, deleteItem, type Item } from "./api/items";

const items = ref<Item[]>([]);
const newTitle = ref("");
const newDesc = ref("");
const editing = ref<Item | null>(null);

const load = async () => { items.value = await listItems(); };

const add = async () => {
  if (!newTitle.value.trim()) return;
  await createItem({ title: newTitle.value, description: newDesc.value });
  newTitle.value = ""; newDesc.value = "";
  await load();
};

const startEdit = (it: Item) => { editing.value = { ...it }; };
const saveEdit = async () => {
  if (!editing.value) return;
  await updateItem(editing.value.id, { title: editing.value.title, description: editing.value.description });
  editing.value = null;
  await load();
};
const cancelEdit = () => { editing.value = null; };
const removeIt = async (id: number) => { await deleteItem(id); await load(); };

onMounted(load);
</script>

<template>
  <main style="max-width:820px;margin:2rem auto;padding:1rem">
    <h1>Items CRUD (FastAPI + Vue)</h1>

    <section style="margin:1rem 0;padding:1rem;border:1px solid #ddd;border-radius:8px">
      <h3>Create</h3>
      <input v-model="newTitle" placeholder="Title" style="padding:.5rem;margin-right:.5rem;width:240px" />
      <input v-model="newDesc" placeholder="Description" style="padding:.5rem;margin-right:.5rem;width:360px" />
      <button @click="add">Add</button>
    </section>

    <section>
      <h3>List</h3>
      <div v-for="it in items" :key="it.id" style="border:1px solid #eee;padding:1rem;margin:.5rem 0;border-radius:8px">
        <template v-if="editing && editing.id === it.id">
          <input v-model="editing.title" style="padding:.5rem;margin-right:.5rem;width:240px" />
          <input v-model="editing.description" style="padding:.5rem;margin-right:.5rem;width:360px" />
          <button @click="saveEdit">Save</button>
          <button @click="cancelEdit" style="margin-left:.5rem">Cancel</button>
        </template>
        <template v-else>
          <div><strong>{{ it.title }}</strong></div>
          <div style="opacity:.75">{{ it.description }}</div>
          <div style="margin-top:.5rem">
            <button @click="startEdit(it)">Edit</button>
            <button @click="removeIt(it.id)" style="margin-left:.5rem">Delete</button>
          </div>
        </template>
      </div>
    </section>
  </main>
</template>

<style>
button { padding: .5rem .75rem; cursor: pointer; }
</style>

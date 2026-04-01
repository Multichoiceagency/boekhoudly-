<script setup lang="ts">
const props = defineProps<{
  connectionId: string
  provider: string
  providerName: string
}>()

const emit = defineEmits<{
  (e: 'import', file: any): void
  (e: 'close'): void
}>()

const api = useApi()
const files = ref<any[]>([])
const loading = ref(true)
const error = ref('')
const currentFolder = ref<string | null>(null)
const folderStack = ref<{ id: string | null; name: string }[]>([{ id: null, name: 'Root' }])
const importing = ref<Set<string>>(new Set())

async function loadFiles(folderId: string | null = null) {
  loading.value = true
  error.value = ''
  try {
    const params = folderId ? `?folder_id=${encodeURIComponent(folderId)}` : ''
    const data = await api.get<any>(`/cloud/files/${props.connectionId}${params}`)
    files.value = data.files || []
  } catch (e: any) {
    error.value = e.message || 'Kon bestanden niet laden'
  } finally {
    loading.value = false
  }
}

function openFolder(folder: any) {
  currentFolder.value = folder.id
  folderStack.value.push({ id: folder.id, name: folder.name })
  loadFiles(folder.id)
}

function goToFolder(index: number) {
  folderStack.value = folderStack.value.slice(0, index + 1)
  currentFolder.value = folderStack.value[index].id
  loadFiles(currentFolder.value)
}

async function importFile(file: any) {
  importing.value.add(file.id)
  try {
    await api.post(`/cloud/import/${props.connectionId}`, {
      file_id: file.id,
      file_name: file.name,
      file_path: file.path || null,
    })
    emit('import', file)
  } catch (e: any) {
    error.value = e.message || 'Import mislukt'
  } finally {
    importing.value.delete(file.id)
  }
}

function isImportable(file: any) {
  if (file.type === 'folder') return false
  const ext = file.name?.split('.').pop()?.toLowerCase()
  return ['pdf', 'jpg', 'jpeg', 'png', 'csv', 'xlsx', 'xls'].includes(ext)
}

function getFileIcon(file: any) {
  if (file.type === 'folder') return '📁'
  const ext = file.name?.split('.').pop()?.toLowerCase()
  if (['pdf'].includes(ext)) return '📄'
  if (['jpg', 'jpeg', 'png'].includes(ext)) return '🖼️'
  if (['csv', 'xlsx', 'xls'].includes(ext)) return '📊'
  return '📎'
}

function formatSize(bytes: number) {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

onMounted(() => loadFiles())
</script>

<template>
  <div class="bg-white border border-gray-200 rounded-2xl overflow-hidden">
    <!-- Header -->
    <div class="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-100">
      <div class="flex items-center gap-2">
        <span class="text-sm font-semibold text-gray-900">{{ providerName }}</span>
        <!-- Breadcrumb -->
        <div class="flex items-center gap-1 text-xs text-gray-400">
          <template v-for="(folder, i) in folderStack" :key="i">
            <span v-if="i > 0">/</span>
            <button @click="goToFolder(i)" class="hover:text-emerald-600 transition-colors" :class="i === folderStack.length - 1 ? 'text-gray-700 font-medium' : ''">
              {{ folder.name }}
            </button>
          </template>
        </div>
      </div>
      <button @click="emit('close')" class="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
      </button>
    </div>

    <!-- Error -->
    <div v-if="error" class="px-4 py-2 bg-red-50 text-sm text-red-600">{{ error }}</div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-8">
      <svg class="w-5 h-5 text-emerald-600 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- File list -->
    <div v-else class="max-h-80 overflow-y-auto divide-y divide-gray-50">
      <div v-if="!files.length" class="px-4 py-8 text-center text-sm text-gray-400">
        Geen bestanden gevonden
      </div>
      <div
        v-for="file in files"
        :key="file.id"
        class="flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 transition-colors"
      >
        <div class="flex items-center gap-3 min-w-0 flex-1">
          <span class="text-base flex-shrink-0">{{ getFileIcon(file) }}</span>
          <div class="min-w-0">
            <button
              v-if="file.type === 'folder'"
              @click="openFolder(file)"
              class="text-sm font-medium text-gray-900 hover:text-emerald-600 truncate block"
            >
              {{ file.name }}
            </button>
            <p v-else class="text-sm text-gray-700 truncate">{{ file.name }}</p>
            <p v-if="file.size" class="text-xs text-gray-400">{{ formatSize(file.size) }}</p>
          </div>
        </div>
        <button
          v-if="isImportable(file)"
          @click="importFile(file)"
          :disabled="importing.has(file.id)"
          class="flex-shrink-0 ml-2 px-3 py-1 text-xs font-medium text-emerald-700 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-colors disabled:opacity-50"
        >
          {{ importing.has(file.id) ? 'Importeren...' : 'Importeer' }}
        </button>
      </div>
    </div>
  </div>
</template>

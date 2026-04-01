<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-900">Instellingen</h1>

    <div class="flex gap-1 bg-surface-100 p-1 rounded-lg w-fit flex-wrap">
      <button v-for="tab in visibleTabs" :key="tab" @click="activeTab = tab" class="px-3 md:px-4 py-2 text-xs md:text-sm font-medium rounded-md transition-colors" :class="activeTab === tab ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'">{{ tab }}</button>
    </div>

    <!-- Bedrijf -->
    <div v-if="activeTab === 'Bedrijf'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Bedrijfsgegevens</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Bedrijfsnaam</label><input v-model="brandingForm.companyName" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">KvK-nummer</label><input v-model="brandingForm.kvk" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">BTW-nummer</label><input v-model="brandingForm.btw" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">IBAN</label><input v-model="brandingForm.iban" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">E-mailadres</label><input v-model="brandingForm.email" type="email" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Telefoon</label><input v-model="brandingForm.phone" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Website</label><input v-model="brandingForm.website" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div class="md:col-span-2"><label class="block text-sm font-medium text-slate-700 mb-1">Adres</label><input v-model="brandingForm.address" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Postcode</label><input v-model="brandingForm.postcode" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Plaats</label><input v-model="brandingForm.city" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
      </div>
      <div class="mt-6 pt-4 border-t border-surface-200">
        <button @click="saveBranding" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Opslaan</button>
        <span v-if="saved" class="ml-3 text-sm text-emerald-600">Opgeslagen!</span>
      </div>
    </div>

    <!-- Branding -->
    <div v-if="activeTab === 'Branding'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Huisstijl</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Logo</label>
          <div class="border-2 border-dashed border-surface-300 rounded-xl p-6 text-center cursor-pointer hover:border-primary-400" @click="($refs as any).logoInput?.click()">
            <input ref="logoInput" type="file" accept="image/*" class="hidden" @change="handleLogoUpload" />
            <div v-if="brandingForm.logo" class="flex justify-center mb-2"><img :src="brandingForm.logo" class="max-h-16" /></div>
            <p class="text-sm text-slate-500">{{ brandingForm.logo ? 'Klik om te wijzigen' : 'Upload je logo (PNG, SVG)' }}</p>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2">Primaire kleur</label>
          <div class="flex items-center gap-4">
            <input type="color" v-model="brandingForm.primaryColor" class="w-12 h-12 rounded-lg border border-surface-200 cursor-pointer" />
            <input type="text" v-model="brandingForm.primaryColor" class="px-3 py-2 border border-surface-200 rounded-lg text-sm w-32 font-mono" />
          </div>
          <div class="flex gap-2 mt-3 flex-wrap">
            <button v-for="color in presetColors" :key="color" @click="brandingForm.primaryColor = color" class="w-8 h-8 rounded-lg border-2 transition-all" :style="{ backgroundColor: color }" :class="brandingForm.primaryColor === color ? 'border-slate-900 scale-110' : 'border-transparent'" />
          </div>
        </div>
      </div>
      <div class="mt-6 pt-4 border-t border-surface-200">
        <button @click="saveBranding" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Branding opslaan</button>
      </div>
    </div>

    <!-- Gebruikers (Admin) -->
    <div v-if="activeTab === 'Gebruikers'" class="space-y-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold text-slate-900">Gebruikersbeheer</h2>
          <button @click="showUserModal = true" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
            Nieuwe gebruiker
          </button>
        </div>

        <div v-if="usersLoading" class="py-8 text-center text-slate-500 text-sm">Laden...</div>
        <div v-else-if="users.length === 0" class="py-8 text-center text-slate-400 text-sm">Geen gebruikers gevonden</div>
        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
                <th class="px-4 py-3">Naam</th>
                <th class="px-4 py-3">Email</th>
                <th class="px-4 py-3">Rol</th>
                <th class="px-4 py-3">Status</th>
                <th class="px-4 py-3">Acties</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-100">
              <tr v-for="u in users" :key="u.id" class="hover:bg-surface-50">
                <td class="px-4 py-3 text-sm font-medium text-slate-900">{{ u.full_name }}</td>
                <td class="px-4 py-3 text-sm text-slate-600">{{ u.email }}</td>
                <td class="px-4 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium" :class="roleColor(u.role)">{{ roleLabel(u.role) }}</span></td>
                <td class="px-4 py-3"><span class="inline-flex px-2 py-0.5 rounded-full text-xs font-medium" :class="u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'">{{ u.is_active ? 'Actief' : 'Inactief' }}</span></td>
                <td class="px-4 py-3">
                  <div class="flex gap-2">
                    <button @click="editUser(u)" class="text-slate-400 hover:text-primary-600 text-xs">Bewerken</button>
                    <button v-if="u.id !== currentUser?.id" @click="deleteUserById(u.id)" class="text-slate-400 hover:text-red-600 text-xs">Verwijderen</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Create/Edit User Modal -->
      <div v-if="showUserModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="showUserModal = false">
        <div class="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
          <h2 class="text-lg font-semibold text-slate-900 mb-4">{{ editingUser ? 'Gebruiker bewerken' : 'Nieuwe gebruiker' }}</h2>
          <div v-if="userError" class="mb-4 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">{{ userError }}</div>
          <div class="space-y-4">
            <div><label class="block text-sm font-medium text-slate-700 mb-1">Volledige naam</label><input v-model="userForm.full_name" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
            <div><label class="block text-sm font-medium text-slate-700 mb-1">E-mailadres</label><input v-model="userForm.email" type="email" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" :disabled="!!editingUser" /></div>
            <div v-if="!editingUser"><label class="block text-sm font-medium text-slate-700 mb-1">Wachtwoord (optioneel)</label><input v-model="userForm.password" type="password" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" placeholder="Laat leeg voor email-login" /></div>
            <div>
              <label class="block text-sm font-medium text-slate-700 mb-1">Rol</label>
              <select v-model="userForm.role" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm">
                <option value="user">Gebruiker</option>
                <option value="accountant">Accountant</option>
                <option value="admin">Beheerder</option>
              </select>
            </div>
          </div>
          <div class="flex justify-end gap-3 mt-6 pt-4 border-t border-surface-200">
            <button @click="showUserModal = false; editingUser = null" class="px-4 py-2 text-sm font-medium text-slate-700">Annuleren</button>
            <button @click="saveUser" :disabled="userSaving" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50">
              {{ userSaving ? 'Opslaan...' : (editingUser ? 'Opslaan' : 'Aanmaken') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Perfex CRM -->
    <div v-if="activeTab === 'Perfex CRM'" class="space-y-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <div class="flex items-center gap-3 mb-6">
          <div class="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
          </div>
          <div>
            <h2 class="text-lg font-semibold text-slate-900">Perfex CRM Koppeling</h2>
            <p class="text-sm text-slate-500">Importeer klanten, facturen en uitgaven vanuit Perfex CRM</p>
          </div>
        </div>

        <div class="space-y-4 max-w-xl">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Perfex CRM URL</label>
            <input v-model="perfexUrl" type="url" placeholder="https://crm.jouwbedrijf.nl" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">API Key</label>
            <input v-model="perfexApiKey" :type="showApiKey ? 'text' : 'password'" placeholder="pk_..." class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm font-mono" />
            <button @click="showApiKey = !showApiKey" class="text-xs text-slate-500 mt-1 hover:text-slate-700">{{ showApiKey ? 'Verbergen' : 'Tonen' }}</button>
          </div>
        </div>

        <!-- Connection status -->
        <div v-if="perfexStatus" class="mt-4 p-3 rounded-xl text-sm" :class="perfexStatus === 'connected' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700' : 'bg-red-50 border border-red-200 text-red-700'">
          {{ perfexMessage }}
        </div>

        <!-- Sync results -->
        <div v-if="perfexSyncResult" class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <p class="text-sm font-semibold text-blue-900 mb-2">Import resultaat:</p>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div v-for="(count, resource) in perfexSyncResult" :key="resource" class="text-center">
              <p class="text-lg font-bold text-blue-700">{{ count }}</p>
              <p class="text-xs text-blue-600 capitalize">{{ resource }}</p>
            </div>
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-surface-200 flex flex-wrap gap-3">
          <button @click="testPerfexConnection" :disabled="perfexTesting" class="border border-surface-300 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-surface-50 disabled:opacity-50">
            {{ perfexTesting ? 'Testen...' : 'Verbinding testen' }}
          </button>
          <button @click="syncPerfexData" :disabled="perfexSyncing || perfexStatus !== 'connected'" class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2">
            <svg v-if="perfexSyncing" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
            {{ perfexSyncing ? 'Importeren...' : 'Alle data importeren' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Integraties -->
    <div v-if="activeTab === 'Integraties'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Integraties</h2>
      <p class="text-sm text-slate-500">Koppel je bankrekenig, cloud opslag en meer.</p>
    </div>

    <!-- Abonnement -->
    <div v-if="activeTab === 'Abonnement'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Abonnement</h2>
      <div class="bg-primary-50 border border-primary-200 rounded-xl p-6">
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div><p class="text-lg font-bold text-primary-900">FiscalFlow Pro</p><p class="text-sm text-primary-600 mt-1">Onbeperkt documenten, AI classificatie, BTW aangiftes, Jaarrekening</p></div>
          <div class="text-left md:text-right"><p class="text-2xl font-bold text-primary-900">€ 49<span class="text-sm font-normal">/maand</span></p></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const ws = useWorkspaceStore()
const api = useApi()
const { user: currentUser, isAdmin } = useAuth()

const activeTab = ref('Bedrijf')
const allTabs = ['Bedrijf', 'Branding', 'Gebruikers', 'Perfex CRM', 'Integraties', 'Abonnement']
const visibleTabs = computed(() => isAdmin.value ? allTabs : allTabs.filter(t => t !== 'Gebruikers'))

const saved = ref(false)
const presetColors = ['#4F46E5', '#2563EB', '#0891B2', '#059669', '#D97706', '#DC2626', '#7C3AED', '#EC4899']

const brandingForm = reactive({ ...ws.activeCompany.branding })

watch(() => ws.activeCompanyId, () => {
  Object.assign(brandingForm, ws.activeCompany.branding)
})

async function saveBranding() {
  try {
    await ws.updateBranding(ws.activeCompanyId, { ...brandingForm })
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } catch (e: any) {
    alert(e.message || 'Opslaan mislukt')
  }
}

function handleLogoUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = () => { brandingForm.logo = reader.result as string }
    reader.readAsDataURL(file)
  }
}

// ---- Admin User Management ----
const users = ref<any[]>([])
const usersLoading = ref(false)
const showUserModal = ref(false)
const editingUser = ref<any>(null)
const userSaving = ref(false)
const userError = ref('')
const userForm = reactive({ full_name: '', email: '', password: '', role: 'user' })

async function loadUsers() {
  usersLoading.value = true
  try {
    users.value = await api.get('/admin/users')
  } catch { users.value = [] }
  finally { usersLoading.value = false }
}

function editUser(u: any) {
  editingUser.value = u
  userForm.full_name = u.full_name
  userForm.email = u.email
  userForm.role = u.role
  userForm.password = ''
  userError.value = ''
  showUserModal.value = true
}

async function saveUser() {
  userError.value = ''
  if (!userForm.full_name || !userForm.email) {
    userError.value = 'Naam en email zijn verplicht'
    return
  }
  userSaving.value = true
  try {
    if (editingUser.value) {
      await api.put(`/admin/users/${editingUser.value.id}`, {
        full_name: userForm.full_name,
        role: userForm.role,
        ...(userForm.password ? { password: userForm.password } : {}),
      })
    } else {
      await api.post('/admin/users', { ...userForm })
    }
    showUserModal.value = false
    editingUser.value = null
    await loadUsers()
  } catch (e: any) {
    userError.value = e.message || 'Opslaan mislukt'
  } finally { userSaving.value = false }
}

async function deleteUserById(id: string) {
  if (!confirm('Weet je zeker dat je deze gebruiker wilt verwijderen?')) return
  try {
    await api.delete(`/admin/users/${id}`)
    await loadUsers()
  } catch (e: any) { alert(e.message || 'Verwijderen mislukt') }
}

function roleColor(role: string) {
  return { admin: 'bg-purple-100 text-purple-700', accountant: 'bg-blue-100 text-blue-700', user: 'bg-slate-100 text-slate-700' }[role] || 'bg-slate-100 text-slate-700'
}
function roleLabel(role: string) {
  return { admin: 'Beheerder', accountant: 'Accountant', user: 'Gebruiker' }[role] || role
}

// ---- Perfex CRM ----
const perfexUrl = ref('')
const perfexApiKey = ref('')
const showApiKey = ref(false)
const perfexStatus = ref('')
const perfexMessage = ref('')
const perfexTesting = ref(false)
const perfexSyncing = ref(false)
const perfexSyncResult = ref<Record<string, number> | null>(null)

async function testPerfexConnection() {
  if (!perfexUrl.value || !perfexApiKey.value) {
    perfexStatus.value = 'error'
    perfexMessage.value = 'Vul de URL en API key in'
    return
  }
  perfexTesting.value = true
  perfexSyncResult.value = null
  try {
    const res = await api.post<{ status: string; message: string }>('/perfex/test', {
      url: perfexUrl.value,
      api_key: perfexApiKey.value,
    })
    perfexStatus.value = res.status
    perfexMessage.value = res.message
  } catch (e: any) {
    perfexStatus.value = 'error'
    perfexMessage.value = e.message || 'Verbinding mislukt'
  } finally { perfexTesting.value = false }
}

async function syncPerfexData() {
  perfexSyncing.value = true
  perfexSyncResult.value = null
  try {
    const res = await api.post<{ status: string; data: any; counts: Record<string, number> }>('/perfex/sync', {
      url: perfexUrl.value,
      api_key: perfexApiKey.value,
    })
    perfexSyncResult.value = res.counts

    // Import data into database via workspace store
    const data = res.data
    if (data.customers) {
      for (const c of data.customers) {
        await ws.addDebtor({
          name: c.company || c.name || '',
          email: c.email || '',
          kvk: c.vat || '',
          btw: c.vat || '',
          iban: '',
          paymentTerm: 30,
          address: c.address || '',
          city: c.city || '',
        }).catch(() => {})
      }
    }
    if (data.invoices) {
      for (const inv of data.invoices) {
        const status = inv.status === '2' ? 'betaald' : inv.status === '4' ? 'verlopen' : 'verzonden'
        await ws.addInvoice({
          number: inv.number || `PFX-${inv.id}`,
          client: inv.client_name || inv.company || '',
          clientId: '',
          date: inv.date || new Date().toISOString().split('T')[0],
          dueDate: inv.duedate || inv.date || new Date().toISOString().split('T')[0],
          lines: (inv.items || []).map((item: any) => ({
            desc: item.description || '',
            qty: parseFloat(item.qty) || 1,
            price: parseFloat(item.rate) || 0,
            btwRate: parseFloat(item.taxrate) || 21,
          })),
          status,
        }).catch(() => {})
      }
    }
    if (data.expenses) {
      for (const exp of data.expenses) {
        await ws.addExpense({
          date: exp.date || new Date().toISOString().split('T')[0],
          description: exp.name || exp.description || '',
          category: exp.category_name || 'Overig',
          amount: parseFloat(exp.amount) || 0,
          btwRate: parseFloat(exp.tax) || 21,
          status: 'geboekt',
        }).catch(() => {})
      }
    }
  } catch (e: any) {
    perfexStatus.value = 'error'
    perfexMessage.value = e.message || 'Sync mislukt'
  } finally { perfexSyncing.value = false }
}

// Load users on mount if admin
onMounted(() => {
  if (isAdmin.value) loadUsers()
})

watch(activeTab, (tab) => {
  if (tab === 'Gebruikers' && isAdmin.value && users.value.length === 0) loadUsers()
})
</script>

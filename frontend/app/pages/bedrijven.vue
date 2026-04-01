<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Bedrijvenstructuur</h1>
      <button @click="showAddModal = true" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
        Bedrijf toevoegen
      </button>
    </div>

    <!-- Active company -->
    <div class="bg-primary-50 border border-primary-200 rounded-xl p-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center text-white font-bold">{{ activeBedrijf.naam[0] }}</div>
        <div>
          <p class="text-sm font-semibold text-primary-900">{{ activeBedrijf.naam }}</p>
          <p class="text-xs text-primary-600">Actief bedrijf | KvK: {{ activeBedrijf.kvk }}</p>
        </div>
      </div>
      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-600 text-white">Actief</span>
    </div>

    <!-- Structure visualization -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Organisatiestructuur</h2>
      <div class="flex flex-col items-center">
        <!-- Holding -->
        <div v-if="holdingBedrijf" class="bg-slate-900 text-white rounded-xl p-4 w-64 text-center">
          <p class="text-sm font-bold">{{ holdingBedrijf.naam }}</p>
          <p class="text-xs text-slate-300">{{ holdingBedrijf.type }} | {{ holdingBedrijf.kvk }}</p>
        </div>
        <div v-if="holdingBedrijf && werkbedrijven.length > 0" class="w-px h-8 bg-slate-300"></div>
        <!-- Connector line -->
        <div v-if="werkbedrijven.length > 1 && holdingBedrijf" class="flex items-center">
          <div class="h-px bg-slate-300" :style="{ width: (werkbedrijven.length - 1) * 280 + 'px' }"></div>
        </div>
        <!-- Werk-BVs -->
        <div class="flex gap-6 mt-2">
          <div v-for="bedrijf in werkbedrijven" :key="bedrijf.id" class="flex flex-col items-center">
            <div v-if="holdingBedrijf" class="w-px h-6 bg-slate-300"></div>
            <div
              class="rounded-xl p-4 w-64 text-center border-2 cursor-pointer transition-all hover:shadow-md"
              :class="bedrijf.id === activeBedrijf.id ? 'border-primary-500 bg-primary-50' : 'border-surface-200 bg-white'"
              @click="switchBedrijf(bedrijf)"
            >
              <div class="flex items-center justify-center gap-2">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" :class="bedrijf.id === activeBedrijf.id ? 'bg-primary-600 text-white' : 'bg-surface-200 text-slate-600'">
                  {{ bedrijf.naam[0] }}
                </div>
                <div class="text-left">
                  <p class="text-sm font-semibold text-slate-900">{{ bedrijf.naam }}</p>
                  <p class="text-[10px] text-slate-500">{{ bedrijf.type }}</p>
                </div>
              </div>
              <div class="mt-3 grid grid-cols-2 gap-2 text-[10px]">
                <div class="bg-surface-50 rounded p-1"><p class="text-slate-500">Omzet</p><p class="font-bold text-slate-900">{{ fc(bedrijf.omzet) }}</p></div>
                <div class="bg-surface-50 rounded p-1"><p class="text-slate-500">Winst</p><p class="font-bold" :class="bedrijf.winst >= 0 ? 'text-emerald-600' : 'text-red-600'">{{ fc(bedrijf.winst) }}</p></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- All companies table -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-surface-200"><h2 class="text-lg font-semibold text-slate-900">Alle bedrijven</h2></div>
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Bedrijf</th>
            <th class="px-6 py-3">Type</th>
            <th class="px-6 py-3">KvK</th>
            <th class="px-6 py-3">BTW-nr</th>
            <th class="px-6 py-3 text-right">Omzet YTD</th>
            <th class="px-6 py-3 text-right">Winst YTD</th>
            <th class="px-6 py-3">Agents</th>
            <th class="px-6 py-3">Acties</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="b in bedrijven" :key="b.id" class="hover:bg-surface-50" :class="b.id === activeBedrijf.id ? 'bg-primary-50/50' : ''">
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold" :class="b.id === activeBedrijf.id ? 'bg-primary-600 text-white' : 'bg-surface-200 text-slate-600'">{{ b.naam[0] }}</div>
                <div>
                  <p class="text-sm font-medium text-slate-900">{{ b.naam }}</p>
                  <p class="text-xs text-slate-500">{{ b.activiteiten }}</p>
                </div>
              </div>
            </td>
            <td class="px-6 py-4 text-sm text-slate-600">{{ b.type }}</td>
            <td class="px-6 py-4 text-sm text-slate-600">{{ b.kvk }}</td>
            <td class="px-6 py-4 text-sm text-slate-600">{{ b.btw }}</td>
            <td class="px-6 py-4 text-sm text-right font-medium text-slate-900">{{ fc(b.omzet) }}</td>
            <td class="px-6 py-4 text-sm text-right font-medium" :class="b.winst >= 0 ? 'text-emerald-600' : 'text-red-600'">{{ fc(b.winst) }}</td>
            <td class="px-6 py-4">
              <div class="flex gap-1">
                <span v-for="a in b.agents" :key="a" class="text-xs px-1.5 py-0.5 rounded bg-surface-100 text-slate-600" :title="a">{{ agentIcons[a] || '🤖' }}</span>
              </div>
            </td>
            <td class="px-6 py-4">
              <div class="flex gap-2">
                <button @click="switchBedrijf(b)" class="text-primary-600 hover:text-primary-700 text-sm font-medium">
                  {{ b.id === activeBedrijf.id ? 'Actief' : 'Activeer' }}
                </button>
                <button @click="selectedBedrijf = b" class="text-slate-400 hover:text-slate-600">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Agent config per bedrijf -->
    <div v-if="selectedBedrijf" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-slate-900">AI Agents - {{ selectedBedrijf.naam }}</h2>
        <button @click="selectedBedrijf = null" class="text-slate-400 hover:text-slate-600"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg></button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-5 gap-3">
        <div v-for="agent in allAgents" :key="agent.key" class="border rounded-lg p-3" :class="selectedBedrijf.agents.includes(agent.key) ? 'border-primary-300 bg-primary-50' : 'border-surface-200'">
          <div class="flex items-center justify-between mb-2">
            <span class="text-lg">{{ agent.icon }}</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" :checked="selectedBedrijf.agents.includes(agent.key)" @change="toggleAgent(agent.key)" class="sr-only peer" />
              <div class="w-9 h-5 bg-surface-200 peer-focus:ring-2 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
          <p class="text-xs font-semibold text-slate-900">{{ agent.name }}</p>
          <p class="text-[10px] text-slate-500">{{ agent.desc }}</p>
        </div>
      </div>
    </div>

    <!-- Add modal -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showAddModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Nieuw bedrijf toevoegen</h2>
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2"><label class="block text-sm font-medium text-slate-700 mb-1">Bedrijfsnaam</label><input type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Type</label>
            <select class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm">
              <option>Eenmanszaak</option><option>BV (Werk-BV)</option><option>BV (Holding)</option><option>VOF</option><option>Stichting</option>
            </select>
          </div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">KvK-nummer</label><input type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">BTW-nummer</label><input type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Activiteiten</label><input type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div class="col-span-2"><label class="block text-sm font-medium text-slate-700 mb-1">Moederbedrijf (optioneel)</label>
            <select class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm">
              <option value="">Geen (zelfstandig)</option>
              <option v-for="b in bedrijven.filter(x => x.type.includes('Holding'))" :key="b.id">{{ b.naam }}</option>
            </select>
          </div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showAddModal = false" class="px-4 py-2 text-sm font-medium text-slate-700">Annuleren</button>
          <button @click="showAddModal = false" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Toevoegen</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const showAddModal = ref(false)
const selectedBedrijf = ref<any>(null)

const agentIcons: Record<string, string> = {
  boekhouder: '📒', btw: '🧾', audit: '🔍', accountant: '📊', advisor: '💡',
}

const allAgents = [
  { key: 'boekhouder', icon: '📒', name: 'Boekhouder', desc: 'Categorisatie & boekingen' },
  { key: 'btw', icon: '🧾', name: 'BTW Agent', desc: 'Aangifte & regelcheck' },
  { key: 'audit', icon: '🔍', name: 'Audit Agent', desc: 'Foutdetectie & compliance' },
  { key: 'accountant', icon: '📊', name: 'Accountant', desc: 'Jaarrekening & rapportage' },
  { key: 'advisor', icon: '💡', name: 'Advisor', desc: 'Belastingtips & besparing' },
]

const bedrijven = reactive([
  { id: 1, naam: 'De Vries Holding BV', type: 'BV (Holding)', kvk: '87654321', btw: 'NL987654321B01', activiteiten: 'Houdstermaatschappij', omzet: 0, winst: 0, parentId: null, agents: ['accountant', 'advisor'] },
  { id: 2, naam: 'De Vries Digital BV', type: 'BV (Werk-BV)', kvk: '12345678', btw: 'NL123456789B01', activiteiten: 'Communicatie- en grafisch ontwerp', omzet: 142500, winst: 35398, parentId: 1, agents: ['boekhouder', 'btw', 'audit', 'accountant', 'advisor'] },
  { id: 3, naam: 'De Vries Consulting', type: 'Eenmanszaak', kvk: '34567890', btw: 'NL345678901B01', activiteiten: 'Management consultancy', omzet: 48000, winst: 22000, parentId: null, agents: ['boekhouder', 'btw', 'accountant'] },
])

const activeBedrijf = ref(bedrijven[1])
const holdingBedrijf = computed(() => bedrijven.find((b) => b.type.includes('Holding')))
const werkbedrijven = computed(() => bedrijven.filter((b) => !b.type.includes('Holding')))

function fc(v: number): string {
  return '€ ' + v.toLocaleString('nl-NL')
}

function switchBedrijf(b: any) {
  activeBedrijf.value = b
}

function toggleAgent(key: string) {
  if (!selectedBedrijf.value) return
  const idx = selectedBedrijf.value.agents.indexOf(key)
  if (idx >= 0) selectedBedrijf.value.agents.splice(idx, 1)
  else selectedBedrijf.value.agents.push(key)
}
</script>

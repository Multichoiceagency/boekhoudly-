<template>
  <div class="flex gap-6 h-[calc(100vh-7rem)]">
    <!-- Left: AI Agents -->
    <div class="w-72 flex-shrink-0 space-y-3 overflow-y-auto">
      <h2 class="text-lg font-semibold text-slate-900">AI Agents</h2>
      <div
        v-for="agent in agents"
        :key="agent.name"
        class="bg-white rounded-xl border border-surface-200 shadow-sm p-4 cursor-pointer hover:shadow-md transition-shadow"
        :class="selectedAgent === agent.name ? 'ring-2 ring-primary-500' : ''"
        @click="selectedAgent = agent.name"
      >
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="agent.bgColor">
            <span class="text-lg">{{ agent.icon }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <p class="text-sm font-semibold text-slate-900 truncate">{{ agent.name }}</p>
              <span class="w-2 h-2 rounded-full flex-shrink-0" :class="agent.active ? 'bg-emerald-500' : 'bg-slate-300'"></span>
            </div>
            <p class="text-xs text-slate-500 truncate">{{ agent.role }}</p>
          </div>
        </div>
        <div class="mt-2 flex flex-wrap gap-1">
          <span v-for="skill in agent.skills" :key="skill" class="text-[10px] px-1.5 py-0.5 bg-surface-100 text-slate-600 rounded">
            {{ skill }}
          </span>
        </div>
      </div>
    </div>

    <!-- Center: Chat -->
    <div class="flex-1 flex flex-col bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <!-- Chat header -->
      <div class="px-6 py-4 border-b border-surface-200 flex items-center gap-3">
        <div class="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <div>
          <h2 class="text-sm font-semibold text-slate-900">AI Accountant</h2>
          <p class="text-xs text-emerald-600">Online - 5 agents actief</p>
        </div>
      </div>

      <!-- Messages -->
      <div ref="chatContainer" class="flex-1 overflow-y-auto p-6 space-y-4">
        <div v-for="(msg, i) in messages" :key="i" class="flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <div
            class="max-w-[75%] rounded-2xl px-4 py-3"
            :class="msg.role === 'user'
              ? 'bg-primary-600 text-white rounded-br-md'
              : 'bg-surface-100 text-slate-900 rounded-bl-md'"
          >
            <p v-if="msg.agent" class="text-xs font-semibold mb-1" :class="msg.role === 'user' ? 'text-primary-200' : 'text-primary-600'">
              {{ msg.agent }}
            </p>
            <p class="text-sm whitespace-pre-line">{{ msg.text }}</p>
            <p class="text-[10px] mt-1" :class="msg.role === 'user' ? 'text-primary-200' : 'text-slate-400'">{{ msg.time }}</p>
          </div>
        </div>

        <!-- Typing indicator -->
        <div v-if="isTyping" class="flex justify-start">
          <div class="bg-surface-100 rounded-2xl rounded-bl-md px-4 py-3">
            <div class="flex gap-1">
              <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
              <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
              <span class="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick questions -->
      <div v-if="messages.length <= 3" class="px-6 pb-3 flex flex-wrap gap-2">
        <button
          v-for="q in quickQuestions"
          :key="q"
          @click="sendMessage(q)"
          class="text-xs px-3 py-1.5 bg-primary-50 text-primary-700 rounded-full hover:bg-primary-100 transition-colors"
        >
          {{ q }}
        </button>
      </div>

      <!-- Input -->
      <div class="px-6 py-4 border-t border-surface-200">
        <div class="flex gap-3">
          <input
            v-model="inputText"
            @keyup.enter="sendMessage(inputText)"
            type="text"
            placeholder="Stel een vraag aan je AI accountant..."
            class="flex-1 px-4 py-2.5 bg-surface-50 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <button
            @click="sendMessage(inputText)"
            :disabled="!inputText.trim()"
            class="bg-primary-600 text-white px-4 py-2.5 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            Verstuur
          </button>
        </div>
      </div>
    </div>

    <!-- Right: Insights -->
    <div class="w-72 flex-shrink-0 space-y-4 overflow-y-auto">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <h3 class="text-sm font-semibold text-slate-900 mb-3">AI Inzichten</h3>
        <div v-if="insights.length === 0" class="py-4 text-center">
          <p class="text-xs text-slate-400">Nog geen inzichten beschikbaar</p>
        </div>
        <div v-else class="space-y-3">
          <div v-for="insight in insights" :key="insight.title" class="flex gap-2">
            <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" :class="insight.bgColor">
              <span class="text-xs">{{ insight.icon }}</span>
            </div>
            <div>
              <p class="text-xs font-semibold text-slate-900">{{ insight.title }}</p>
              <p class="text-[11px] text-slate-500">{{ insight.desc }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <h3 class="text-sm font-semibold text-slate-900 mb-3">Recente Agent Acties</h3>
        <div v-if="recentActions.length === 0" class="py-4 text-center">
          <p class="text-xs text-slate-400">Nog geen acties uitgevoerd</p>
        </div>
        <div v-else class="space-y-3">
          <div v-for="action in recentActions" :key="action.text" class="flex gap-2 items-start">
            <span class="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" :class="action.color"></span>
            <div>
              <p class="text-xs text-slate-700">{{ action.text }}</p>
              <p class="text-[10px] text-slate-400">{{ action.time }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl p-4 text-white">
        <p class="text-sm font-semibold">AI Confidence Score</p>
        <p class="text-3xl font-bold mt-1">--</p>
        <p class="text-xs text-primary-200 mt-1">Nog geen data beschikbaar</p>
        <div class="mt-3 w-full bg-primary-400/30 rounded-full h-2">
          <div class="bg-white h-2 rounded-full" style="width: 0%"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const chatContainer = ref<HTMLElement>()
const inputText = ref('')
const isTyping = ref(false)
const selectedAgent = ref('Boekhouder Agent')

const agents = [
  { name: 'Boekhouder Agent', role: 'Categoriseert & boekt', icon: '📒', bgColor: 'bg-emerald-100', active: true, skills: ['Boekingen', 'Categorisatie', 'Matching'] },
  { name: 'BTW Agent', role: 'Berekent & controleert', icon: '🧾', bgColor: 'bg-blue-100', active: true, skills: ['BTW aangifte', 'Regelcheck', 'Deadlines'] },
  { name: 'Audit Agent', role: 'Controleert & scoort', icon: '🔍', bgColor: 'bg-amber-100', active: true, skills: ['Foutdetectie', 'Compliance', 'Scoring'] },
  { name: 'Accountant Agent', role: 'Rapporteert & analyseert', icon: '📊', bgColor: 'bg-purple-100', active: true, skills: ['Jaarrekening', 'Balans', 'W&V'] },
  { name: 'Advisor Agent', role: 'Adviseert & optimaliseert', icon: '💡', bgColor: 'bg-pink-100', active: true, skills: ['Belastingtips', 'Besparing', 'Strategie'] },
]

const quickQuestions = [
  'Hoeveel btw moet ik betalen?',
  'Waar geef ik teveel uit?',
  'Wat is mijn winst dit kwartaal?',
  'Welke facturen staan open?',
  'Geef me belastingtips',
]

const messages = ref<any[]>([])

const insights = ref<any[]>([])

const recentActions = ref<any[]>([])

function getTime(): string {
  return new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })
}

async function sendMessage(text: string) {
  if (!text.trim()) return
  const userText = text.trim()
  inputText.value = ''

  messages.value.push({ role: 'user', text: userText, time: getTime() })
  scrollToBottom()

  isTyping.value = true
  await new Promise((r) => setTimeout(r, 1500))
  isTyping.value = false

  messages.value.push({
    role: 'ai',
    agent: 'AI Accountant',
    text: 'Ik heb je vraag ontvangen. Deze functie wordt binnenkort gekoppeld aan de AI backend. Stel gerust een andere vraag.',
    time: getTime(),
  })
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}
</script>

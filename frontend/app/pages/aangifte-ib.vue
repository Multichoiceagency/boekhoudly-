<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Aangifte Inkomstenbelasting</h1>
      <div class="flex gap-2">
        <select v-model="selectedYear" class="px-3 py-2 border border-surface-200 rounded-lg text-sm">
          <option>2025</option><option>2024</option>
        </select>
        <button @click="status = 'concept'" class="border border-surface-300 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-surface-50 flex items-center gap-2">
          Concept opslaan
        </button>
        <button @click="showApproveModal = true" class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 flex items-center gap-2" :disabled="status === 'ingediend'">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          {{ status === 'ingediend' ? 'Ingediend' : 'Ter goedkeuring sturen' }}
        </button>
        <button @click="printReport" :disabled="generating" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 flex items-center gap-2 disabled:opacity-50">
          <svg v-if="!generating" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
          <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          {{ generating ? 'Genereren...' : 'PDF Uitdraaien' }}
        </button>
      </div>
    </div>

    <!-- Status banner -->
    <div class="rounded-xl p-4 flex items-center gap-3" :class="status === 'concept' ? 'bg-amber-50 border border-amber-200' : status === 'goedkeuring' ? 'bg-blue-50 border border-blue-200' : 'bg-emerald-50 border border-emerald-200'">
      <span class="text-lg">{{ status === 'concept' ? '📝' : status === 'goedkeuring' ? '⏳' : '✅' }}</span>
      <div>
        <p class="text-sm font-medium" :class="status === 'concept' ? 'text-amber-800' : status === 'goedkeuring' ? 'text-blue-800' : 'text-emerald-800'">
          {{ status === 'concept' ? 'Concept - Nog niet verstuurd' : status === 'goedkeuring' ? 'Wacht op goedkeuring klant' : 'Goedgekeurd en ingediend' }}
        </p>
        <p class="text-xs" :class="status === 'concept' ? 'text-amber-600' : status === 'goedkeuring' ? 'text-blue-600' : 'text-emerald-600'">
          Aangifte Inkomstenbelasting {{ selectedYear }} | Afgedrukt op {{ today }}
        </p>
      </div>
    </div>

    <!-- BELASTINGDIENST RAPPORT -->
    <div ref="reportRef" class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <!-- Cover page -->
      <div class="p-8 border-b border-surface-200">
        <div class="flex justify-between items-start">
          <div>
            <p class="text-sm text-slate-400">Eigen kopie, niet opsturen</p>
          </div>
          <div class="text-right text-sm text-slate-600">
            <p><span class="font-semibold">Aangifte</span></p>
            <p>Inkomstenbelasting {{ selectedYear }}</p>
            <p class="mt-2"><span class="font-semibold">Formulierenversie</span></p>
            <p>IB 650E - 2Z41OLAV</p>
            <p class="mt-2"><span class="font-semibold">Afgedrukt op</span></p>
            <p>{{ today }}</p>
          </div>
        </div>
        <div class="mt-12">
          <h2 class="text-2xl font-bold text-slate-900">{{ status === 'concept' ? 'Nog niet verstuurd: ' : '' }}Aangifte Inkomstenbelasting {{ selectedYear }}</h2>
          <div class="mt-4">
            <p class="font-semibold text-slate-900">{{ data.naam }}</p>
            <p class="text-sm text-slate-600">Burgerservicenummer&nbsp;&nbsp;&nbsp;&nbsp;{{ data.bsn }}</p>
          </div>
        </div>
      </div>

      <!-- Persoonlijke gegevens -->
      <ReportSection title="Persoonlijke gegevens" subtitle="Persoonlijke gegevens" :color="sectionColor">
        <ReportRow label="Naam" :value="data.naam" />
        <ReportRow label="Geboortedatum" :value="data.geboortedatum" />
        <ReportRow label="Burgerservicenummer" :value="data.bsn" />
        <ReportRow label="Telefoonnummer" :value="data.telefoon" />
        <ReportRow label="Nummer belastingconsulent" :value="data.consultentNr" />
      </ReportSection>

      <!-- Partner -->
      <ReportSection title="Partner" subtitle="Partner" :color="sectionColor">
        <div class="px-8 py-2 text-sm font-semibold text-slate-700">Echtgenoot/huisgenoot: {{ data.partner ? 'ja' : 'geen' }}</div>
        <ReportRow label="Had u in {{ selectedYear }} een echtgenoot?" :value="data.partner ? 'Ja' : 'Nee'" />
      </ReportSection>

      <!-- Onderneming -->
      <ReportSection title="Gegevens onderneming(en)" subtitle="Gegevens onderneming(en)" :color="sectionColor">
        <div class="px-8 py-2 text-sm font-semibold text-slate-700">Onderneming: {{ data.onderneming.naam }}</div>
        <ReportRow label="Naam onderneming" :value="data.onderneming.naam" />
        <ReportRow label="Omschrijving van de activiteiten" :value="data.onderneming.activiteiten" />
        <ReportRow label="Ondernemingsvorm" :value="data.onderneming.vorm" />
        <ReportRow :label="'Is deze onderneming in dit boekjaar gestart?'" value="Nee" />
        <ReportRow :label="'Wijkt het boekjaar af van het kalenderjaar?'" value="Nee" />
      </ReportSection>

      <!-- Winst-en-verliesrekening -->
      <ReportSection :title="'Winst-en-verliesrekening: ' + data.onderneming.naam" :subtitle="''" :color="sectionColor">
        <ReportRow label="Opbrengsten" :value="fc(data.wv.opbrengsten)" :bold="false" :highlight="true" />
        <ReportRow label="Opbrengsten uit leveringen en diensten" :value="fc(data.wv.opbrengsten)" />
        <ReportRow label="Totaal opbrengsten" :value="fc(data.wv.opbrengsten)" :bold="true" :subtotal="true" />

        <div class="h-4"></div>
        <ReportRow label="Inkoopkosten, uitbesteed werk en andere externe kosten" :value="fc(data.wv.inkoop)" :highlight="true" />
        <ReportRow label="Totaal inkoopkosten" :value="fc(data.wv.inkoop)" :bold="true" :subtotal="true" />

        <div class="h-4"></div>
        <ReportRow label="Overige bedrijfskosten" :value="fc(data.wv.overigeKostenTotaal)" :highlight="true" />
        <ReportRow label="Auto- en transportkosten" :value="fc(data.wv.autokosten)" />
        <ReportRow label="Huisvestingskosten" :value="fc(data.wv.huisvesting)" />
        <ReportRow label="Verkoopkosten" :value="fc(data.wv.verkoop)" />
        <ReportRow label="Andere kosten" :value="fc(data.wv.andereKosten)" />
        <ReportRow label="Totaal overige bedrijfskosten" :value="fc(data.wv.overigeKostenTotaal)" :bold="true" :subtotal="true" />

        <div class="h-4"></div>
        <ReportRow label="Subtotaal" :value="fc(data.wv.opbrengsten - data.wv.inkoop - data.wv.overigeKostenTotaal)" :bold="true" :highlight="true" />

        <div class="h-4"></div>
        <ReportRow label="Financiele baten en lasten" :value="fc(data.wv.financieel)" :highlight="true" />
        <ReportRow label="Totaal financiele baten en lasten" :value="fc(data.wv.financieel)" :subtotal="true" />

        <div class="h-4"></div>
        <ReportRow label="Saldo winst-en-verliesrekening" :value="fc(saldoWV)" :bold="true" :highlight="true" />
      </ReportSection>

      <!-- Balans Activa -->
      <ReportSection :title="'Balans: activa ' + data.onderneming.naam" :color="sectionColor">
        <ReportRow label="Vorderingen" :value="fc(data.balans.vorderingen)" :highlight="true" />
        <div class="px-8 py-1 flex justify-between text-xs text-slate-500">
          <span></span>
          <div class="flex gap-12"><span class="font-semibold">Nominale waarde</span><span class="font-semibold">Boekwaarde einde boekjaar</span></div>
        </div>
        <ReportRow label="Vordering omzetbelasting" :value="fc(data.balans.vorderingOB)" />
        <ReportRow label="Vorderingen op handelsdebiteuren" :value="fc(data.balans.debiteuren)" />
        <ReportRow label="Totaal vorderingen" :value="fc(data.balans.vorderingen)" :subtotal="true" />

        <div class="h-4"></div>
        <ReportRow label="Liquide middelen" :value="fc(data.balans.liquide)" :highlight="true" />
        <ReportRow label="Totaal activa" :value="fc(data.balans.totaalActiva)" :bold="true" :subtotal="true" />
      </ReportSection>

      <!-- Balans Passiva -->
      <ReportSection :title="'Balans: passiva ' + data.onderneming.naam" :color="sectionColor">
        <div class="px-8 py-1 flex justify-between text-xs text-slate-500">
          <span></span>
          <div class="flex gap-8"><span class="font-semibold">Boekwaarde begin boekjaar</span><span class="font-semibold">Boekwaarde einde boekjaar</span></div>
        </div>
        <ReportRow label="Eigen vermogen" :value="fc(data.balans.eigenVermogenEind)" />
        <ReportRow label="Totaal ondernemingsvermogen" :value="fc(data.balans.eigenVermogenEind)" :subtotal="true" />

        <div class="h-4"></div>
        <ReportRow label="Kortlopende schulden" :value="fc(data.balans.schulden)" :highlight="true" />
        <ReportRow label="Schulden aan leveranciers en handelskredieten" :value="fc(data.balans.leveranciers)" />
        <ReportRow label="Overige kortlopende schulden" :value="fc(data.balans.overigeSchulden)" />
        <ReportRow label="Totaal kortlopende schulden" :value="fc(data.balans.schulden)" :subtotal="true" />

        <div class="h-4"></div>
        <ReportRow label="Totaal passiva" :value="fc(data.balans.totaalPassiva)" :bold="true" :subtotal="true" />
      </ReportSection>

      <!-- Fiscale winstberekening -->
      <ReportSection title="Fiscalewinstberekening" :color="sectionColor">
        <ReportRow label="Ondernemingsvermogen einde boekjaar" :value="fc(data.balans.eigenVermogenEind)" />
        <ReportRow label="Ondernemingsvermogen begin boekjaar" :value="fc(data.balans.eigenVermogenBegin)" />
        <ReportRow label="Saldo ondernemingsvermogen" :value="fc(data.balans.eigenVermogenEind - data.balans.eigenVermogenBegin)" />
        <div class="h-2"></div>
        <ReportRow label="Priveonttrekkingen" :value="fc(data.fiscaal.priveOnttrekkingen)" />
        <ReportRow label="Winstberekening" :value="fc(saldoWV)" :bold="true" :subtotal="true" />
        <div class="h-2"></div>
        <ReportRow label="Niet-aftrekbare kosten en lasten" :value="fc(data.fiscaal.nietAftrekbaar)" />
        <ReportRow label="Fiscalewinstberekening" :value="fc(fiscaleWinst)" :bold="true" :highlight="true" />
      </ReportSection>

      <!-- Ondernemersaftrek -->
      <ReportSection title="Ondernemersaftrek" :color="sectionColor">
        <ReportRow label="Zelfstandigenaftrek" :value="fc(data.aftrek.zelfstandigen)" />
        <ReportRow label="Totaal ondernemersaftrek" :value="fc(data.aftrek.zelfstandigen)" :bold="true" :subtotal="true" />
      </ReportSection>

      <!-- Inkomstenbelasting berekening -->
      <ReportSection title="Inkomstenbelasting" subtitle="Berekening inkomstenbelasting en premie volksverzekeringen" :color="sectionColor">
        <ReportRow label="Te betalen" :value="fc(data.belasting.teBetalen)" :bold="true" :highlight="true" />

        <div class="h-4"></div>
        <div class="px-8 py-2 text-sm font-semibold text-slate-700">Inkomen</div>
        <ReportRow label="Box 1: werk en woning" :value="fc(data.belasting.box1)" />
        <ReportRow label="Winst uit onderneming" :value="fc(fiscaleWinst)" />
        <ReportRow label="Belastbare winst uit onderneming" :value="fc(data.belasting.belastbareWinst)" :bold="true" :subtotal="true" />

        <div class="h-4"></div>
        <div class="px-8 py-2 text-sm font-semibold text-slate-700">Inkomsten uit werk</div>
        <ReportRow v-for="w in data.werkgevers" :key="w.naam" :label="'Loon in Nederland - ' + w.naam" :value="fc(w.loon)" />
        <ReportRow label="Totaal inkomsten uit werk" :value="fc(totaalLoon)" :bold="true" :subtotal="true" />

        <div class="h-4"></div>
        <ReportRow label="Totaal box 1: werk en woning" :value="fc(data.belasting.box1)" :bold="true" :highlight="true" />
        <ReportRow label="Verzamelinkomen" :value="fc(data.belasting.box1)" :bold="true" />

        <div class="h-4"></div>
        <div class="px-8 py-2 text-sm font-semibold text-slate-700">Berekening belasting en premie</div>
        <ReportRow label="Inkomstenbelasting" :value="fc(data.belasting.ib)" />
        <ReportRow label="1e schijf: 8,17% van € 38.441" :value="fc(data.belasting.schijf1)" />
        <ReportRow label="2e schijf: 37,48%" :value="fc(data.belasting.schijf2)" />
        <ReportRow label="Totaal inkomstenbelasting" :value="fc(data.belasting.ib)" :bold="true" :subtotal="true" />

        <div class="h-4"></div>
        <ReportRow label="Premie volksverzekeringen" :value="fc(data.belasting.premie)" />
        <ReportRow label="Premie AOW: 17,9% van € 38.441" :value="fc(data.belasting.aow)" />
        <ReportRow label="Premie Anw: 0,1% van € 38.441" :value="fc(data.belasting.anw)" />
        <ReportRow label="Premie Wlz: 9,65% van € 38.441" :value="fc(data.belasting.wlz)" />
        <ReportRow label="Premie volksverzekeringen" :value="fc(data.belasting.premie)" :bold="true" :subtotal="true" />

        <div class="h-6"></div>
        <div class="px-8 py-2 text-sm font-semibold text-slate-700">Bijdrage Zorgverzekeringswet</div>
        <ReportRow label="Te betalen bijdrage Zorgverzekeringswet" :value="fc(data.belasting.zvw)" />
        <div class="h-4"></div>
        <ReportRow label="Totaal te betalen" :value="fc(data.belasting.teBetalen)" :bold="true" :highlight="true" />
      </ReportSection>

      <!-- Paginanummering -->
      <div class="px-8 py-4 text-right text-xs text-slate-400">
        Gegenereerd door FiscalFlow AI | Pagina 1 van 1
      </div>
    </div>

    <!-- Goedkeuring modal -->
    <div v-if="showApproveModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showApproveModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Aangifte ter goedkeuring sturen</h2>
        <p class="text-sm text-slate-600 mb-4">De concept aangifte wordt naar de klant gestuurd ter review. Na goedkeuring kan deze worden ingediend bij de Belastingdienst.</p>
        <div class="space-y-3">
          <div><label class="block text-sm font-medium text-slate-700 mb-1">E-mail klant</label><input type="email" v-model="data.email" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Bericht (optioneel)</label><textarea rows="3" placeholder="Eventuele toelichting..." class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"></textarea></div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showApproveModal = false" class="px-4 py-2 text-sm font-medium text-slate-700">Annuleren</button>
          <button @click="sendForApproval" class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700">Verstuur ter goedkeuring</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const selectedYear = ref('2025')
const status = ref<'concept' | 'goedkeuring' | 'ingediend'>('concept')
const showApproveModal = ref(false)
const reportRef = ref<HTMLElement>()
const sectionColor = 'text-sky-600'
const today = new Date().toLocaleDateString('nl-NL')

const data = reactive({
  naam: 'J. de Vries',
  bsn: '123456789',
  geboortedatum: '15-06-1985',
  telefoon: '0612345678',
  consultentNr: '731614',
  email: 'jan@devries-digital.nl',
  partner: false,
  onderneming: {
    naam: 'De Vries Digital BV',
    activiteiten: 'communicatie- en grafisch ontwerp',
    vorm: 'Eenmanszaak',
  },
  wv: {
    opbrengsten: 142500,
    inkoop: 12400,
    overigeKostenTotaal: 32780,
    autokosten: 3600,
    huisvesting: 14400,
    verkoop: 2800,
    andereKosten: 11980,
    financieel: -263,
  },
  balans: {
    vorderingen: 12450,
    vorderingOB: 2221,
    debiteuren: 10229,
    liquide: 24650,
    totaalActiva: 37100,
    eigenVermogenBegin: 18000,
    eigenVermogenEind: 26200,
    schulden: 10900,
    leveranciers: 5850,
    overigeSchulden: 5050,
    totaalPassiva: 37100,
  },
  fiscaal: {
    priveOnttrekkingen: 44404,
    nietAftrekbaar: 211,
  },
  aftrek: {
    zelfstandigen: 2470,
  },
  werkgevers: [] as Array<{ naam: string; loon: number; loonheffing: number; arbeidskorting: number }>,
  belasting: {
    teBetalen: 11837,
    box1: 72500,
    belastbareWinst: 28930,
    ib: 16188,
    schijf1: 3140,
    schijf2: 12765,
    premie: 10628,
    aow: 6880,
    anw: 38,
    wlz: 3709,
    zvw: 1521,
  },
})

const saldoWV = computed(() => data.wv.opbrengsten - data.wv.inkoop - data.wv.overigeKostenTotaal + data.wv.financieel)
const fiscaleWinst = computed(() => saldoWV.value + data.fiscaal.nietAftrekbaar)
const totaalLoon = computed(() => data.werkgevers.reduce((s, w) => s + w.loon, 0))

function fc(v: number): string {
  const prefix = v < 0 ? '€ -' : '€ '
  return prefix + Math.abs(v).toLocaleString('nl-NL')
}

const { generating, generateFromTemplate } = usePdf()

async function printReport() {
  const { aangifteIBTemplate } = await import('~/composables/usePdfTemplates')
  const html = aangifteIBTemplate(data, selectedYear.value)
  await generateFromTemplate(html, `Aangifte-IB-${selectedYear.value}-${data.naam.replace(/\s/g, '_')}.pdf`)
}

function sendForApproval() {
  status.value = 'goedkeuring'
  showApproveModal.value = false
}

// Report sub-components
const ReportSection = defineComponent({
  props: { title: String, subtitle: String, color: String },
  setup(props, { slots }) {
    return () => h('div', { class: 'border-b border-surface-200' }, [
      h('div', { class: 'px-8 pt-8 pb-2' }, [
        h('h3', { class: 'text-xl font-bold text-slate-900' }, props.title),
        props.subtitle ? h('p', { class: [props.color || 'text-sky-600', 'text-sm mt-1'] }, props.subtitle) : null,
      ]),
      h('div', { class: 'pb-6' }, slots.default?.()),
    ])
  },
})

const ReportRow = defineComponent({
  props: { label: String, value: String, bold: Boolean, highlight: Boolean, subtotal: Boolean },
  setup(props) {
    return () => h('div', {
      class: ['px-8 py-2 flex justify-between items-center text-sm', props.highlight ? 'bg-sky-50' : '', props.subtotal ? 'border-t border-surface-200 mt-1' : ''],
    }, [
      h('span', { class: [props.bold ? 'font-semibold text-slate-900' : 'text-slate-700'] }, props.label),
      h('span', { class: [props.bold ? 'font-bold text-slate-900' : 'font-medium text-slate-900'] }, props.value),
    ])
  },
})
</script>

<style>
@media print {
  aside, header, .no-print { display: none !important; }
  main { padding: 0 !important; }
  .bg-white { box-shadow: none !important; border: none !important; }
}
</style>

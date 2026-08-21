<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import {
  Music,
  Search,
  Edit3,
  Loader2,
  Disc,
  FileAudio,
  Clock,
  Sparkles,
  Image as ImageIcon,
  CheckCircle2,
  AlertCircle,
  Upload,
  CheckSquare,
  Square,
  Layers,
  X,
} from 'lucide-vue-next';
import { api } from '../api/client';
import type { Track } from '../types';
import TagEditorModal from '../components/TagEditorModal.vue';
import OnlineCoverSearchModal from '../components/OnlineCoverSearchModal.vue';
import BatchCoverModal from '../components/BatchCoverModal.vue';

const tracks = ref<Track[]>([]);
const totalTracks = ref(0);
const totalPages = ref(1);
const currentPage = ref(1);
const isLoading = ref(true);
const search = ref('');
const activeFilter = ref<'all' | 'no_cover' | 'has_cover'>('all');

const counts = ref({
  total: 0,
  has_cover: 0,
  no_cover: 0,
});

// Selection & Modals
const selectedTrackIds = ref<number[]>([]);
const isBatchModalOpen = ref(false);
const selectedTrackForTags = ref<Track | null>(null);
const selectedTrackForCover = ref<Track | null>(null);
let searchTimeout: any = null;

// Computed for batch tracks
const selectedTracksList = computed(() => {
  return tracks.value.filter((t) => selectedTrackIds.value.includes(t.id));
});

const isAllVisibleSelected = computed(() => {
  if (tracks.value.length === 0) return false;
  return tracks.value.every((t) => selectedTrackIds.value.includes(t.id));
});

const isSomeVisibleSelected = computed(() => {
  return tracks.value.some((t) => selectedTrackIds.value.includes(t.id)) && !isAllVisibleSelected.value;
});

function toggleSelectAllVisible() {
  if (isAllVisibleSelected.value) {
    // Deselect visible tracks
    const visibleIds = new Set(tracks.value.map((t) => t.id));
    selectedTrackIds.value = selectedTrackIds.value.filter((id) => !visibleIds.has(id));
  } else {
    // Select all visible tracks
    const newSet = new Set(selectedTrackIds.value);
    for (const t of tracks.value) {
      newSet.add(t.id);
    }
    selectedTrackIds.value = Array.from(newSet);
  }
}

function toggleTrackSelect(id: number) {
  const idx = selectedTrackIds.value.indexOf(id);
  if (idx > -1) {
    selectedTrackIds.value.splice(idx, 1);
  } else {
    selectedTrackIds.value.push(id);
  }
}

function clearSelection() {
  selectedTrackIds.value = [];
}

async function loadTracks() {
  isLoading.value = true;
  try {
    const data = await api.getTracks({
      q: search.value.trim(),
      filter: activeFilter.value,
      page: currentPage.value,
      limit: 30,
    });
    tracks.value = data.tracks;
    totalTracks.value = data.total;
    totalPages.value = data.total_pages;
    if (data.counts) {
      counts.value = data.counts;
    }
  } catch (err) {
    console.error('Erro ao carregar faixas:', err);
  } finally {
    isLoading.value = false;
  }
}

function onSearchInput() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    currentPage.value = 1;
    loadTracks();
  }, 300);
}

function setFilter(filter: 'all' | 'no_cover' | 'has_cover') {
  activeFilter.value = filter;
  currentPage.value = 1;
  loadTracks();
}

function formatDuration(seconds: number): string {
  if (!seconds) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatYear(val: number | string | undefined | null): string {
  if (!val) return '-';
  const num = typeof val === 'number' ? val : parseInt(val.toString(), 10);
  if (isNaN(num)) return val.toString().slice(0, 4);
  if (num > 100000) {
    try {
      return new Date(num * 1000).getUTCFullYear().toString();
    } catch {
      return num.toString();
    }
  }
  return num.toString();
}

function getArtistDisplay(track: Track): string {
  if (Array.isArray(track.artists)) {
    return track.artists.map((a) => (typeof a === 'object' ? a.name : a)).join(', ');
  }
  if (typeof track.artists === 'string') {
    return track.artists;
  }
  return 'Artista Desconhecido';
}

function handleTagsUpdated() {
  loadTracks();
}

function handleCoverApplied() {
  loadTracks();
}

function handleBatchApplied() {
  clearSelection();
  loadTracks();
}

watch(currentPage, () => {
  loadTracks();
});

onMounted(() => {
  loadTracks();
});
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-b from-surface-elevated/70 to-surface rounded-3xl p-6 sm:p-8 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center space-x-2 text-accent text-sm font-medium mb-1">
          <FileAudio class="w-4 h-4" />
          <span>Editor de Metadados & Capas</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Faixas & Capas de Álbuns
        </h1>
        <p class="text-sm text-gray-400 mt-1">
          Gerencie capas (upload, URL direta ou busca online) e edite tags ID3 diretamente nos arquivos.
        </p>
      </div>

      <div class="flex items-center space-x-2 text-xs bg-black/40 px-4 py-2.5 rounded-2xl border border-white/5">
        <span class="text-gray-400">Total indexado:</span>
        <span class="font-bold text-white text-sm">{{ counts.total }}</span>
        <span class="text-gray-500">•</span>
        <span class="text-gray-400">Pág. {{ currentPage }} de {{ totalPages }}</span>
      </div>
    </div>

    <!-- Filters, Search & Batch Actions Bar -->
    <div class="bg-surface rounded-2xl p-4 border border-white/5 space-y-4">
      <!-- Filter Tabs & Batch Trigger -->
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center space-x-2">
          <button
            @click="setFilter('all')"
            class="px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5"
            :class="activeFilter === 'all' ? 'bg-white text-black shadow-md' : 'bg-surface-elevated text-gray-400 hover:text-white'"
          >
            <span>Todas as Faixas</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="activeFilter === 'all' ? 'bg-black/20 text-black' : 'bg-white/10 text-gray-400'">
              {{ counts.total }}
            </span>
          </button>

          <button
            @click="setFilter('no_cover')"
            class="px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5"
            :class="activeFilter === 'no_cover' ? 'bg-amber-500 text-black shadow-md' : 'bg-surface-elevated text-amber-400 hover:text-amber-300'"
          >
            <AlertCircle class="w-3.5 h-3.5" />
            <span>Sem Capa</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="activeFilter === 'no_cover' ? 'bg-black/20 text-black' : 'bg-amber-500/20 text-amber-300'">
              {{ counts.no_cover }}
            </span>
          </button>

          <button
            @click="setFilter('has_cover')"
            class="px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5"
            :class="activeFilter === 'has_cover' ? 'bg-emerald-500 text-black shadow-md' : 'bg-surface-elevated text-emerald-400 hover:text-emerald-300'"
          >
            <CheckCircle2 class="w-3.5 h-3.5" />
            <span>Com Capa</span>
            <span class="text-[10px] px-1.5 py-0.5 rounded-full" :class="activeFilter === 'has_cover' ? 'bg-black/20 text-black' : 'bg-emerald-500/20 text-emerald-300'">
              {{ counts.has_cover }}
            </span>
          </button>
        </div>

        <div class="flex items-center space-x-3">
          <div class="text-xs text-gray-400">
            Mostrando <span class="text-white font-medium">{{ totalTracks }}</span> resultado(s)
          </div>
        </div>
      </div>

      <!-- Batch Selection Floating / Contextual Bar -->
      <div
        v-if="selectedTrackIds.length > 0"
        class="p-3 bg-accent/10 border border-accent/30 rounded-2xl flex flex-wrap items-center justify-between gap-3 animate-fade-in"
      >
        <div class="flex items-center space-x-2.5">
          <div class="p-1.5 bg-accent text-black rounded-lg">
            <CheckSquare class="w-4 h-4" />
          </div>
          <span class="text-sm font-bold text-white">
            {{ selectedTrackIds.length }} {{ selectedTrackIds.length === 1 ? 'faixa selecionada' : 'faixas selecionadas' }}
          </span>
        </div>

        <div class="flex items-center space-x-2">
          <button
            @click="isBatchModalOpen = true"
            class="px-4 py-2 bg-accent text-black font-bold text-xs rounded-xl shadow-lg shadow-accent/20 hover:bg-accent/90 transition-all flex items-center space-x-2"
          >
            <ImageIcon class="w-4 h-4" />
            <span>Capa em Lote</span>
          </button>

          <button
            @click="clearSelection"
            class="px-3 py-2 bg-surface-elevated hover:bg-white/10 text-gray-300 hover:text-white rounded-xl text-xs font-semibold border border-white/10 transition-colors flex items-center space-x-1"
          >
            <X class="w-3.5 h-3.5" />
            <span>Limpar Seleção</span>
          </button>
        </div>
      </div>

      <!-- Search Input -->
      <div class="relative">
        <Search class="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          v-model="search"
          type="text"
          placeholder="Pesquisar por título de música, álbum ou artista..."
          class="w-full bg-surface-elevated border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent"
          @input="onSearchInput"
        />
      </div>
    </div>

    <!-- Tracks Table -->
    <div class="bg-surface rounded-3xl border border-white/5 overflow-hidden shadow-sm">
      <div v-if="isLoading" class="py-24 flex flex-col items-center justify-center space-y-3 text-gray-400">
        <Loader2 class="w-8 h-8 animate-spin text-accent" />
        <p class="text-sm">Carregando faixas da biblioteca...</p>
      </div>

      <div v-else-if="tracks.length > 0" class="overflow-x-auto">
        <table class="w-full text-left text-sm text-gray-300">
          <thead class="text-xs uppercase bg-surface-elevated text-gray-400 border-b border-white/5">
            <tr>
              <!-- Master Checkbox -->
              <th class="px-4 py-3.5 w-10 text-center">
                <input
                  type="checkbox"
                  :checked="isAllVisibleSelected"
                  :indeterminate.prop="isSomeVisibleSelected"
                  @change="toggleSelectAllVisible"
                  class="w-4 h-4 rounded text-accent focus:ring-accent border-white/20 bg-surface cursor-pointer"
                  title="Selecionar todas da página"
                />
              </th>
              <th class="px-4 py-3.5">Capa</th>
              <th class="px-5 py-3.5">Título</th>
              <th class="px-5 py-3.5">Artista</th>
              <th class="px-5 py-3.5">Álbum</th>
              <th class="px-5 py-3.5">Ano</th>
              <th class="px-5 py-3.5"><Clock class="w-3.5 h-3.5" /></th>
              <th class="px-5 py-3.5 text-right">Ações</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr
              v-for="track in tracks"
              :key="track.id"
              class="hover:bg-white/5 transition-colors group cursor-pointer"
              :class="selectedTrackIds.includes(track.id) ? 'bg-accent/5' : ''"
              @click="toggleTrackSelect(track.id)"
            >
              <!-- Row Checkbox -->
              <td class="px-4 py-3.5 text-center" @click.stop>
                <input
                  type="checkbox"
                  :checked="selectedTrackIds.includes(track.id)"
                  @change="toggleTrackSelect(track.id)"
                  class="w-4 h-4 rounded text-accent focus:ring-accent border-white/20 bg-surface cursor-pointer"
                />
              </td>

              <!-- Cover Column -->
              <td class="px-4 py-3.5" @click.stop>
                <div
                  @click="selectedTrackForCover = track"
                  class="w-10 h-10 rounded-lg overflow-hidden bg-surface-elevated relative cursor-pointer border border-white/10 group-hover:border-accent/40 transition-all flex-shrink-0 flex items-center justify-center shadow-inner"
                  title="Clique para gerenciar a capa deste álbum"
                >
                  <img
                    v-if="track.has_cover && track.cover_url"
                    :src="track.cover_url"
                    :alt="track.album"
                    class="w-full h-full object-cover"
                    loading="lazy"
                  />
                  <div v-else class="text-amber-400 flex flex-col items-center justify-center">
                    <Disc class="w-5 h-5 opacity-70" />
                  </div>
                  <!-- Hover Overlay -->
                  <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-accent">
                    <Sparkles class="w-4 h-4" />
                  </div>
                </div>
              </td>

              <!-- Title -->
              <td class="px-5 py-3.5 font-medium text-white">
                <div class="flex items-center space-x-2.5">
                  <span class="truncate max-w-xs font-semibold">{{ track.title }}</span>
                  <span
                    v-if="!track.has_cover"
                    class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium flex-shrink-0"
                  >
                    Sem Capa
                  </span>
                </div>
              </td>

              <!-- Artist -->
              <td class="px-5 py-3.5 text-gray-300 truncate max-w-xs">
                {{ getArtistDisplay(track) }}
              </td>

              <!-- Album -->
              <td class="px-5 py-3.5 text-gray-400 truncate max-w-xs">
                {{ track.album || 'Sem Álbum' }}
              </td>

              <!-- Year -->
              <td class="px-5 py-3.5 text-gray-400">
                {{ formatYear(track.date) }}
              </td>

              <!-- Duration -->
              <td class="px-5 py-3.5 text-gray-400">
                {{ formatDuration(track.duration) }}
              </td>

              <!-- Actions -->
              <td class="px-5 py-3.5 text-right" @click.stop>
                <div class="flex items-center justify-end space-x-1.5">
                  <!-- Manage Cover Button -->
                  <button
                    @click="selectedTrackForCover = track"
                    class="px-2.5 py-1.5 bg-white/5 hover:bg-accent/20 hover:text-accent border border-white/10 rounded-lg text-xs font-medium transition-all inline-flex items-center space-x-1"
                    title="Buscar capa online ou fazer upload"
                  >
                    <Sparkles class="w-3.5 h-3.5 text-accent" />
                    <span>Capa</span>
                  </button>

                  <!-- Edit Tags Button -->
                  <button
                    @click="selectedTrackForTags = track"
                    class="px-2.5 py-1.5 bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 rounded-lg text-xs font-medium transition-all inline-flex items-center space-x-1"
                    title="Editar tags ID3 diretamente no arquivo"
                  >
                    <Edit3 class="w-3.5 h-3.5" />
                    <span>Tags</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty State -->
      <div v-else class="py-16 text-center text-gray-500 space-y-2">
        <Music class="w-10 h-10 mx-auto text-gray-600" />
        <p class="text-sm">Nenhuma música encontrada com os filtros atuais.</p>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between px-2 pt-2">
      <button
        @click="currentPage = Math.max(1, currentPage - 1)"
        :disabled="currentPage === 1 || isLoading"
        class="px-4 py-2 bg-surface-elevated hover:bg-surface-hover text-sm font-medium rounded-xl text-white disabled:opacity-30 transition-all border border-white/5"
      >
        Anterior
      </button>

      <span class="text-xs text-gray-400">Página {{ currentPage }} de {{ totalPages }}</span>

      <button
        @click="currentPage = Math.min(totalPages, currentPage + 1)"
        :disabled="currentPage === totalPages || isLoading"
        class="px-4 py-2 bg-surface-elevated hover:bg-surface-hover text-sm font-medium rounded-xl text-white disabled:opacity-30 transition-all border border-white/5"
      >
        Próxima
      </button>
    </div>

    <!-- Tag Editor Modal -->
    <TagEditorModal
      v-if="selectedTrackForTags"
      :track="selectedTrackForTags"
      @close="selectedTrackForTags = null"
      @updated="handleTagsUpdated"
    />

    <!-- Single Track Online Cover Search & Upload Modal -->
    <OnlineCoverSearchModal
      v-if="selectedTrackForCover"
      :track="selectedTrackForCover"
      @close="selectedTrackForCover = null"
      @applied="handleCoverApplied"
    />

    <!-- Batch Cover Modal -->
    <BatchCoverModal
      v-if="isBatchModalOpen && selectedTracksList.length > 0"
      :selected-tracks="selectedTracksList"
      @close="isBatchModalOpen = false"
      @applied="handleBatchApplied"
    />
  </div>
</template>

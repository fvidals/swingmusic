<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { Music, Search, Edit3, Loader2, Disc, FileAudio, Clock } from 'lucide-vue-next';
import { api } from '../api/client';
import type { Track } from '../types';
import TagEditorModal from '../components/TagEditorModal.vue';

const tracks = ref<Track[]>([]);
const totalTracks = ref(0);
const totalPages = ref(1);
const currentPage = ref(1);
const isLoading = ref(true);
const search = ref('');

const selectedTrack = ref<Track | null>(null);
let searchTimeout: any = null;

async function loadTracks() {
  isLoading.value = true;
  try {
    const data = await api.getTracks({
      q: search.value.trim(),
      page: currentPage.value,
      limit: 30,
    });
    tracks.value = data.tracks;
    totalTracks.value = data.total;
    totalPages.value = data.total_pages;
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

function formatDuration(seconds: number): string {
  if (!seconds) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function getArtistDisplay(track: Track): string {
  if (Array.isArray(track.artists)) {
    return track.artists.map(a => typeof a === 'object' ? a.name : a).join(', ');
  }
  return 'Artista Desconhecido';
}

function handleTagsUpdated() {
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
    <!-- Header -->
    <div class="bg-gradient-to-b from-surface-elevated/70 to-surface rounded-3xl p-6 sm:p-8 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center space-x-2 text-accent text-sm font-medium mb-1">
          <FileAudio class="w-4 h-4" />
          <span>Editor de Tags de Áudio</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Gerenciador de Tags ID3
        </h1>
        <p class="text-sm text-gray-400 mt-1">
          Edite metadados (Título, Artista, Álbum, Ano, Gênero) diretamente nos arquivos MP3, FLAC, M4A e OGG.
        </p>
      </div>

      <div class="flex items-center space-x-2 text-xs bg-black/40 px-4 py-2.5 rounded-2xl border border-white/5">
        <span class="text-gray-400">Total indexado:</span>
        <span class="font-bold text-white text-sm">{{ totalTracks }}</span>
        <span class="text-gray-500">•</span>
        <span class="text-gray-400">Pág. {{ currentPage }} de {{ totalPages }}</span>
      </div>
    </div>

    <!-- Search bar -->
    <div class="bg-surface rounded-2xl p-4 border border-white/5">
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
    <div class="bg-surface rounded-3xl border border-white/5 overflow-hidden">
      <div v-if="isLoading" class="py-24 flex flex-col items-center justify-center space-y-3 text-gray-400">
        <Loader2 class="w-8 h-8 animate-spin text-accent" />
        <p class="text-sm">Carregando faixas da biblioteca...</p>
      </div>

      <div v-else-if="tracks.length > 0" class="overflow-x-auto">
        <table class="w-full text-left text-sm text-gray-300">
          <thead class="text-xs uppercase bg-surface-elevated text-gray-400 border-b border-white/5">
            <tr>
              <th class="px-5 py-3.5">Título</th>
              <th class="px-5 py-3.5">Artista</th>
              <th class="px-5 py-3.5">Álbum</th>
              <th class="px-5 py-3.5">Ano</th>
              <th class="px-5 py-3.5"><Clock class="w-3.5 h-3.5" /></th>
              <th class="px-5 py-3.5 text-right">Ação</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-white/5">
            <tr
              v-for="track in tracks"
              :key="track.id"
              class="hover:bg-white/5 transition-colors group"
            >
              <td class="px-5 py-3.5 font-medium text-white">
                <div class="flex items-center space-x-2.5">
                  <div class="w-8 h-8 rounded-lg bg-surface-elevated flex items-center justify-center flex-shrink-0 text-gray-500">
                    <Music class="w-4 h-4" />
                  </div>
                  <span class="truncate max-w-xs">{{ track.title }}</span>
                </div>
              </td>
              <td class="px-5 py-3.5 text-gray-300 truncate max-w-xs">
                {{ getArtistDisplay(track) }}
              </td>
              <td class="px-5 py-3.5 text-gray-400 truncate max-w-xs">
                {{ track.album }}
              </td>
              <td class="px-5 py-3.5 text-gray-400">
                {{ track.date || '-' }}
              </td>
              <td class="px-5 py-3.5 text-gray-400">
                {{ formatDuration(track.duration) }}
              </td>
              <td class="px-5 py-3.5 text-right">
                <button
                  @click="selectedTrack = track"
                  class="px-3.5 py-1.5 bg-white/5 hover:bg-accent hover:text-black rounded-lg text-xs font-semibold transition-all inline-flex items-center space-x-1.5"
                >
                  <Edit3 class="w-3.5 h-3.5" />
                  <span>Editar Tags</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="py-16 text-center text-gray-500">
        Nenhuma música encontrada com os filtros atuais.
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-center space-x-2 pt-2">
      <button
        @click="currentPage = Math.max(1, currentPage - 1)"
        :disabled="currentPage === 1 || isLoading"
        class="px-4 py-2 bg-surface-elevated hover:bg-surface-hover text-sm font-medium rounded-xl text-white disabled:opacity-30 transition-all"
      >
        Anterior
      </button>

      <span class="text-xs text-gray-400 px-2">Página {{ currentPage }} de {{ totalPages }}</span>

      <button
        @click="currentPage = Math.min(totalPages, currentPage + 1)"
        :disabled="currentPage === totalPages || isLoading"
        class="px-4 py-2 bg-surface-elevated hover:bg-surface-hover text-sm font-medium rounded-xl text-white disabled:opacity-30 transition-all"
      >
        Próxima
      </button>
    </div>

    <!-- Tag Editor Modal -->
    <TagEditorModal
      v-if="selectedTrack"
      :track="selectedTrack"
      @close="selectedTrack = null"
      @updated="handleTagsUpdated"
    />
  </div>
</template>

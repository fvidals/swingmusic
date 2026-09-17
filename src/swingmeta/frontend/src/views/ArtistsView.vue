<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { Search, Filter, ArrowUpDown, Loader2, Users, AlertCircle, CheckCircle2, FileText, FolderSync } from 'lucide-vue-next';
import { api } from '../api/client';
import type { Artist } from '../types';
import ArtistCard from '../components/ArtistCard.vue';

const router = useRouter();

const artists = ref<Artist[]>([]);
const totalArtists = ref(0);
const totalPages = ref(1);
const currentPage = ref(1);
const isLoading = ref(true);

const search = ref('');
const currentFilter = ref('all'); // all, missing_image, has_image, missing_bio
const sortBy = ref('name'); // name, track_count, album_count
const sortOrder = ref('asc'); // asc, desc

let searchTimeout: any = null;

const isExporting = ref(false);
const exportFeedback = ref('');
const exportError = ref('');

async function exportSharedArtistArt() {
  isExporting.value = true;
  exportFeedback.value = '';
  exportError.value = '';
  try {
    const res = await api.exportSharedArtistArt();
    exportFeedback.value = `${res.exported} de ${res.total} artistas exportados para a pasta compartilhada.`;
    setTimeout(() => { exportFeedback.value = ''; }, 5000);
  } catch (err: any) {
    exportError.value = err.message || 'Erro ao exportar artes para a pasta compartilhada.';
  } finally {
    isExporting.value = false;
  }
}

async function loadArtists() {
  isLoading.value = true;
  try {
    const data = await api.getArtists({
      q: search.value.trim(),
      filter: currentFilter.value,
      sort: sortBy.value,
      order: sortOrder.value,
      page: currentPage.value,
      limit: 36,
    });
    artists.value = data.artists;
    totalArtists.value = data.total;
    totalPages.value = data.total_pages;
  } catch (err) {
    console.error('Erro ao carregar artistas:', err);
  } finally {
    isLoading.value = false;
  }
}

function onSearchInput() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    currentPage.value = 1;
    loadArtists();
  }, 300);
}

function selectArtist(artist: Artist) {
  router.push({ name: 'artist-detail', params: { artisthash: artist.artisthash } });
}

watch([currentFilter, sortBy, sortOrder, currentPage], () => {
  loadArtists();
});

onMounted(() => {
  loadArtists();
});
</script>

<template>
  <div class="space-y-6">
    <!-- Hero Header -->
    <div class="bg-gradient-to-b from-surface-elevated/70 to-surface rounded-3xl p-6 sm:p-8 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center space-x-2 text-accent text-sm font-medium mb-1">
          <Users class="w-4 h-4" />
          <span>Biblioteca de Artistas</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Gerenciador de Artistas
        </h1>
        <p class="text-sm text-gray-400 mt-1">
          Edite fotos em alta resolução, adicione biografias e consulte fontes online (Deezer, Spotify, MusicBrainz).
        </p>
      </div>

      <div class="flex flex-col items-end space-y-2">
        <!-- Quick stats pill -->
        <div class="flex items-center space-x-2 text-xs bg-black/40 px-4 py-2.5 rounded-2xl border border-white/5">
          <span class="text-gray-400">Total listado:</span>
          <span class="font-bold text-white text-sm">{{ totalArtists }}</span>
          <span class="text-gray-500">•</span>
          <span class="text-gray-400">Página {{ currentPage }} de {{ totalPages }}</span>
        </div>

        <button
          @click="exportSharedArtistArt"
          :disabled="isExporting"
          class="px-3.5 py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-semibold rounded-xl border border-white/10 flex items-center space-x-2 transition-all disabled:opacity-50"
          title="Exporta as fotos de artistas já salvas no SwingMusic (maior qualidade disponível) para a pasta compartilhada (/shared/artist-art), consumida por outros servidores de mídia como o Navidrome"
        >
          <Loader2 v-if="isExporting" class="w-3.5 h-3.5 animate-spin" />
          <FolderSync v-else class="w-3.5 h-3.5" />
          <span>Exportar Artes para Pasta Compartilhada</span>
        </button>
      </div>
    </div>

    <div v-if="exportFeedback" class="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-2xl text-xs flex items-center space-x-2 shadow-lg">
      <CheckCircle2 class="w-4 h-4 text-emerald-400 flex-shrink-0" />
      <span>{{ exportFeedback }}</span>
    </div>

    <div v-if="exportError" class="p-4 bg-red-500/10 border border-red-500/20 text-red-300 rounded-2xl text-xs">
      {{ exportError }}
    </div>

    <!-- Filter & Search Bar -->
    <div class="bg-surface rounded-2xl p-4 border border-white/5 flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
      <!-- Search Input -->
      <div class="relative flex-1">
        <Search class="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          v-model="search"
          type="text"
          placeholder="Buscar artista por nome..."
          class="w-full bg-surface-elevated border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent transition-colors"
          @input="onSearchInput"
        />
      </div>

      <!-- Filters & Sorting -->
      <div class="flex flex-wrap items-center gap-2">
        <!-- Status Filter Buttons -->
        <div class="flex items-center bg-surface-elevated p-1 rounded-xl border border-white/5 text-xs">
          <button
            @click="currentFilter = 'all'; currentPage = 1"
            class="px-3 py-1.5 rounded-lg font-medium transition-all"
            :class="currentFilter === 'all' ? 'bg-accent text-black font-semibold shadow' : 'text-gray-400 hover:text-white'"
          >
            Todos
          </button>
          <button
            @click="currentFilter = 'missing_image'; currentPage = 1"
            class="px-3 py-1.5 rounded-lg font-medium transition-all flex items-center space-x-1"
            :class="currentFilter === 'missing_image' ? 'bg-amber-500 text-black font-semibold shadow' : 'text-gray-400 hover:text-white'"
          >
            <AlertCircle class="w-3 h-3" />
            <span>Sem Foto</span>
          </button>
          <button
            @click="currentFilter = 'has_image'; currentPage = 1"
            class="px-3 py-1.5 rounded-lg font-medium transition-all flex items-center space-x-1"
            :class="currentFilter === 'has_image' ? 'bg-emerald-500 text-black font-semibold shadow' : 'text-gray-400 hover:text-white'"
          >
            <CheckCircle2 class="w-3 h-3" />
            <span>Com Foto</span>
          </button>
          <button
            @click="currentFilter = 'missing_bio'; currentPage = 1"
            class="px-3 py-1.5 rounded-lg font-medium transition-all flex items-center space-x-1"
            :class="currentFilter === 'missing_bio' ? 'bg-blue-500 text-white font-semibold shadow' : 'text-gray-400 hover:text-white'"
          >
            <FileText class="w-3 h-3" />
            <span>Sem Bio</span>
          </button>
        </div>

        <!-- Sort dropdown -->
        <div class="flex items-center space-x-1 bg-surface-elevated px-3 py-1.5 rounded-xl border border-white/5 text-xs">
          <ArrowUpDown class="w-3.5 h-3.5 text-gray-400" />
          <select
            v-model="sortBy"
            class="bg-transparent text-gray-200 focus:outline-none cursor-pointer pr-1"
          >
            <option value="name" class="bg-surface">Nome</option>
            <option value="track_count" class="bg-surface">Qtd. Músicas</option>
            <option value="album_count" class="bg-surface">Qtd. Álbuns</option>
          </select>
          <button
            @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
            class="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase bg-white/5 hover:bg-white/10 text-gray-300"
          >
            {{ sortOrder }}
          </button>
        </div>
      </div>
    </div>

    <!-- Artists Grid -->
    <div v-if="isLoading" class="py-24 flex flex-col items-center justify-center space-y-3 text-gray-400">
      <Loader2 class="w-8 h-8 animate-spin text-accent" />
      <p class="text-sm">Carregando catálogo de artistas...</p>
    </div>

    <div v-else-if="artists.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
      <ArtistCard
        v-for="artist in artists"
        :key="artist.artisthash"
        :artist="artist"
        @select="selectArtist"
      />
    </div>

    <div v-else class="py-20 text-center bg-surface rounded-3xl border border-white/5">
      <Users class="w-12 h-12 text-gray-600 mx-auto mb-3" />
      <h3 class="text-lg font-medium text-gray-300">Nenhum artista encontrado</h3>
      <p class="text-sm text-gray-500 mt-1 max-w-sm mx-auto">
        Tente ajustar seus filtros ou o termo de busca para encontrar o que procura.
      </p>
    </div>

    <!-- Pagination Controls -->
    <div v-if="totalPages > 1" class="flex items-center justify-center space-x-2 pt-4">
      <button
        @click="currentPage = Math.max(1, currentPage - 1)"
        :disabled="currentPage === 1 || isLoading"
        class="px-4 py-2 bg-surface-elevated hover:bg-surface-hover text-sm font-medium rounded-xl text-white disabled:opacity-30 transition-all"
      >
        Anterior
      </button>

      <div class="flex items-center space-x-1">
        <span class="px-3.5 py-2 rounded-xl bg-accent text-black font-bold text-sm">
          {{ currentPage }}
        </span>
        <span class="text-gray-500 text-sm">de</span>
        <span class="px-3.5 py-2 rounded-xl bg-surface-elevated text-gray-300 text-sm">
          {{ totalPages }}
        </span>
      </div>

      <button
        @click="currentPage = Math.min(totalPages, currentPage + 1)"
        :disabled="currentPage === totalPages || isLoading"
        class="px-4 py-2 bg-surface-elevated hover:bg-surface-hover text-sm font-medium rounded-xl text-white disabled:opacity-30 transition-all"
      >
        Próxima
      </button>
    </div>
  </div>
</template>

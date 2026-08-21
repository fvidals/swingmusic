<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { X, Search, Sparkles, Check, Loader2, ExternalLink, Globe, Link as LinkIcon } from 'lucide-vue-next';
import { api } from '../api/client';
import type { OnlineImageCandidate } from '../types';

const props = defineProps<{
  artisthash: string;
  artistName: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'selected-image', result: any): void;
  (e: 'selected-bio', bio: string): void;
}>();

const searchQuery = ref(props.artistName);
const isSearching = ref(false);
const isApplying = ref(false);
const applyingUrl = ref<string | null>(null);
const candidates = ref<OnlineImageCandidate[]>([]);
const mbResults = ref<any[]>([]);
const spotifyConfigured = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

// Direct URL
const customUrl = ref('');
const showUrlRow = ref(false);

async function performSearch() {
  if (!searchQuery.value.trim()) return;
  isSearching.value = true;
  errorMsg.value = '';

  try {
    const data = await api.searchOnline(props.artisthash, searchQuery.value.trim());
    candidates.value = data.images || [];
    mbResults.value = data.musicbrainz || [];
    spotifyConfigured.value = data.spotify_configured;
  } catch (err: any) {
    errorMsg.value = 'Erro ao buscar dados online.';
  } finally {
    isSearching.value = false;
  }
}

async function applyImage(candidate: OnlineImageCandidate) {
  if (!candidate.image_url) return;
  isApplying.value = true;
  applyingUrl.value = candidate.image_url;
  errorMsg.value = '';

  try {
    const result = await api.applyOnlineImage(props.artisthash, candidate.image_url);
    successMsg.value = `Foto do ${candidate.provider} aplicada com sucesso!`;
    emit('selected-image', result);
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao aplicar imagem.';
  } finally {
    isApplying.value = false;
    applyingUrl.value = null;
  }
}

async function applyCustomUrl() {
  const url = customUrl.value.trim();
  if (!url) return;
  isApplying.value = true;
  applyingUrl.value = url;
  errorMsg.value = '';

  try {
    const result = await api.applyOnlineImage(props.artisthash, url);
    successMsg.value = 'Foto da URL aplicada com sucesso!';
    emit('selected-image', result);
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao aplicar imagem da URL.';
  } finally {
    isApplying.value = false;
    applyingUrl.value = null;
  }
}

onMounted(() => {
  performSearch();
});
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in">
    <div class="bg-surface rounded-2xl border border-white/10 w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="p-5 border-b border-white/10 flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <Sparkles class="w-5 h-5 text-accent" />
          <h2 class="text-lg font-semibold text-white">Buscar Fotos & Dados Online</h2>
        </div>
        <button
          @click="emit('close')"
          class="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Search & URL Bar -->
      <div class="p-5 border-b border-white/5 bg-surface-elevated/40 space-y-3">
        <form @submit.prevent="performSearch" class="flex space-x-2">
          <div class="relative flex-1">
            <Search class="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Digite o nome do artista para pesquisar..."
              class="w-full bg-surface-elevated border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent"
            />
          </div>
          <button
            type="submit"
            :disabled="isSearching"
            class="px-5 py-2.5 bg-accent text-black font-semibold text-sm rounded-xl hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center space-x-1.5"
          >
            <Loader2 v-if="isSearching" class="w-4 h-4 animate-spin" />
            <Search v-else class="w-4 h-4" />
            <span>Buscar</span>
          </button>
        </form>

        <div class="flex items-center justify-between text-[11px] text-gray-400">
          <div class="flex items-center space-x-3">
            <span class="flex items-center space-x-1 text-emerald-400">
              <Check class="w-3 h-3" />
              <span>Deezer</span>
            </span>
            <span class="flex items-center space-x-1 text-emerald-400">
              <Check class="w-3 h-3" />
              <span>MusicBrainz</span>
            </span>
            <span
              class="flex items-center space-x-1"
              :class="spotifyConfigured ? 'text-emerald-400' : 'text-gray-500'"
            >
              <Globe class="w-3 h-3" />
              <span>Spotify ({{ spotifyConfigured ? 'Ativo' : 'Opcional' }})</span>
            </span>
          </div>

          <button
            type="button"
            @click="showUrlRow = !showUrlRow"
            class="text-xs text-accent hover:underline flex items-center space-x-1"
          >
            <LinkIcon class="w-3 h-3" />
            <span>{{ showUrlRow ? 'Ocultar URL Direta' : 'Informar URL Direta' }}</span>
          </button>
        </div>

        <!-- Direct URL input -->
        <div v-if="showUrlRow" class="p-3 bg-black/30 rounded-xl border border-white/5 space-y-2 animate-fade-in">
          <label class="text-[11px] text-gray-400 font-medium">Cole a URL de uma foto na web:</label>
          <div class="flex items-center space-x-2">
            <input
              v-model="customUrl"
              type="url"
              placeholder="https://exemplo.com/foto-artista.jpg"
              class="w-full bg-surface border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-accent"
              @keyup.enter="applyCustomUrl"
            />
            <button
              @click="applyCustomUrl"
              :disabled="!customUrl.trim() || isApplying"
              class="px-4 py-1.5 bg-accent text-black font-semibold rounded-xl text-xs hover:bg-accent/90 transition-all flex items-center space-x-1 disabled:opacity-40 flex-shrink-0"
            >
              <Loader2 v-if="isApplying && applyingUrl === customUrl.trim()" class="w-3.5 h-3.5 animate-spin" />
              <Check v-else class="w-3.5 h-3.5" />
              <span>Aplicar URL</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Content Area -->
      <div class="p-5 overflow-y-auto flex-1 space-y-6">
        <div v-if="errorMsg" class="p-3 bg-red-500/10 border border-red-500/20 text-red-300 rounded-xl text-xs">
          {{ errorMsg }}
        </div>
        <div v-if="successMsg" class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-xl text-xs">
          {{ successMsg }}
        </div>

        <!-- Loading state -->
        <div v-if="isSearching" class="py-16 flex flex-col items-center justify-center space-y-3 text-gray-400">
          <Loader2 class="w-8 h-8 animate-spin text-accent" />
          <p class="text-sm">Consultando Deezer, Spotify e MusicBrainz...</p>
        </div>

        <!-- Image Candidates Grid -->
        <div v-else-if="candidates.length > 0" class="space-y-3">
          <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Sugestões de Fotos Encontradas</h3>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            <div
              v-for="(cand, idx) in candidates"
              :key="idx"
              class="group relative bg-surface-elevated rounded-xl p-3 border border-white/5 hover:border-accent/50 transition-all flex flex-col items-center text-center overflow-hidden"
            >
              <!-- Provider Badge -->
              <div class="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md text-[10px] font-medium text-white">
                {{ cand.provider }}
              </div>

              <!-- Image -->
              <div class="w-24 h-24 rounded-full overflow-hidden mb-3 border-2 border-white/10 group-hover:border-accent transition-colors shadow-inner">
                <img
                  :src="cand.image_url"
                  :alt="cand.provider"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
              </div>

              <div class="text-[11px] text-gray-400 mb-2 truncate w-full">
                {{ cand.name || cand.provider }}
              </div>

              <!-- Action Button -->
              <button
                @click="applyImage(cand)"
                :disabled="isApplying"
                class="w-full py-1.5 bg-white/5 hover:bg-accent text-gray-300 hover:text-black border border-white/10 rounded-lg text-xs font-semibold transition-all flex items-center justify-center space-x-1 disabled:opacity-50"
              >
                <Loader2 v-if="isApplying && applyingUrl === cand.image_url" class="w-3 h-3 animate-spin" />
                <Check v-else class="w-3 h-3" />
                <span>Usar Esta Foto</span>
              </button>
            </div>
          </div>
        </div>

        <!-- No Results -->
        <div v-else-if="!isSearching && !errorMsg" class="py-16 text-center text-gray-500 space-y-2">
          <Sparkles class="w-8 h-8 mx-auto text-gray-600" />
          <p class="text-sm">Nenhuma foto encontrada. Tente buscar por outro termo ou use a opção de informar URL direta.</p>
        </div>
      </div>
    </div>
  </div>
</template>

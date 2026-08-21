<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from '../api/client';
import type { Track, OnlineAlbumCoverCandidate } from '../types';
import {
  X,
  Search,
  Image as ImageIcon,
  Upload,
  Check,
  AlertCircle,
  Loader2,
  Sparkles,
  Link as LinkIcon,
  Globe,
} from 'lucide-vue-next';

const props = defineProps<{
  track: Track;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'applied'): void;
}>();

const albumName = ref(props.track.album || '');
const artistName = ref('');
const candidates = ref<OnlineAlbumCoverCandidate[]>([]);
const isLoading = ref(false);
const isApplying = ref(false);
const applyingUrl = ref<string | null>(null);
const isUploading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');
const fileInput = ref<HTMLInputElement | null>(null);

// Direct URL state
const customUrl = ref('');
const showUrlInput = ref(false);

// Extract clean artist name
onMounted(() => {
  if (Array.isArray(props.track.artists)) {
    const first = props.track.artists[0];
    artistName.value = typeof first === 'object' ? first.name : String(first);
  } else if (typeof props.track.artists === 'string') {
    artistName.value = props.track.artists.split(/[,;/&]/)[0].trim();
  }
  searchCovers();
});

async function searchCovers() {
  if (!albumName.value.trim() && !artistName.value.trim()) return;
  isLoading.value = true;
  errorMsg.value = '';
  try {
    const data = await api.searchAlbumCovers(albumName.value.trim(), artistName.value.trim());
    candidates.value = data.covers || [];
    if (candidates.value.length === 0) {
      errorMsg.value = 'Nenhuma capa encontrada para esta combinação de álbum e artista.';
    }
  } catch (err: any) {
    errorMsg.value = 'Erro ao consultar serviços online. Verifique sua conexão.';
  } finally {
    isLoading.value = false;
  }
}

async function applyCover(candidate: OnlineAlbumCoverCandidate) {
  if (!candidate.image_url) return;
  isApplying.value = true;
  applyingUrl.value = candidate.image_url;
  errorMsg.value = '';
  try {
    await api.applyTrackOnlineCover(props.track.id, candidate.image_url);
    successMsg.value = `Capa do ${candidate.provider} aplicada com sucesso!`;
    setTimeout(() => {
      emit('applied');
      emit('close');
    }, 1000);
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao aplicar capa.';
  } finally {
    isApplying.value = false;
    applyingUrl.value = null;
  }
}

async function handleFileUpload(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  isUploading.value = true;
  errorMsg.value = '';
  try {
    await api.uploadTrackCover(props.track.id, file);
    successMsg.value = 'Capa local enviada e processada com sucesso!';
    setTimeout(() => {
      emit('applied');
      emit('close');
    }, 1000);
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao enviar capa.';
  } finally {
    isUploading.value = false;
  }
}

async function applyCustomUrl() {
  const url = customUrl.value.trim();
  if (!url) return;
  isApplying.value = true;
  applyingUrl.value = url;
  errorMsg.value = '';
  try {
    await api.applyTrackOnlineCover(props.track.id, url);
    successMsg.value = 'Capa da URL aplicada com sucesso!';
    setTimeout(() => {
      emit('applied');
      emit('close');
    }, 1000);
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao aplicar capa da URL.';
  } finally {
    isApplying.value = false;
    applyingUrl.value = null;
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
    <div class="bg-surface-elevated border border-white/10 rounded-3xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
      
      <!-- Modal Header -->
      <div class="p-6 border-b border-white/5 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-accent/10 flex items-center justify-center text-accent">
            <Sparkles class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-white">Gerenciar Capa do Álbum</h2>
            <p class="text-xs text-gray-400">
              Faixa: <span class="text-gray-200">{{ props.track.title }}</span> • Álbum: <span class="text-gray-200">{{ props.track.album || 'Sem Álbum' }}</span>
            </p>
          </div>
        </div>
        <button @click="$emit('close')" class="p-2 text-gray-400 hover:text-white rounded-full hover:bg-white/5 transition-all">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Search & Options Bar -->
      <div class="p-6 border-b border-white/5 bg-surface/50 space-y-4">
        <!-- Search Inputs -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 block">Álbum</label>
            <input
              v-model="albumName"
              type="text"
              placeholder="Nome do álbum..."
              @keyup.enter="searchCovers"
              class="w-full px-3.5 py-2 bg-surface rounded-xl border border-white/10 text-white placeholder-gray-500 text-sm focus:outline-none focus:border-accent"
            />
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 block">Artista</label>
            <div class="flex space-x-2">
              <input
                v-model="artistName"
                type="text"
                placeholder="Nome do artista..."
                @keyup.enter="searchCovers"
                class="w-full px-3.5 py-2 bg-surface rounded-xl border border-white/10 text-white placeholder-gray-500 text-sm focus:outline-none focus:border-accent"
              />
              <button
                @click="searchCovers"
                :disabled="isLoading"
                class="px-4 py-2 bg-accent text-black font-semibold rounded-xl text-sm hover:opacity-90 transition-all flex items-center space-x-1.5 flex-shrink-0 disabled:opacity-50"
              >
                <Search class="w-4 h-4" />
                <span>Buscar</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Manual Upload & Direct URL Options -->
        <div class="pt-2 border-t border-white/5 flex flex-wrap items-center justify-between gap-2">
          <div class="flex items-center space-x-2">
            <!-- URL Input Toggle -->
            <button
              @click="showUrlInput = !showUrlInput"
              class="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-xs text-white font-medium transition-all flex items-center space-x-1.5"
            >
              <Globe class="w-3.5 h-3.5 text-accent" />
              <span>{{ showUrlInput ? 'Ocultar URL' : 'Informar URL' }}</span>
            </button>

            <!-- File Upload -->
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleFileUpload"
            />
            <button
              @click="fileInput?.click()"
              :disabled="isUploading"
              class="px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-xs text-white font-medium transition-all flex items-center space-x-1.5"
            >
              <Upload class="w-3.5 h-3.5 text-accent" />
              <span>{{ isUploading ? 'Processando...' : 'Upload Manual' }}</span>
            </button>
          </div>
        </div>

        <!-- Collapsible Direct URL Row -->
        <div v-if="showUrlInput" class="p-3 bg-black/20 rounded-2xl border border-white/5 space-y-2 animate-fade-in">
          <label class="text-[11px] font-semibold text-gray-400 block">Cole a URL direta da imagem (JPG, PNG ou WebP):</label>
          <div class="flex items-center space-x-2">
            <div class="relative flex-1">
              <LinkIcon class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                v-model="customUrl"
                type="url"
                placeholder="https://exemplo.com/capa.jpg"
                class="w-full bg-surface border border-white/10 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-accent"
                @keyup.enter="applyCustomUrl"
              />
            </div>
            <button
              @click="applyCustomUrl"
              :disabled="!customUrl.trim() || isApplying"
              class="px-4 py-1.5 bg-accent text-black font-semibold rounded-xl text-xs hover:opacity-90 transition-all flex items-center space-x-1 disabled:opacity-40"
            >
              <Loader2 v-if="isApplying && applyingUrl === customUrl.trim()" class="w-3.5 h-3.5 animate-spin" />
              <Check v-else class="w-3.5 h-3.5" />
              <span>Aplicar URL</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Feedback Messages -->
      <div v-if="successMsg" class="mx-6 mt-4 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center space-x-2 text-xs text-emerald-400">
        <Check class="w-4 h-4 flex-shrink-0" />
        <span>{{ successMsg }}</span>
      </div>

      <div v-if="errorMsg" class="mx-6 mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center space-x-2 text-xs text-red-400">
        <AlertCircle class="w-4 h-4 flex-shrink-0" />
        <span>{{ errorMsg }}</span>
      </div>

      <!-- Results Grid -->
      <div class="p-6 overflow-y-auto flex-1">
        <!-- Loading -->
        <div v-if="isLoading" class="py-16 flex flex-col items-center justify-center text-gray-400 space-y-3">
          <Loader2 class="w-8 h-8 animate-spin text-accent" />
          <p class="text-sm">Consultando Apple Music, Deezer e Spotify...</p>
        </div>

        <!-- Candidates Grid -->
        <div v-else-if="candidates.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          <div
            v-for="(cand, idx) in candidates"
            :key="idx"
            class="bg-surface rounded-2xl p-2.5 border border-white/5 hover:border-accent/40 transition-all group flex flex-col justify-between space-y-2.5 shadow-sm"
          >
            <!-- Image Thumbnail -->
            <div class="aspect-square rounded-xl overflow-hidden bg-black/40 relative">
              <img
                :src="cand.image_url"
                :alt="cand.album"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
              />
              <div class="absolute top-2 left-2 px-2 py-0.5 rounded-full bg-black/70 backdrop-blur-md text-[10px] font-semibold text-white border border-white/10">
                {{ cand.provider }}
              </div>
            </div>

            <!-- Meta & Action -->
            <div class="space-y-1.5">
              <p class="text-xs font-semibold text-white truncate" :title="cand.album">{{ cand.album }}</p>
              <p class="text-[11px] text-gray-400 truncate" :title="cand.artist">{{ cand.artist }}</p>
              <div class="flex items-center justify-between text-[10px] text-gray-500 pt-1 border-t border-white/5">
                <span>{{ cand.year || 'HQ' }}</span>
              </div>
            </div>

            <button
              @click="applyCover(cand)"
              :disabled="isApplying"
              class="w-full py-1.5 bg-accent/10 hover:bg-accent text-accent hover:text-black border border-accent/20 rounded-xl text-xs font-semibold transition-all flex items-center justify-center space-x-1.5 disabled:opacity-50"
            >
              <Loader2 v-if="isApplying && applyingUrl === cand.image_url" class="w-3.5 h-3.5 animate-spin" />
              <Check v-else class="w-3.5 h-3.5" />
              <span>Usar Esta</span>
            </button>
          </div>
        </div>

        <!-- No Results -->
        <div v-else-if="!isLoading && !errorMsg" class="py-16 text-center text-gray-500 space-y-2">
          <ImageIcon class="w-10 h-10 mx-auto text-gray-600" />
          <p class="text-sm">Nenhum resultado online. Tente alterar os termos da busca acima.</p>
        </div>
      </div>
    </div>
  </div>
</template>

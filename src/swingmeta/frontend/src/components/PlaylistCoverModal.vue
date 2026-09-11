<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from '../api/client';
import type { M3UPlaylist, OnlinePlaylistCoverCandidate } from '../types';
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
  User,
} from 'lucide-vue-next';

const props = defineProps<{
  playlist: M3UPlaylist;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'applied'): void;
}>();

const searchQuery = ref(props.playlist.name || '');
const candidates = ref<OnlinePlaylistCoverCandidate[]>([]);
const spotifyConfigured = ref(false);
const isLoading = ref(false);
const isApplying = ref(false);
const applyingUrl = ref<string | null>(null);
const isUploading = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

// Tabs: 'online' | 'upload' | 'url'
const activeTab = ref<'online' | 'upload' | 'url'>('online');

// Upload tab state
const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);

// Direct URL tab state
const customUrl = ref('');

onMounted(() => {
  searchCovers();
});

async function searchCovers() {
  if (!searchQuery.value.trim()) return;
  isLoading.value = true;
  errorMsg.value = '';
  try {
    const data = await api.searchPlaylistCovers(searchQuery.value.trim());
    candidates.value = data.covers || [];
    spotifyConfigured.value = data.spotify_configured;
    if (candidates.value.length === 0) {
      errorMsg.value = 'Nenhuma capa de playlist encontrada nos serviços de streaming para este termo.';
    }
  } catch (err: any) {
    errorMsg.value = 'Erro ao consultar serviços de streaming. Verifique sua conexão.';
  } finally {
    isLoading.value = false;
  }
}

async function applyOnlineCover(candidate: OnlinePlaylistCoverCandidate) {
  if (!props.playlist.swing_playlist?.id || !candidate.image_url) return;
  isApplying.value = true;
  applyingUrl.value = candidate.image_url;
  errorMsg.value = '';

  try {
    await api.uploadPlaylistCover(props.playlist.swing_playlist.id, {
      imageUrl: candidate.image_url,
    });
    successMsg.value = `Capa do ${candidate.provider} aplicada com sucesso!`;
    setTimeout(() => {
      emit('applied');
      emit('close');
    }, 1200);
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao aplicar capa da playlist.';
  } finally {
    isApplying.value = false;
    applyingUrl.value = null;
  }
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  selectedFile.value = file;
  const reader = new FileReader();
  reader.onload = (ev) => {
    previewUrl.value = ev.target?.result as string;
  };
  reader.readAsDataURL(file);
}

async function applyUploadedFile() {
  if (!props.playlist.swing_playlist?.id || !selectedFile.value) return;
  isUploading.value = true;
  errorMsg.value = '';

  try {
    await api.uploadPlaylistCover(props.playlist.swing_playlist.id, selectedFile.value);
    successMsg.value = 'Capa local enviada e aplicada com sucesso!';
    setTimeout(() => {
      emit('applied');
      emit('close');
    }, 1200);
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao enviar arquivo de imagem.';
  } finally {
    isUploading.value = false;
  }
}

async function applyCustomUrl() {
  const url = customUrl.value.trim();
  if (!props.playlist.swing_playlist?.id || !url) return;
  isApplying.value = true;
  applyingUrl.value = url;
  errorMsg.value = '';

  try {
    await api.uploadPlaylistCover(props.playlist.swing_playlist.id, {
      imageUrl: url,
    });
    successMsg.value = 'Capa da URL aplicada com sucesso!';
    setTimeout(() => {
      emit('applied');
      emit('close');
    }, 1200);
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao aplicar imagem da URL.';
  } finally {
    isApplying.value = false;
    applyingUrl.value = null;
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
    <div
      class="bg-surface rounded-2xl border border-white/10 w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden"
    >
      <!-- Header -->
      <div class="p-5 border-b border-white/10 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="p-2.5 rounded-xl bg-accent/10 border border-accent/20 text-accent">
            <Sparkles class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-white flex items-center space-x-2">
              <span>Buscar Foto & Capa de Playlist</span>
            </h2>
            <p class="text-xs text-gray-400 mt-0.5">
              Playlist: <span class="text-white font-medium">{{ playlist.name }}</span>
            </p>
          </div>
        </div>

        <button
          @click="emit('close')"
          class="p-2 text-gray-400 hover:text-white rounded-xl hover:bg-white/10 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Navigation Tabs -->
      <div class="px-5 pt-3 pb-0 border-b border-white/5 flex items-center space-x-2 bg-surface-elevated/40">
        <button
          @click="activeTab = 'online'"
          class="px-4 py-2.5 text-xs font-semibold rounded-t-xl border-b-2 transition-all flex items-center space-x-2"
          :class="
            activeTab === 'online'
              ? 'border-accent text-accent bg-white/5'
              : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
          "
        >
          <Globe class="w-4 h-4" />
          <span>Serviços de Streaming (Deezer & Spotify)</span>
        </button>

        <button
          @click="activeTab = 'upload'"
          class="px-4 py-2.5 text-xs font-semibold rounded-t-xl border-b-2 transition-all flex items-center space-x-2"
          :class="
            activeTab === 'upload'
              ? 'border-accent text-accent bg-white/5'
              : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
          "
        >
          <Upload class="w-4 h-4" />
          <span>Upload do Computador</span>
        </button>

        <button
          @click="activeTab = 'url'"
          class="px-4 py-2.5 text-xs font-semibold rounded-t-xl border-b-2 transition-all flex items-center space-x-2"
          :class="
            activeTab === 'url'
              ? 'border-accent text-accent bg-white/5'
              : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5'
          "
        >
          <LinkIcon class="w-4 h-4" />
          <span>Colar Link Direto (URL)</span>
        </button>
      </div>

      <!-- Main Body -->
      <div class="p-6 overflow-y-auto flex-1 space-y-5">
        <!-- Toast feedback messages -->
        <div
          v-if="successMsg"
          class="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center space-x-2"
        >
          <Check class="w-4 h-4 flex-shrink-0" />
          <span>{{ successMsg }}</span>
        </div>

        <div
          v-if="errorMsg"
          class="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center space-x-2"
        >
          <AlertCircle class="w-4 h-4 flex-shrink-0" />
          <span>{{ errorMsg }}</span>
        </div>

        <!-- TAB 1: ONLINE SEARCH -->
        <div v-if="activeTab === 'online'" class="space-y-4">
          <!-- Search input box -->
          <div class="flex items-center space-x-2">
            <div class="relative flex-1">
              <Search class="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                v-model="searchQuery"
                @keyup.enter="searchCovers"
                type="text"
                placeholder="Nome da playlist para buscar capas (ex: Rock Classics, Anos 80, Pop)..."
                class="w-full bg-surface-elevated pl-10 pr-4 py-2.5 rounded-xl border border-white/10 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-accent"
              />
            </div>
            <button
              @click="searchCovers"
              :disabled="isLoading"
              class="px-5 py-2.5 bg-accent hover:bg-accent/90 text-black font-bold text-xs rounded-xl flex items-center space-x-2 transition-colors disabled:opacity-50"
            >
              <Loader2 v-if="isLoading" class="w-4 h-4 animate-spin" />
              <Search v-else class="w-4 h-4" />
              <span>Buscar</span>
            </button>
          </div>

          <!-- Provider indicators -->
          <div class="flex items-center justify-between text-[11px] text-gray-400 px-1">
            <span>Resultados dedicados de capas oficiais de playlists</span>
            <div class="flex items-center space-x-3">
              <span class="flex items-center space-x-1 text-cyan-400">
                <span class="w-2 h-2 rounded-full bg-cyan-400 inline-block"></span>
                <span>Deezer (1000x1000 HD)</span>
              </span>
              <span
                class="flex items-center space-x-1"
                :class="spotifyConfigured ? 'text-emerald-400' : 'text-gray-500'"
              >
                <span
                  class="w-2 h-2 rounded-full inline-block"
                  :class="spotifyConfigured ? 'bg-emerald-400' : 'bg-gray-600'"
                ></span>
                <span>Spotify {{ spotifyConfigured ? '(Ativo)' : '(Não configurado)' }}</span>
              </span>
            </div>
          </div>

          <!-- Loading state -->
          <div v-if="isLoading" class="py-16 flex flex-col items-center justify-center space-y-3">
            <Loader2 class="w-8 h-8 animate-spin text-accent" />
            <p class="text-xs text-gray-400">Consultando capas oficiais de playlists...</p>
          </div>

          <!-- Empty state -->
          <div
            v-else-if="candidates.length === 0"
            class="py-12 border border-dashed border-white/10 rounded-2xl flex flex-col items-center justify-center space-y-2 text-center p-6"
          >
            <ImageIcon class="w-10 h-10 text-gray-600" />
            <p class="text-sm font-semibold text-gray-300">Nenhum resultado online no momento</p>
            <p class="text-xs text-gray-500 max-w-sm">
              Tente buscar por termos alternativos ou use as abas acima para enviar um arquivo local ou colar uma URL direta.
            </p>
          </div>

          <!-- Results Grid -->
          <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
            <div
              v-for="(c, idx) in candidates"
              :key="idx"
              class="bg-surface-elevated rounded-2xl overflow-hidden border border-white/5 hover:border-accent/40 group/card transition-all flex flex-col shadow-sm"
            >
              <!-- Image Thumbnail -->
              <div class="aspect-square relative overflow-hidden bg-black/40">
                <img
                  :src="c.thumbnail_url || c.image_url"
                  :alt="c.title"
                  class="w-full h-full object-cover group-hover/card:scale-105 transition-transform duration-300"
                  loading="lazy"
                />

                <!-- Provider Badge -->
                <div class="absolute top-2 left-2">
                  <span
                    class="px-2 py-0.5 rounded-full text-[10px] font-bold shadow-md uppercase tracking-wider"
                    :class="
                      c.provider === 'Spotify'
                        ? 'bg-emerald-500/90 text-black'
                        : 'bg-cyan-500/90 text-black'
                    "
                  >
                    {{ c.provider }}
                  </span>
                </div>

                <!-- Resolution/Tracks Badge -->
                <div v-if="c.track_count" class="absolute top-2 right-2">
                  <span class="px-1.5 py-0.5 rounded bg-black/70 backdrop-blur-sm text-white text-[9px] font-semibold">
                    {{ c.track_count }} faixas
                  </span>
                </div>
              </div>

              <!-- Metadata & Action -->
              <div class="p-3 flex-1 flex flex-col justify-between space-y-2.5">
                <div>
                  <h4 class="text-xs font-bold text-white truncate" :title="c.title">{{ c.title }}</h4>
                  <p class="text-[11px] text-gray-400 truncate flex items-center space-x-1 mt-0.5">
                    <User class="w-3 h-3 text-gray-500 inline flex-shrink-0" />
                    <span>{{ c.creator || 'Curador' }}</span>
                  </p>
                </div>

                <button
                  @click="applyOnlineCover(c)"
                  :disabled="isApplying && applyingUrl === c.image_url"
                  class="w-full py-2 bg-white/10 hover:bg-accent text-white hover:text-black font-bold text-xs rounded-xl transition-all flex items-center justify-center space-x-1.5 disabled:opacity-50"
                >
                  <Loader2
                    v-if="isApplying && applyingUrl === c.image_url"
                    class="w-3.5 h-3.5 animate-spin"
                  />
                  <Check v-else class="w-3.5 h-3.5" />
                  <span>Aplicar Capa</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB 2: UPLOAD LOCAL FILE -->
        <div v-if="activeTab === 'upload'" class="space-y-4">
          <div
            @click="fileInput?.click()"
            class="border-2 border-dashed border-white/20 hover:border-accent/60 rounded-2xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-colors group bg-surface-elevated/30 hover:bg-surface-elevated/60"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="hidden"
              @change="handleFileSelect"
            />

            <!-- Preview if selected -->
            <div v-if="previewUrl" class="space-y-3 flex flex-col items-center">
              <div class="w-36 h-36 rounded-2xl overflow-hidden border border-white/20 shadow-lg">
                <img :src="previewUrl" alt="Pré-visualização" class="w-full h-full object-cover" />
              </div>
              <p class="text-xs text-white font-medium">{{ selectedFile?.name }}</p>
              <p class="text-[11px] text-accent font-semibold">Clique para escolher outro arquivo</p>
            </div>

            <!-- Empty prompt -->
            <div v-else class="space-y-2 flex flex-col items-center">
              <div class="p-3.5 rounded-full bg-accent/10 border border-accent/20 text-accent group-hover:scale-110 transition-transform">
                <Upload class="w-7 h-7" />
              </div>
              <p class="text-sm font-semibold text-white">Clique para selecionar uma imagem do seu computador</p>
              <p class="text-xs text-gray-400">Formatos aceitos: JPG, PNG, WEBP (Quadrado 1:1 recomendado)</p>
            </div>
          </div>

          <div v-if="selectedFile" class="flex justify-end">
            <button
              @click="applyUploadedFile"
              :disabled="isUploading"
              class="px-6 py-2.5 bg-accent hover:bg-accent/90 text-black font-bold text-xs rounded-xl flex items-center space-x-2 transition-all disabled:opacity-50 shadow-lg shadow-accent/20"
            >
              <Loader2 v-if="isUploading" class="w-4 h-4 animate-spin" />
              <Check v-else class="w-4 h-4" />
              <span>Salvar e Aplicar Capa na Playlist</span>
            </button>
          </div>
        </div>

        <!-- TAB 3: DIRECT IMAGE URL -->
        <div v-if="activeTab === 'url'" class="space-y-4">
          <div class="space-y-2">
            <label class="text-xs font-semibold text-gray-300">URL Direta da Imagem (JPG, PNG ou WebP):</label>
            <div class="flex items-center space-x-2">
              <div class="relative flex-1">
                <LinkIcon class="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  v-model="customUrl"
                  type="url"
                  placeholder="https://exemplo.com/minha-capa.jpg"
                  class="w-full bg-surface-elevated pl-10 pr-4 py-2.5 rounded-xl border border-white/10 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-accent"
                />
              </div>
              <button
                @click="applyCustomUrl"
                :disabled="!customUrl.trim() || isApplying"
                class="px-6 py-2.5 bg-accent hover:bg-accent/90 text-black font-bold text-xs rounded-xl flex items-center space-x-2 transition-all disabled:opacity-50"
              >
                <Loader2 v-if="isApplying" class="w-4 h-4 animate-spin" />
                <Check v-else class="w-4 h-4" />
                <span>Aplicar da URL</span>
              </button>
            </div>
          </div>

          <!-- URL Preview if typed -->
          <div v-if="customUrl.trim()" class="p-4 rounded-2xl bg-surface-elevated border border-white/10 flex items-center space-x-4">
            <div class="w-20 h-20 rounded-xl overflow-hidden bg-black/40 border border-white/10 flex-shrink-0">
              <img
                :src="customUrl.trim()"
                alt="Preview"
                class="w-full h-full object-cover"
                @error="errorMsg = 'Não foi possível carregar a imagem desta URL. Verifique se o link está correto.'"
              />
            </div>
            <div class="min-w-0">
              <p class="text-xs font-bold text-white">Pré-visualização da URL</p>
              <p class="text-[11px] text-gray-400 truncate mt-0.5">{{ customUrl }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-white/10 flex items-center justify-between bg-surface-elevated/40 text-xs text-gray-400">
        <span>As capas são convertidas em WebP 512x512 e miniatura 250x250 automaticamente para o SwingMusic.</span>
        <button
          @click="emit('close')"
          class="px-4 py-2 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-colors"
        >
          Fechar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { api } from '../api/client';
import type { Track, OnlineAlbumCoverCandidate } from '../types';
import {
  X,
  Upload,
  Link as LinkIcon,
  Search,
  Check,
  AlertCircle,
  Loader2,
  Sparkles,
  Disc,
  FileCheck,
  Globe,
  Image as ImageIcon,
} from 'lucide-vue-next';

const props = defineProps<{
  selectedTracks: Track[];
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'applied'): void;
}>();

type TabType = 'upload' | 'url' | 'online';
const activeTab = ref<TabType>('upload');

// Options
const embedAudio = ref(false);
const isProcessing = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

// Tab 1: File Upload
const selectedFile = ref<File | null>(null);
const filePreviewUrl = ref<string | null>(null);
const fileInput = ref<HTMLInputElement | null>(null);

// Tab 2: URL
const directUrl = ref('');
const urlPreviewValid = ref(false);
const urlPreviewLoading = ref(false);
const urlPreviewError = ref('');

// Tab 3: Online Search
const searchAlbum = ref('');
const searchArtist = ref('');
const isSearchingOnline = ref(false);
const onlineCandidates = ref<OnlineAlbumCoverCandidate[]>([]);
const selectedOnlineUrl = ref<string | null>(null);

// Selected source
const activePreviewUrl = computed(() => {
  if (activeTab.value === 'upload') return filePreviewUrl.value;
  if (activeTab.value === 'url') return urlPreviewValid.value ? directUrl.value.trim() : null;
  if (activeTab.value === 'online') return selectedOnlineUrl.value;
  return null;
});

const canSubmit = computed(() => {
  if (isProcessing.value) return false;
  if (activeTab.value === 'upload') return !!selectedFile.value;
  if (activeTab.value === 'url') return urlPreviewValid.value && !!directUrl.value.trim();
  if (activeTab.value === 'online') return !!selectedOnlineUrl.value;
  return false;
});

// Initialization
onMounted(async () => {
  try {
    const s = await api.getSettings();
    embedAudio.value = s.embed_audio_tags ?? false;
  } catch (err) {
    embedAudio.value = false;
  }

  if (props.selectedTracks.length > 0) {
    const first = props.selectedTracks[0];
    searchAlbum.value = first.album || '';
    if (Array.isArray(first.artists) && first.artists.length > 0) {
      const art = first.artists[0];
      searchArtist.value = typeof art === 'object' ? art.name : String(art);
    } else if (typeof first.artists === 'string') {
      searchArtist.value = first.artists.split(/[,;/&]/)[0].trim();
    }
  }
});

// File upload handlers
function onFileSelected(e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  selectedFile.value = file;
  filePreviewUrl.value = URL.createObjectURL(file);
  errorMsg.value = '';
}

function onDrop(e: DragEvent) {
  e.preventDefault();
  const file = e.dataTransfer?.files?.[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) {
    errorMsg.value = 'Por favor, selecione um arquivo de imagem válido (.jpg, .png, .webp).';
    return;
  }

  selectedFile.value = file;
  filePreviewUrl.value = URL.createObjectURL(file);
  errorMsg.value = '';
}

// Direct URL handlers
function onUrlChange() {
  const url = directUrl.value.trim();
  urlPreviewError.value = '';
  urlPreviewValid.value = false;

  if (!url) return;
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    urlPreviewError.value = 'URL deve começar com http:// ou https://';
    return;
  }

  urlPreviewLoading.value = true;
  const img = new Image();
  img.onload = () => {
    urlPreviewLoading.value = false;
    urlPreviewValid.value = true;
  };
  img.onerror = () => {
    urlPreviewLoading.value = false;
    urlPreviewValid.value = false;
    urlPreviewError.value = 'Não foi possível carregar a imagem da URL informada.';
  };
  img.src = url;
}

// Online search handlers
async function searchOnline() {
  if (!searchAlbum.value.trim() && !searchArtist.value.trim()) return;
  isSearchingOnline.value = true;
  errorMsg.value = '';
  selectedOnlineUrl.value = null;

  try {
    const res = await api.searchAlbumCovers(searchAlbum.value.trim(), searchArtist.value.trim());
    onlineCandidates.value = res.covers || [];
    if (onlineCandidates.value.length === 0) {
      errorMsg.value = 'Nenhuma capa encontrada para esta busca.';
    }
  } catch (err: any) {
    errorMsg.value = 'Erro ao consultar serviços online.';
  } finally {
    isSearchingOnline.value = false;
  }
}

function selectOnlineCandidate(candidate: OnlineAlbumCoverCandidate) {
  selectedOnlineUrl.value = candidate.image_url;
}

// Submit Batch
async function applyBatch() {
  if (!canSubmit.value) return;

  isProcessing.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  const trackIds = props.selectedTracks.map((t) => t.id);

  try {
    let res;
    if (activeTab.value === 'upload' && selectedFile.value) {
      res = await api.applyBatchCover(trackIds, {
        file: selectedFile.value,
        embedAudio: embedAudio.value,
      });
    } else if (activeTab.value === 'url' && directUrl.value.trim()) {
      res = await api.applyBatchCover(trackIds, {
        imageUrl: directUrl.value.trim(),
        embedAudio: embedAudio.value,
      });
    } else if (activeTab.value === 'online' && selectedOnlineUrl.value) {
      res = await api.applyBatchCover(trackIds, {
        imageUrl: selectedOnlineUrl.value,
        embedAudio: embedAudio.value,
      });
    }

    if (res?.success) {
      successMsg.value = `Capa aplicada com sucesso em ${res.total_tracks} faixas (${res.updated_files} arquivos físicos atualizados)!`;
      setTimeout(() => {
        emit('applied');
        emit('close');
      }, 1200);
    } else {
      throw new Error('Erro ao processar lote de capas');
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao aplicar capa em lote.';
  } finally {
    isProcessing.value = false;
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
    <div class="bg-surface-elevated border border-white/10 rounded-3xl w-full max-w-3xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
      
      <!-- Modal Header -->
      <div class="p-6 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
        <div class="flex items-center space-x-3">
          <div class="p-2.5 bg-accent/10 border border-accent/20 rounded-2xl text-accent">
            <ImageIcon class="w-6 h-6" />
          </div>
          <div>
            <h2 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
              <span>Capa em Lote</span>
              <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-accent/20 text-accent border border-accent/30">
                {{ selectedTracks.length }} faixas selecionadas
              </span>
            </h2>
            <p class="text-xs text-gray-400 mt-0.5">
              Defina a mesma arte de capa para todas as faixas selecionadas.
            </p>
          </div>
        </div>

        <button
          @click="emit('close')"
          :disabled="isProcessing"
          class="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-colors disabled:opacity-50"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex border-b border-white/10 bg-black/20 px-6 pt-3 gap-2">
        <button
          @click="activeTab = 'upload'"
          class="pb-3 px-4 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-all"
          :class="activeTab === 'upload' ? 'border-accent text-accent' : 'border-transparent text-gray-400 hover:text-gray-200'"
        >
          <Upload class="w-4 h-4" />
          <span>Upload de Arquivo</span>
        </button>

        <button
          @click="activeTab = 'url'"
          class="pb-3 px-4 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-all"
          :class="activeTab === 'url' ? 'border-accent text-accent' : 'border-transparent text-gray-400 hover:text-gray-200'"
        >
          <Globe class="w-4 h-4" />
          <span>URL Direta</span>
        </button>

        <button
          @click="activeTab = 'online'"
          class="pb-3 px-4 text-xs font-semibold flex items-center space-x-2 border-b-2 transition-all"
          :class="activeTab === 'online' ? 'border-accent text-accent' : 'border-transparent text-gray-400 hover:text-gray-200'"
        >
          <Sparkles class="w-4 h-4" />
          <span>Buscar Online</span>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-6 overflow-y-auto space-y-6 flex-1">
        
        <!-- Alerts -->
        <div v-if="errorMsg" class="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center space-x-3 text-red-400 text-sm">
          <AlertCircle class="w-5 h-5 flex-shrink-0" />
          <span>{{ errorMsg }}</span>
        </div>

        <div v-if="successMsg" class="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl flex items-center space-x-3 text-emerald-400 text-sm">
          <Check class="w-5 h-5 flex-shrink-0" />
          <span>{{ successMsg }}</span>
        </div>

        <!-- TAB 1: File Upload -->
        <div v-if="activeTab === 'upload'" class="space-y-4">
          <div
            @dragover.prevent
            @drop="onDrop"
            @click="fileInput?.click()"
            class="border-2 border-dashed border-white/10 hover:border-accent/40 rounded-3xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all bg-black/20 hover:bg-white/[0.02] group"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              class="hidden"
              @change="onFileSelected"
            />

            <div v-if="filePreviewUrl" class="space-y-3 flex flex-col items-center">
              <div class="w-40 h-40 rounded-2xl overflow-hidden shadow-2xl border border-white/20 relative group-hover:scale-105 transition-transform">
                <img :src="filePreviewUrl" alt="Preview" class="w-full h-full object-cover" />
              </div>
              <p class="text-xs text-accent font-medium">Clique ou arraste para trocar a imagem selecionada</p>
              <p class="text-[11px] text-gray-400">{{ selectedFile?.name }} ({{ Math.round((selectedFile?.size || 0) / 1024) }} KB)</p>
            </div>

            <div v-else class="space-y-3 flex flex-col items-center">
              <div class="p-4 rounded-full bg-surface-elevated text-gray-400 group-hover:text-accent group-hover:bg-accent/10 transition-colors">
                <Upload class="w-8 h-8" />
              </div>
              <div>
                <p class="text-sm font-semibold text-white">Arraste uma imagem ou clique para selecionar</p>
                <p class="text-xs text-gray-500 mt-1">Suporta JPG, PNG e WebP em alta resolução</p>
              </div>
            </div>
          </div>
        </div>

        <!-- TAB 2: Direct URL -->
        <div v-else-if="activeTab === 'url'" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
              URL da Imagem na Web
            </label>
            <div class="flex items-center space-x-2">
              <div class="relative flex-1">
                <LinkIcon class="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  v-model="directUrl"
                  type="url"
                  placeholder="https://exemplo.com/capa-album.jpg"
                  class="w-full bg-surface border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent"
                  @input="onUrlChange"
                />
              </div>
              <button
                @click="onUrlChange"
                type="button"
                class="px-4 py-2.5 bg-surface-elevated hover:bg-white/10 text-white rounded-xl text-xs font-semibold border border-white/10 transition-colors"
              >
                Validar
              </button>
            </div>
            <p v-if="urlPreviewError" class="text-xs text-red-400 mt-1.5">{{ urlPreviewError }}</p>
            <p class="text-[11px] text-gray-500 mt-1.5">
              Cole o link direto da imagem (de sites como Spotify, Deezer, Fanart, Discogs ou qualquer URL pública).
            </p>
          </div>

          <!-- URL Preview Card -->
          <div v-if="directUrl.trim()" class="p-4 bg-surface rounded-2xl border border-white/5 flex items-center space-x-4">
            <div class="w-24 h-24 rounded-xl overflow-hidden bg-black/40 border border-white/10 flex-shrink-0 flex items-center justify-center relative">
              <Loader2 v-if="urlPreviewLoading" class="w-6 h-6 animate-spin text-accent" />
              <img
                v-else-if="urlPreviewValid"
                :src="directUrl.trim()"
                alt="Preview"
                class="w-full h-full object-cover"
              />
              <ImageIcon v-else class="w-6 h-6 text-gray-600" />
            </div>

            <div class="flex-1 min-w-0">
              <div v-if="urlPreviewValid" class="flex items-center space-x-1.5 text-emerald-400 text-xs font-semibold mb-1">
                <Check class="w-4 h-4" />
                <span>Imagem válida e pronta para aplicar!</span>
              </div>
              <p class="text-xs text-gray-400 truncate">{{ directUrl }}</p>
            </div>
          </div>
        </div>

        <!-- TAB 3: Online Search -->
        <div v-else-if="activeTab === 'online'" class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-gray-400 mb-1.5">Nome do Álbum</label>
              <input
                v-model="searchAlbum"
                type="text"
                placeholder="Ex: Hybrid Theory"
                class="w-full bg-surface border border-white/10 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-accent"
                @keyup.enter="searchOnline"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-400 mb-1.5">Artista</label>
              <div class="flex items-center space-x-2">
                <input
                  v-model="searchArtist"
                  type="text"
                  placeholder="Ex: Linkin Park"
                  class="w-full bg-surface border border-white/10 rounded-xl px-3.5 py-2 text-sm text-white focus:outline-none focus:border-accent"
                  @keyup.enter="searchOnline"
                />
                <button
                  @click="searchOnline"
                  :disabled="isSearchingOnline"
                  class="px-4 py-2 bg-accent text-black font-semibold rounded-xl text-xs flex items-center space-x-1.5 hover:bg-accent/90 transition-all flex-shrink-0 disabled:opacity-50"
                >
                  <Loader2 v-if="isSearchingOnline" class="w-3.5 h-3.5 animate-spin" />
                  <Search v-else class="w-3.5 h-3.5" />
                  <span>Buscar</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Candidates Grid -->
          <div v-if="onlineCandidates.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 pt-2 max-h-64 overflow-y-auto">
            <div
              v-for="(cand, idx) in onlineCandidates"
              :key="idx"
              @click="selectOnlineCandidate(cand)"
              class="relative rounded-2xl overflow-hidden border-2 cursor-pointer transition-all group bg-surface shadow-md"
              :class="selectedOnlineUrl === cand.image_url ? 'border-accent scale-[1.02] shadow-accent/20' : 'border-transparent hover:border-white/20'"
            >
              <div class="aspect-square w-full bg-black/40 overflow-hidden relative">
                <img :src="cand.image_url" :alt="cand.album" class="w-full h-full object-cover" loading="lazy" />
                
                <!-- Provider Badge -->
                <div class="absolute top-2 left-2 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-black/70 backdrop-blur-md text-white border border-white/10">
                  {{ cand.provider }}
                </div>

                <!-- Selected Overlay -->
                <div v-if="selectedOnlineUrl === cand.image_url" class="absolute inset-0 bg-accent/20 flex items-center justify-center text-accent backdrop-blur-[2px]">
                  <div class="p-2 rounded-full bg-accent text-black shadow-lg">
                    <Check class="w-4 h-4 stroke-[3]" />
                  </div>
                </div>
              </div>

              <div class="p-2.5 text-xs">
                <p class="font-semibold text-white truncate">{{ cand.album }}</p>
                <p class="text-gray-400 text-[11px] truncate">{{ cand.artist }}</p>
                <p class="text-[10px] text-gray-500 mt-0.5">{{ cand.year || 'HQ' }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Options & Selected Tracks Summary -->
        <div class="p-4 bg-surface rounded-2xl border border-white/5 space-y-3">
          <label class="flex items-center space-x-3 cursor-pointer select-none">
            <input
              v-model="embedAudio"
              type="checkbox"
              class="w-4 h-4 rounded text-accent focus:ring-accent border-white/20 bg-surface-elevated"
            />
            <div>
              <span class="text-xs font-semibold text-white block">Embutir capa nas tags dos arquivos físicos</span>
              <span class="text-[11px] text-gray-400 block">
                Grava a imagem diretamente nas tags ID3 / FLAC / MP4 / OGG das faixas no armazenamento.
              </span>
            </div>
          </label>

          <div class="pt-2 border-t border-white/5 flex items-center justify-between text-xs text-gray-400">
            <span>Faixas que receberão esta arte:</span>
            <span class="font-medium text-white">{{ selectedTracks.length }} faixas</span>
          </div>
        </div>

      </div>

      <!-- Modal Footer -->
      <div class="p-6 border-t border-white/10 flex items-center justify-between bg-white/[0.02]">
        <button
          @click="emit('close')"
          :disabled="isProcessing"
          class="px-5 py-2.5 rounded-xl text-xs font-semibold text-gray-400 hover:text-white hover:bg-white/5 transition-colors disabled:opacity-50"
        >
          Cancelar
        </button>

        <button
          @click="applyBatch"
          :disabled="!canSubmit || isProcessing"
          class="px-6 py-2.5 bg-accent text-black font-bold rounded-xl text-xs shadow-lg shadow-accent/20 hover:bg-accent/90 transition-all flex items-center space-x-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="isProcessing" class="w-4 h-4 animate-spin" />
          <FileCheck v-else class="w-4 h-4" />
          <span>{{ isProcessing ? 'Aplicando nas faixas...' : `Aplicar em ${selectedTracks.length} Faixas` }}</span>
        </button>
      </div>

    </div>
  </div>
</template>

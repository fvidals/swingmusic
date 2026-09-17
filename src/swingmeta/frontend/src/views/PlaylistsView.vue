<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
  ListMusic,
  Plus,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertCircle,
  Eye,
  Trash2,
  Loader2,
  FolderTree,
  Check,
  Upload,
  Image as ImageIcon,
  Globe,
  Link as LinkIcon,
  Sparkles,
} from 'lucide-vue-next';
import { api } from '../api/client';
import type { M3UPlaylist } from '../types';
import M3UDetailModal from '../components/M3UDetailModal.vue';
import PlaylistCoverModal from '../components/PlaylistCoverModal.vue';

const playlists = ref<M3UPlaylist[]>([]);
const isLoading = ref(true);
const search = ref('');
const filterStatus = ref<'all' | 'created' | 'not_created'>('all');
const selectedM3UPath = ref<string | null>(null);

const selectedCoverPlaylist = ref<M3UPlaylist | null>(null);
const isCoverModalOpen = ref(false);

const activeCreatingPath = ref<string | null>(null);
const uploadingPlaylistId = ref<number | null>(null);
const feedbackMsg = ref('');
const errorMsg = ref('');

function openCoverModal(p: M3UPlaylist) {
  if (!p.is_created_in_swing || !p.swing_playlist?.id) {
    if (confirm(`Para definir a capa, a playlist "${p.name}" precisa ser criada no SwingMusic primeiro. Deseja criá-la agora?`)) {
      quickCreatePlaylist(p).then(() => {
        const found = playlists.value.find(item => item.filepath === p.filepath);
        if (found && found.is_created_in_swing && found.swing_playlist?.id) {
          selectedCoverPlaylist.value = found;
          isCoverModalOpen.value = true;
        }
      });
    }
    return;
  }
  selectedCoverPlaylist.value = p;
  isCoverModalOpen.value = true;
}

const playlistFileInputs = ref<{ [key: number]: HTMLInputElement | null }>({});

async function loadPlaylists() {
  isLoading.value = true;
  errorMsg.value = '';
  try {
    const data = await api.getPlaylists();
    playlists.value = data.playlists || [];
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao carregar playlists';
  } finally {
    isLoading.value = false;
  }
}

async function quickCreatePlaylist(p: M3UPlaylist) {
  activeCreatingPath.value = p.filepath;
  feedbackMsg.value = '';
  errorMsg.value = '';

  try {
    const res = await api.createPlaylist(p.filepath, p.name);
    const coverNote = res.cover_applied ? ' Capa local aplicada.' : '';
    feedbackMsg.value = `Playlist "${p.name}" ${res.action === 'updated' ? 'sincronizada' : 'criada'} com sucesso no SwingMusic! (${res.imported_tracks} músicas)${coverNote}`;
    p.is_created_in_swing = true;
    await loadPlaylists();
    setTimeout(() => {
      feedbackMsg.value = '';
    }, 4000);
  } catch (err: any) {
    errorMsg.value = err.message || 'Falha ao criar playlist no SwingMusic';
  } finally {
    activeCreatingPath.value = null;
  }
}

async function removeSwingPlaylist(p: M3UPlaylist) {
  if (!p.swing_playlist?.id) return;
  if (!confirm(`Deseja realmente remover a playlist "${p.name}" do SwingMusic? (O arquivo .m3u continuará no disco)`)) return;

  try {
    await api.deleteSwingPlaylist(p.swing_playlist.id);
    p.is_created_in_swing = false;
    p.swing_playlist = undefined;
    feedbackMsg.value = `Playlist "${p.name}" removida do SwingMusic.`;
    setTimeout(() => {
      feedbackMsg.value = '';
    }, 3000);
  } catch (err: any) {
    errorMsg.value = 'Erro ao remover playlist.';
  }
}

async function handleCoverUpload(p: M3UPlaylist, e: Event) {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file || !p.swing_playlist?.id) return;

  uploadingPlaylistId.value = p.swing_playlist.id;
  errorMsg.value = '';
  feedbackMsg.value = '';

  try {
    const res = await api.uploadPlaylistCover(p.swing_playlist.id, file);
    if (p.swing_playlist) {
      p.swing_playlist.image = res.image;
      p.swing_playlist.has_image = true;
      p.swing_playlist.image_url = `${res.image_url}?t=${Date.now()}`;
    }
    feedbackMsg.value = `Capa da playlist "${p.name}" atualizada com sucesso!`;
    setTimeout(() => {
      feedbackMsg.value = '';
    }, 4000);
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao enviar capa da playlist.';
  } finally {
    uploadingPlaylistId.value = null;
  }
}

async function handleCoverUrlPrompt(p: M3UPlaylist) {
  if (!p.swing_playlist?.id) return;
  const url = prompt(`Cole a URL direta da imagem para a playlist "${p.name}" (JPG, PNG ou WebP):`);
  if (!url || !url.trim()) return;

  uploadingPlaylistId.value = p.swing_playlist.id;
  errorMsg.value = '';
  feedbackMsg.value = '';

  try {
    const res = await api.uploadPlaylistCover(p.swing_playlist.id, { imageUrl: url.trim() });
    if (p.swing_playlist) {
      p.swing_playlist.image = res.image;
      p.swing_playlist.has_image = true;
      p.swing_playlist.image_url = `${res.image_url}?t=${Date.now()}`;
    }
    feedbackMsg.value = `Capa da playlist "${p.name}" atualizada com sucesso!`;
    setTimeout(() => {
      feedbackMsg.value = '';
    }, 4000);
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao aplicar capa da URL.';
  } finally {
    uploadingPlaylistId.value = null;
  }
}

function triggerCoverUpload(playlistId: number) {
  playlistFileInputs.value[playlistId]?.click();
}

function filteredPlaylists(): M3UPlaylist[] {
  let list = playlists.value;

  if (search.value.trim()) {
    const q = search.value.trim().toLowerCase();
    list = list.filter(p => p.name.toLowerCase().includes(q) || p.filepath.toLowerCase().includes(q));
  }

  if (filterStatus.value === 'created') {
    list = list.filter(p => p.is_created_in_swing);
  } else if (filterStatus.value === 'not_created') {
    list = list.filter(p => !p.is_created_in_swing);
  }

  return list;
}

onMounted(() => {
  loadPlaylists();
});
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-gradient-to-b from-surface-elevated/70 to-surface rounded-3xl p-6 sm:p-8 border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <div class="flex items-center space-x-2 text-accent text-sm font-medium mb-1">
          <ListMusic class="w-4 h-4" />
          <span>Importador & Capas de Playlists</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Playlists M3U & Capas
        </h1>
        <p class="text-sm text-gray-400 mt-1">
          Detecta arquivos <code>.m3u</code> nas pastas de música, sincroniza com o SwingMusic e permite upload de capas personalizadas.
        </p>
      </div>

      <button
        @click="loadPlaylists"
        :disabled="isLoading"
        class="px-4 py-2.5 bg-white/5 hover:bg-white/10 text-white text-xs font-semibold rounded-2xl border border-white/10 flex items-center space-x-2 transition-all self-start md:self-auto"
      >
        <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isLoading }" />
        <span>Escanear Pastas</span>
      </button>
    </div>

    <!-- Alert Messages -->
    <div v-if="feedbackMsg" class="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-2xl text-xs flex items-center space-x-2 shadow-lg">
      <Check class="w-4 h-4 text-emerald-400 flex-shrink-0" />
      <span>{{ feedbackMsg }}</span>
    </div>

    <div v-if="errorMsg" class="p-4 bg-red-500/10 border border-red-500/20 text-red-300 rounded-2xl text-xs">
      {{ errorMsg }}
    </div>

    <!-- Filters & Search -->
    <div class="bg-surface rounded-2xl p-4 border border-white/5 flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
      <div class="relative flex-1">
        <Search class="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
        <input
          v-model="search"
          type="text"
          placeholder="Buscar playlist por nome ou arquivo..."
          class="w-full bg-surface-elevated border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent"
        />
      </div>

      <div class="flex items-center bg-surface-elevated p-1 rounded-xl border border-white/5 text-xs">
        <button
          @click="filterStatus = 'all'"
          class="px-3.5 py-1.5 rounded-lg font-medium transition-all"
          :class="filterStatus === 'all' ? 'bg-accent text-black font-semibold shadow' : 'text-gray-400 hover:text-white'"
        >
          Todas ({{ playlists.length }})
        </button>
        <button
          @click="filterStatus = 'not_created'"
          class="px-3.5 py-1.5 rounded-lg font-medium transition-all flex items-center space-x-1"
          :class="filterStatus === 'not_created' ? 'bg-amber-500 text-black font-semibold shadow' : 'text-gray-400 hover:text-white'"
        >
          <AlertCircle class="w-3 h-3" />
          <span>Pendentes</span>
        </button>
        <button
          @click="filterStatus = 'created'"
          class="px-3.5 py-1.5 rounded-lg font-medium transition-all flex items-center space-x-1"
          :class="filterStatus === 'created' ? 'bg-emerald-500 text-black font-semibold shadow' : 'text-gray-400 hover:text-white'"
        >
          <CheckCircle2 class="w-3 h-3" />
          <span>Criadas</span>
        </button>
      </div>
    </div>

    <!-- Playlists List -->
    <div v-if="isLoading" class="py-24 flex flex-col items-center justify-center space-y-3 text-gray-400">
      <Loader2 class="w-8 h-8 animate-spin text-accent" />
      <p class="text-sm">Buscando arquivos M3U nos diretórios de música...</p>
    </div>

    <div v-else-if="filteredPlaylists().length > 0" class="space-y-3">
      <div
        v-for="p in filteredPlaylists()"
        :key="p.filepath"
        class="bg-surface hover:bg-surface-elevated/80 rounded-2xl p-5 border border-white/5 hover:border-white/20 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm"
      >
        <!-- Left: Cover Artwork & Info -->
        <div class="flex items-start space-x-4 min-w-0">
          <!-- Cover Thumbnail -->
          <div class="relative group/cover flex-shrink-0">
            <div
              class="w-14 h-14 rounded-2xl overflow-hidden bg-surface-elevated flex items-center justify-center text-accent border border-white/10 shadow-inner"
            >
              <img
                v-if="p.swing_playlist?.image_url || p.local_cover_url"
                :src="p.swing_playlist?.image_url || p.local_cover_url!"
                :alt="p.name"
                class="w-full h-full object-cover"
              />
              <ListMusic v-else class="w-7 h-7 text-gray-500" />
            </div>

            <!-- Cover Trigger Overlay -->
            <button
              @click="openCoverModal(p)"
              class="absolute inset-0 bg-black/70 opacity-0 group-hover/cover:opacity-100 rounded-2xl flex flex-col items-center justify-center text-white transition-opacity cursor-pointer"
              title="Buscar Foto Online / Alterar Capa desta playlist"
            >
              <Sparkles class="w-4 h-4 text-accent mb-0.5" />
              <span class="text-[9px] font-bold">Capa</span>
            </button>
          </div>

          <!-- Info Text -->
          <div class="min-w-0">
            <div class="flex items-center space-x-2 flex-wrap">
              <h3 class="font-bold text-base text-white truncate">{{ p.name }}</h3>
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                :class="p.is_created_in_swing ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'"
              >
                {{ p.is_created_in_swing ? 'No SwingMusic' : 'Pendente' }}
              </span>
              <span
                v-if="p.swing_playlist?.image"
                class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-purple-500/10 text-purple-300 border border-purple-500/20"
              >
                Com Capa
              </span>
              <span
                v-else-if="p.has_local_cover"
                class="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/20"
                title="Capa .jpg encontrada na pasta da playlist. Será aplicada ao sincronizar."
              >
                Capa Local Detectada
              </span>
            </div>

            <p class="text-xs text-gray-400 font-mono mt-0.5 truncate flex items-center space-x-1">
              <FolderTree class="w-3 h-3 text-gray-500 inline flex-shrink-0" />
              <span class="truncate">{{ p.relative_path }}</span>
            </p>

            <!-- Match rate bar -->
            <div class="mt-2.5 flex items-center space-x-2 text-xs">
              <div class="w-24 h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all"
                  :class="p.match_rate === 100 ? 'bg-emerald-400' : p.match_rate > 50 ? 'bg-accent' : 'bg-amber-400'"
                  :style="{ width: `${p.match_rate}%` }"
                ></div>
              </div>
              <span class="text-gray-300 font-medium">
                {{ p.matched_tracks }} de {{ p.total_tracks }} músicas identificadas ({{ p.match_rate }}%)
              </span>
            </div>
          </div>
        </div>

        <!-- Right: Actions -->
        <div class="flex items-center space-x-2 self-end md:self-center flex-shrink-0">
          <!-- Buscar Foto Online Button -->
          <button
            @click="openCoverModal(p)"
            class="px-3.5 py-2 bg-accent/10 hover:bg-accent/20 text-accent font-semibold text-xs rounded-xl border border-accent/20 flex items-center space-x-1.5 transition-all"
            title="Buscar fotos e capas de playlists online ou fazer upload"
          >
            <Sparkles class="w-3.5 h-3.5" />
            <span>Buscar Foto Online</span>
          </button>

          <button
            @click="selectedM3UPath = p.filepath"
            class="px-3.5 py-2 bg-white/5 hover:bg-white/15 text-white text-xs font-semibold rounded-xl border border-white/10 flex items-center space-x-1.5 transition-all"
          >
            <Eye class="w-3.5 h-3.5" />
            <span>Ver Faixas</span>
          </button>

          <button
            @click="quickCreatePlaylist(p)"
            :disabled="activeCreatingPath === p.filepath || p.matched_tracks === 0"
            class="px-4 py-2 bg-accent text-black font-bold text-xs rounded-xl hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center space-x-1.5 shadow-lg shadow-accent/20"
          >
            <Loader2 v-if="activeCreatingPath === p.filepath" class="w-3.5 h-3.5 animate-spin" />
            <RefreshCw v-else-if="p.is_created_in_swing" class="w-3.5 h-3.5" />
            <Plus v-else class="w-3.5 h-3.5" />
            <span>{{ p.is_created_in_swing ? 'Sincronizar' : 'Criar no SwingMusic' }}</span>
          </button>

          <button
            v-if="p.is_created_in_swing"
            @click="removeSwingPlaylist(p)"
            class="p-2 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all"
            title="Remover do SwingMusic"
          >
            <Trash2 class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="py-20 text-center bg-surface rounded-3xl border border-white/5 space-y-3">
      <ListMusic class="w-12 h-12 text-gray-600 mx-auto mb-2" />
      <h3 class="text-lg font-medium text-gray-300">Nenhum arquivo de Playlist (.m3u) encontrado</h3>
      <p class="text-sm text-gray-500 max-w-md mx-auto">
        Coloque seus arquivos <code>.m3u</code> ou <code>.m3u8</code> dentro da pasta <code>Playlists</code> no seu diretório de músicas e clique em <strong>Escanear Pastas</strong>.
      </p>
    </div>

    <!-- Detail Modal -->
    <M3UDetailModal
      v-if="selectedM3UPath"
      :m3u-path="selectedM3UPath"
      @close="selectedM3UPath = null"
      @created="loadPlaylists"
    />

    <!-- Playlist Cover Modal -->
    <PlaylistCoverModal
      v-if="isCoverModalOpen && selectedCoverPlaylist"
      :playlist="selectedCoverPlaylist"
      @close="isCoverModalOpen = false; selectedCoverPlaylist = null"
      @applied="loadPlaylists"
    />
  </div>
</template>

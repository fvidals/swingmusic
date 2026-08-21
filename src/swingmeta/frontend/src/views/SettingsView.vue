<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
  Settings,
  HardDrive,
  Database,
  Image,
  FileMusic,
  CheckCircle2,
  AlertTriangle,
  Save,
  Globe,
  Loader2,
  RefreshCw,
  Info,
} from 'lucide-vue-next';
import { api } from '../api/client';
import type { SystemStatus } from '../types';

const status = ref<SystemStatus | null>(null);
const isLoading = ref(true);
const isSavingSpotify = ref(false);

const spotifyClientId = ref('');
const spotifyClientSecret = ref('');
const spotifyMsg = ref('');
const spotifyError = ref('');

async function loadStatus() {
  isLoading.value = true;
  try {
    status.value = await api.getSystemStatus();
    if (status.value?.spotify.client_id) {
      spotifyClientId.value = status.value.spotify.client_id;
    }
  } catch (err) {
    console.error('Erro ao carregar status:', err);
  } finally {
    isLoading.value = false;
  }
}

async function saveSpotify() {
  if (!spotifyClientId.value || !spotifyClientSecret.value) {
    spotifyError.value = 'Preencha o Client ID e o Client Secret do Spotify.';
    return;
  }

  isSavingSpotify.value = true;
  spotifyMsg.value = '';
  spotifyError.value = '';

  try {
    const res = await api.saveSpotifyConfig(spotifyClientId.value.trim(), spotifyClientSecret.value.trim());
    spotifyMsg.value = res.message || 'Spotify configurado com sucesso!';
    loadStatus();
  } catch (err: any) {
    spotifyError.value = err.message || 'Erro ao validar credenciais do Spotify.';
  } finally {
    isSavingSpotify.value = false;
  }
}

onMounted(() => {
  loadStatus();
});
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- Header -->
    <div class="bg-gradient-to-b from-surface-elevated/70 to-surface rounded-3xl p-6 sm:p-8 border border-white/5 flex items-center justify-between">
      <div>
        <div class="flex items-center space-x-2 text-accent text-sm font-medium mb-1">
          <Settings class="w-4 h-4" />
          <span>Configuração & Diagnóstico</span>
        </div>
        <h1 class="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          Status do Sistema
        </h1>
        <p class="text-sm text-gray-400 mt-1">
          Verifique o ponto de montagem dos volumes e configure integrações opcionais.
        </p>
      </div>

      <button
        @click="loadStatus"
        :disabled="isLoading"
        class="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all"
      >
        <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isLoading }" />
        <span>Atualizar</span>
      </button>
    </div>

    <!-- Volume Mounts Status -->
    <div class="bg-surface rounded-3xl p-6 sm:p-8 border border-white/5 space-y-6">
      <div class="flex items-center space-x-2">
        <Database class="w-5 h-5 text-accent" />
        <h2 class="text-lg font-bold text-white">Banco de Dados & Armazenamento</h2>
      </div>

      <div v-if="status" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <!-- swingmusic.db -->
        <div class="bg-surface-elevated rounded-2xl p-4 border border-white/5 flex items-start space-x-3.5">
          <div class="p-2.5 rounded-xl bg-white/5 text-gray-300">
            <Database class="w-5 h-5" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sm text-white">swingmusic.db</span>
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center space-x-1"
                :class="status.mounts.swingmusic_db_exists ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'"
              >
                <CheckCircle2 v-if="status.mounts.swingmusic_db_exists" class="w-3 h-3" />
                <AlertTriangle v-else class="w-3 h-3" />
                <span>{{ status.mounts.swingmusic_db_exists ? 'Conectado' : 'Ausente' }}</span>
              </span>
            </div>
            <p class="text-xs text-gray-400 font-mono truncate mt-1">{{ status.paths.swingmusic_db }}</p>
            <p class="text-xs text-gray-500 mt-0.5">{{ status.stats.track_count }} faixas no catálogo</p>
          </div>
        </div>

        <!-- Images Folder -->
        <div class="bg-surface-elevated rounded-2xl p-4 border border-white/5 flex items-start space-x-3.5">
          <div class="p-2.5 rounded-xl bg-white/5 text-gray-300">
            <Image class="w-5 h-5" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-sm text-white">Diretório de Imagens</span>
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center space-x-1"
                :class="status.mounts.images_dir_exists ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'"
              >
                <CheckCircle2 v-if="status.mounts.images_dir_exists" class="w-3 h-3" />
                <AlertTriangle v-else class="w-3 h-3" />
                <span>{{ status.mounts.images_dir_exists ? 'Conectado' : 'Ausente' }}</span>
              </span>
            </div>
            <p class="text-xs text-gray-400 font-mono truncate mt-1">{{ status.paths.images_dir }}</p>
            <p class="text-xs text-gray-500 mt-0.5">{{ status.stats.artist_image_count }} fotos de artistas e capas</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Music & Extra Mount Points -->
    <div class="bg-surface rounded-3xl p-6 sm:p-8 border border-white/5 space-y-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <HardDrive class="w-5 h-5 text-accent" />
          <div>
            <h2 class="text-lg font-bold text-white">Volumes de Músicas & Downloads</h2>
            <p class="text-xs text-gray-400">Pontos de montagem detectados no container para leitura e gravação de tags ID3</p>
          </div>
        </div>
      </div>

      <div v-if="status?.mount_points && status.mount_points.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div
          v-for="mount in status.mount_points"
          :key="mount.path"
          class="bg-surface-elevated rounded-2xl p-4 border border-white/5 flex items-start space-x-3.5"
        >
          <div class="p-2.5 rounded-xl bg-white/5 text-gray-300">
            <FileMusic class="w-5 h-5" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="font-semibold text-sm text-white font-mono">{{ mount.path }}</span>
                <span
                  v-if="mount.is_swing_root"
                  class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-accent/20 text-accent border border-accent/30 uppercase tracking-wide"
                >
                  Fonte SwingMusic
                </span>
              </div>
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center space-x-1"
                :class="mount.exists ? (mount.writable ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-blue-500/10 text-blue-400 border border-blue-500/20') : 'bg-red-500/10 text-red-400 border border-red-500/20'"
              >
                <CheckCircle2 v-if="mount.exists" class="w-3 h-3" />
                <AlertTriangle v-else class="w-3 h-3" />
                <span>{{ mount.exists ? (mount.writable ? 'Montado (Leitura & Escrita)' : 'Somente Leitura') : 'Não Montado no Container' }}</span>
              </span>
            </div>
            <p class="text-xs text-gray-400 truncate mt-1">{{ mount.label }}</p>
            <div class="flex items-center space-x-2 text-xs text-gray-500 mt-1">
              <span v-if="mount.track_count > 0" class="text-accent font-semibold">
                {{ mount.track_count }} faixas no catálogo
              </span>
              <span v-else class="text-gray-500">Nenhuma faixa encontrada</span>
              <span v-if="!mount.exists && mount.is_swing_root" class="text-red-400 font-medium">
                • Adicione este volume ao docker-compose do SwingMeta
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Spotify API Integration (Optional) -->
    <div class="bg-surface rounded-3xl p-6 sm:p-8 border border-white/5 space-y-5">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <Globe class="w-5 h-5 text-[#1DB954]" />
          <h2 class="text-lg font-bold text-white">Integração Opcional: Spotify Developer</h2>
        </div>
        <span
          class="px-2.5 py-0.5 rounded-full text-xs font-semibold"
          :class="status?.spotify.configured ? 'bg-[#1DB954]/10 text-[#1DB954] border border-[#1DB954]/20' : 'bg-white/5 text-gray-400 border border-white/10'"
        >
          {{ status?.spotify.configured ? 'Conectado' : 'Não configurado' }}
        </span>
      </div>

      <div class="p-4 bg-surface-elevated/70 rounded-2xl border border-white/5 flex items-start space-x-3 text-xs text-gray-300">
        <Info class="w-4 h-4 text-accent flex-shrink-0 mt-0.5" />
        <p>
          O Deezer e o MusicBrainz funcionam <strong>automaticamente sem chave</strong>. Se você quiser consultar também fotos oficiais em altíssima qualidade do catálogo do Spotify, crie um aplicativo no <a href="https://developer.spotify.com/dashboard" target="_blank" class="text-accent underline">Spotify Developer Dashboard</a> e informe as credenciais abaixo:
        </p>
      </div>

      <form @submit.prevent="saveSpotify" class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Spotify Client ID</label>
            <input
              v-model="spotifyClientId"
              type="text"
              placeholder="ex: 1a2b3c4d5e6f7g8h9i0j..."
              class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
            />
          </div>
          <div>
            <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Spotify Client Secret</label>
            <input
              v-model="spotifyClientSecret"
              type="password"
              placeholder="ex: a1b2c3d4e5f6..."
              class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
            />
          </div>
        </div>

        <div v-if="spotifyError" class="p-3 bg-red-500/10 border border-red-500/20 text-red-300 rounded-xl text-xs">
          {{ spotifyError }}
        </div>
        <div v-if="spotifyMsg" class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-xl text-xs">
          {{ spotifyMsg }}
        </div>

        <div class="flex justify-end">
          <button
            type="submit"
            :disabled="isSavingSpotify"
            class="px-5 py-2.5 bg-accent text-black font-semibold text-sm rounded-xl hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center space-x-1.5 shadow-lg shadow-accent/20"
          >
            <Loader2 v-if="isSavingSpotify" class="w-4 h-4 animate-spin" />
            <Save v-else class="w-4 h-4" />
            <span>Salvar e Validar Credenciais</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

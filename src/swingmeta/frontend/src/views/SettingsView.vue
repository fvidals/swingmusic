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
  Archive,
  Download,
  Upload,
  Check,
  ShieldCheck,
  FolderTree,
  Tag,
  Sliders,
  Share2,
} from 'lucide-vue-next';
import { api } from '../api/client';
import type { SystemStatus, BackupSummary } from '../types';

const status = ref<SystemStatus | null>(null);
const isLoading = ref(true);
const isSavingSpotify = ref(false);

const spotifyClientId = ref('');
const spotifyClientSecret = ref('');
const spotifyMsg = ref('');
const spotifyError = ref('');

// Backup state
const backupSummary = ref<BackupSummary | null>(null);
const isBackupLoading = ref(false);
const isDownloadingBackup = ref(false);
const isRestoringBackup = ref(false);
const backupMsg = ref('');
const backupError = ref('');
const restoreFileInput = ref<HTMLInputElement | null>(null);

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

async function loadBackupSummary() {
  isBackupLoading.value = true;
  try {
    backupSummary.value = await api.getBackupSummary();
  } catch (err) {
    console.warn('Erro ao carregar resumo de backup:', err);
  } finally {
    isBackupLoading.value = false;
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

async function handleDownloadBackup() {
  isDownloadingBackup.value = true;
  backupMsg.value = '';
  backupError.value = '';
  try {
    const url = api.getBackupDownloadUrl();
    const link = document.createElement('a');
    link.href = url;
    link.download = `swingmusic-backup-${new Date().toISOString().slice(0, 10)}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    backupMsg.value = 'Download do backup (.zip) iniciado com sucesso!';
    setTimeout(() => {
      backupMsg.value = '';
    }, 4000);
  } catch (err: any) {
    backupError.value = 'Falha ao iniciar download do backup.';
  } finally {
    isDownloadingBackup.value = false;
  }
}

async function handleRestoreBackup(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  if (!confirm(`ATENÇÃO: Deseja restaurar o backup "${file.name}"?\n\nOs arquivos de configuração e bancos de dados atuais serão substituídos (um snapshot de segurança automático será salvo antes).`)) {
    target.value = '';
    return;
  }

  isRestoringBackup.value = true;
  backupMsg.value = '';
  backupError.value = '';

  try {
    const res = await api.restoreBackup(file);
    backupMsg.value = res.message || 'Backup restaurado com sucesso!';
    await loadStatus();
    await loadBackupSummary();
  } catch (err: any) {
    backupError.value = err.message || 'Falha ao restaurar backup.';
  } finally {
    isRestoringBackup.value = false;
    target.value = '';
  }
}

// Feature Toggle: Embed Audio Tags
const embedAudioTags = ref(false);
const isUpdatingToggle = ref(false);
const toggleMsg = ref('');

async function loadSettings() {
  try {
    const s = await api.getSettings();
    embedAudioTags.value = s.embed_audio_tags ?? false;
  } catch (err) {
    console.warn('Erro ao carregar configurações:', err);
  }
}

async function handleToggleEmbedAudio() {
  isUpdatingToggle.value = true;
  toggleMsg.value = '';
  try {
    const newVal = !embedAudioTags.value;
    const res = await api.updateSettings({ embed_audio_tags: newVal });
    embedAudioTags.value = res.settings.embed_audio_tags;
    toggleMsg.value = embedAudioTags.value
      ? 'Gravação física de tags em arquivos de áudio ATIVADA.'
      : 'Gravação física de tags DESATIVADA (modo padrão seguro).';
    setTimeout(() => {
      toggleMsg.value = '';
    }, 4000);
  } catch (err: any) {
    console.error('Erro ao atualizar toggle:', err);
  } finally {
    isUpdatingToggle.value = false;
  }
}

function triggerRestoreInput() {
  restoreFileInput.value?.click();
}

onMounted(() => {
  loadStatus();
  loadBackupSummary();
  loadSettings();
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

    <!-- Shared Artist Art Folder (SM_ARTISTARTPRIORITY) -->
    <div class="bg-surface rounded-3xl p-6 sm:p-8 border border-white/5 space-y-4">
      <div class="flex items-center space-x-2">
        <Share2 class="w-5 h-5 text-accent" />
        <div>
          <h2 class="text-lg font-bold text-white">Pasta Compartilhada de Artes de Artistas</h2>
          <p class="text-xs text-gray-400">
            Espelha as fotos de artistas em qualidade máxima (.jpg) para um volume que outros servidores de mídia
            podem consumir de forma somente leitura (ex: Navidrome via <code>ArtistImageFolder</code>).
          </p>
        </div>
      </div>

      <div v-if="status?.shared_artist_art" class="bg-surface-elevated rounded-2xl p-4 border border-white/5 flex items-start space-x-3.5">
        <div class="p-2.5 rounded-xl bg-white/5 text-gray-300">
          <FolderTree class="w-5 h-5" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between">
            <span class="font-semibold text-sm text-white">SM_ARTISTARTPRIORITY</span>
            <span
              class="px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center space-x-1"
              :class="status.shared_artist_art.configured && status.shared_artist_art.exists ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'"
            >
              <CheckCircle2 v-if="status.shared_artist_art.configured && status.shared_artist_art.exists" class="w-3 h-3" />
              <AlertTriangle v-else class="w-3 h-3" />
              <span>{{ status.shared_artist_art.configured ? (status.shared_artist_art.exists ? 'Ativo' : 'Configurado, pasta ausente') : 'Não Configurado' }}</span>
            </span>
          </div>
          <p class="text-xs text-gray-400 font-mono truncate mt-1">{{ status.shared_artist_art.path || 'Defina a variável de ambiente SM_ARTISTARTPRIORITY' }}</p>
          <p v-if="status.shared_artist_art.configured" class="text-xs text-gray-500 mt-0.5">{{ status.shared_artist_art.image_count }} artes exportadas</p>
        </div>
      </div>
    </div>

    <!-- Feature Toggle: Physical Audio Tags Embedding -->
    <div class="bg-surface rounded-3xl p-6 sm:p-8 border border-white/5 space-y-5 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div class="flex items-start space-x-3.5 max-w-2xl">
          <div
            class="w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 transition-colors"
            :class="embedAudioTags ? 'bg-accent/15 text-accent border border-accent/30' : 'bg-white/5 text-gray-400 border border-white/10'"
          >
            <Tag class="w-5 h-5" />
          </div>
          <div>
            <div class="flex items-center space-x-2.5">
              <h2 class="text-lg font-bold text-white">Gravar Tags nos Arquivos de Áudio (ID3 / FLAC)</h2>
              <span
                class="px-2 py-0.5 rounded-full text-[10px] font-bold"
                :class="embedAudioTags ? 'bg-accent/20 text-accent border border-accent/30' : 'bg-white/5 text-gray-400 border border-white/10'"
              >
                {{ embedAudioTags ? 'Ativado' : 'Desativado (Padrão Seguro)' }}
              </span>
            </div>
            <p class="text-xs text-gray-400 mt-1 leading-relaxed">
              O propósito padrão do <strong>SwingMeta</strong> é atualizar o catálogo do <code>swingmusic.db</code> e as miniaturas WebP de capas, sem alterar os arquivos no disco (ideal para pontos de montagem somente leitura <code>:ro</code>).
            </p>
            <p class="text-xs text-gray-500 mt-1">
              Ative esta opção apenas se seus volumes de música tiverem permissão de escrita e você desejar gravar capas e tags ID3 permanentemente dentro dos arquivos de áudio originais.
            </p>
          </div>
        </div>

        <!-- Custom Switch Toggle -->
        <button
          type="button"
          @click="handleToggleEmbedAudio"
          :disabled="isUpdatingToggle"
          class="relative inline-flex h-7 w-12 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none disabled:opacity-50 self-start sm:self-center"
          :class="embedAudioTags ? 'bg-accent' : 'bg-surface-elevated border-white/10'"
          role="switch"
          :aria-checked="embedAudioTags"
        >
          <span
            aria-hidden="true"
            class="pointer-events-none inline-block h-6 w-6 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"
            :class="embedAudioTags ? 'translate-x-5 !bg-black' : 'translate-x-0 !bg-gray-400'"
          />
        </button>
      </div>

      <div v-if="toggleMsg" class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-xl text-xs flex items-center space-x-2">
        <Check class="w-4 h-4 text-emerald-400 flex-shrink-0" />
        <span>{{ toggleMsg }}</span>
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

    <!-- Backup & Restore Section -->
    <div class="bg-surface rounded-3xl p-6 sm:p-8 border border-white/5 space-y-6 shadow-sm">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent flex-shrink-0">
            <Archive class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-white">Backup & Restauração da Configuração</h2>
            <p class="text-xs text-gray-400">
              Exporte todos os bancos de dados catalogados, fotos de artistas, capas e configurações em um arquivo <code>.zip</code>.
            </p>
          </div>
        </div>

        <button
          @click="loadBackupSummary"
          :disabled="isBackupLoading"
          class="px-3 py-1.5 bg-white/5 hover:bg-white/10 text-white rounded-xl text-xs font-semibold flex items-center space-x-1.5 self-start sm:self-auto transition-all"
        >
          <RefreshCw class="w-3.5 h-3.5" :class="{ 'animate-spin': isBackupLoading }" />
          <span>Atualizar Tamanho</span>
        </button>
      </div>

      <!-- Backup Stats Grid -->
      <div v-if="backupSummary" class="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div class="bg-surface-elevated/70 p-4 rounded-2xl border border-white/5">
          <span class="text-[11px] text-gray-400 font-medium">Tamanho Total</span>
          <p class="text-base font-bold text-accent mt-1">
            {{ backupSummary.total_size_mb }} MB
          </p>
          <span class="text-[10px] text-gray-500">{{ backupSummary.total_files }} arquivos no volume</span>
        </div>

        <div class="bg-surface-elevated/70 p-4 rounded-2xl border border-white/5">
          <span class="text-[11px] text-gray-400 font-medium">Bancos de Dados</span>
          <p class="text-base font-bold text-white mt-1">
            {{ backupSummary.database_count }} SQLite
          </p>
          <span class="text-[10px] text-gray-500 font-mono">swingmusic.db / user</span>
        </div>

        <div class="bg-surface-elevated/70 p-4 rounded-2xl border border-white/5">
          <span class="text-[11px] text-gray-400 font-medium">Imagens & Capas</span>
          <p class="text-base font-bold text-white mt-1">
            {{ backupSummary.image_count }} fotos
          </p>
          <span class="text-[10px] text-gray-500">{{ backupSummary.images_size_mb }} MB em WebP</span>
        </div>

        <div class="bg-surface-elevated/70 p-4 rounded-2xl border border-white/5">
          <span class="text-[11px] text-gray-400 font-medium">Pasta Fonte</span>
          <p class="text-xs font-mono text-gray-300 mt-1.5 truncate" :title="backupSummary.config_dir">
            {{ backupSummary.config_dir }}
          </p>
          <span class="text-[10px] text-emerald-400 flex items-center space-x-1 mt-0.5">
            <Check class="w-3 h-3" />
            <span>Pronto p/ Exportar</span>
          </span>
        </div>
      </div>

      <!-- Action Feedback Alerts -->
      <div v-if="backupMsg" class="p-3.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-2xl text-xs flex items-center space-x-2">
        <Check class="w-4 h-4 text-emerald-400 flex-shrink-0" />
        <span>{{ backupMsg }}</span>
      </div>

      <div v-if="backupError" class="p-3.5 bg-red-500/10 border border-red-500/20 text-red-300 rounded-2xl text-xs flex items-center space-x-2">
        <AlertTriangle class="w-4 h-4 text-red-400 flex-shrink-0" />
        <span>{{ backupError }}</span>
      </div>

      <!-- Actions Buttons Bar -->
      <div class="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 border-t border-white/5">
        <div class="text-xs text-gray-400 flex items-center space-x-2">
          <ShieldCheck class="w-4 h-4 text-accent flex-shrink-0" />
          <span>Ao restaurar, um snapshot de segurança (<code>.bak</code>) é gerado automaticamente antes da substituição.</span>
        </div>

        <div class="flex items-center space-x-3 flex-shrink-0">
          <!-- Restore Input Hidden -->
          <input
            ref="restoreFileInput"
            type="file"
            accept=".zip,application/zip"
            class="hidden"
            @change="handleRestoreBackup"
          />

          <button
            @click="triggerRestoreInput"
            :disabled="isRestoringBackup"
            class="px-4 py-2.5 bg-white/5 hover:bg-white/15 text-white text-xs font-semibold rounded-xl border border-white/10 flex items-center justify-center space-x-2 transition-all disabled:opacity-50"
            title="Restaurar backup .zip anterior"
          >
            <Loader2 v-if="isRestoringBackup" class="w-4 h-4 animate-spin" />
            <Upload v-else class="w-4 h-4 text-accent" />
            <span>{{ isRestoringBackup ? 'Restaurando...' : 'Restaurar Backup (.zip)' }}</span>
          </button>

          <button
            @click="handleDownloadBackup"
            :disabled="isDownloadingBackup || !backupSummary?.exists"
            class="px-5 py-2.5 bg-accent text-black font-bold text-xs rounded-xl hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center justify-center space-x-2 shadow-lg shadow-accent/20"
            title="Fazer download completo da pasta de configuração do SwingMusic"
          >
            <Loader2 v-if="isDownloadingBackup" class="w-4 h-4 animate-spin" />
            <Download v-else class="w-4 h-4" />
            <span>{{ isDownloadingBackup ? 'Gerando ZIP...' : 'Baixar Backup Completo (.zip)' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

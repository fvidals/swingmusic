<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { X, ListMusic, CheckCircle2, AlertCircle, Plus, RefreshCw, Loader2, Music, Check } from 'lucide-vue-next';
import { api } from '../api/client';
import type { M3UDetail, M3UTrackItem } from '../types';

const props = defineProps<{
  m3uPath: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'created'): void;
}>();

const detail = ref<M3UDetail | null>(null);
const isLoading = ref(true);
const isCreating = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

async function loadDetail() {
  isLoading.value = true;
  errorMsg.value = '';
  try {
    detail.value = await api.getPlaylistDetail(props.m3uPath);
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao ler arquivo M3U';
  } finally {
    isLoading.value = false;
  }
}

async function createPlaylist() {
  if (!detail.value) return;
  isCreating.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  try {
    const res = await api.createPlaylist(detail.value.filepath, detail.value.name);
    successMsg.value = `Playlist "${detail.value.name}" ${res.action === 'updated' ? 'sincronizada' : 'criada'} com sucesso no SwingMusic com ${res.imported_tracks} músicas!`;
    detail.value.is_created = true;
    emit('created');
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao criar playlist no SwingMusic';
  } finally {
    isCreating.value = false;
  }
}

function formatDuration(seconds: number): string {
  if (!seconds) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

onMounted(() => {
  loadDetail();
});
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
    <div class="bg-surface rounded-3xl border border-white/10 w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="p-6 border-b border-white/10 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-xl bg-accent/10 border border-accent/20 flex items-center justify-center text-accent">
            <ListMusic class="w-5 h-5" />
          </div>
          <div>
            <h2 class="text-lg font-bold text-white flex items-center space-x-2">
              <span>{{ detail?.name || 'Detalhes da Playlist' }}</span>
              <span
                v-if="detail"
                class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                :class="detail.is_created ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'"
              >
                {{ detail.is_created ? 'Criada no SwingMusic' : 'Não criada' }}
              </span>
            </h2>
            <p v-if="detail" class="text-xs text-gray-400 font-mono mt-0.5 truncate max-w-md">
              {{ detail.filepath }}
            </p>
          </div>
        </div>

        <button
          @click="emit('close')"
          class="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Match summary banner -->
      <div v-if="detail" class="px-6 py-3.5 bg-surface-elevated/60 border-b border-white/5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div class="flex items-center space-x-4">
          <span class="text-gray-300">
            Total no M3U: <strong class="text-white">{{ detail.total_tracks }}</strong>
          </span>
          <span class="text-emerald-400 flex items-center space-x-1">
            <CheckCircle2 class="w-3.5 h-3.5" />
            <span>Encontradas no SwingMusic: <strong>{{ detail.matched_count }}</strong></span>
          </span>
          <span v-if="detail.total_tracks - detail.matched_count > 0" class="text-amber-400 flex items-center space-x-1">
            <AlertCircle class="w-3.5 h-3.5" />
            <span>Não encontradas: <strong>{{ detail.total_tracks - detail.matched_count }}</strong></span>
          </span>
        </div>

        <button
          @click="createPlaylist"
          :disabled="isCreating || detail.matched_count === 0"
          class="px-4 py-2 bg-accent text-black font-bold text-xs rounded-xl hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center space-x-1.5 shadow-lg shadow-accent/20"
        >
          <Loader2 v-if="isCreating" class="w-3.5 h-3.5 animate-spin" />
          <RefreshCw v-else-if="detail.is_created" class="w-3.5 h-3.5" />
          <Plus v-else class="w-3.5 h-3.5" />
          <span>{{ isCreating ? 'Processando...' : detail.is_created ? 'Sincronizar no SwingMusic' : 'Criar no SwingMusic' }}</span>
        </button>
      </div>

      <!-- Content / Track List -->
      <div class="p-6 overflow-y-auto flex-1 space-y-4">
        <div v-if="isLoading" class="py-20 flex flex-col items-center justify-center space-y-3 text-gray-400">
          <Loader2 class="w-8 h-8 animate-spin text-accent" />
          <p class="text-sm">Analisando caminhos e faixas do M3U...</p>
        </div>

        <div v-else-if="errorMsg" class="p-4 bg-red-500/10 border border-red-500/20 text-red-300 rounded-xl text-xs">
          {{ errorMsg }}
        </div>

        <div v-if="successMsg" class="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-xl text-xs flex items-center space-x-2">
          <Check class="w-4 h-4 text-emerald-400" />
          <span>{{ successMsg }}</span>
        </div>

        <!-- Tracks list -->
        <div v-if="detail && detail.tracks.length > 0" class="space-y-2">
          <div
            v-for="(t, idx) in detail.tracks"
            :key="idx"
            class="p-3.5 bg-surface-elevated/70 rounded-2xl border flex items-center justify-between gap-3 text-xs transition-all"
            :class="t.matched ? 'border-white/5 hover:border-white/20' : 'border-amber-500/20 bg-amber-500/5'"
          >
            <div class="flex items-center space-x-3 min-w-0">
              <span class="text-gray-500 font-mono w-6 text-right flex-shrink-0">{{ idx + 1 }}</span>
              <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" :class="t.matched ? 'bg-accent/10 text-accent' : 'bg-amber-500/10 text-amber-400'">
                <Music class="w-4 h-4" />
              </div>
              <div class="min-w-0">
                <p class="font-medium text-white truncate text-sm">
                  {{ t.matched ? t.db_title : t.title }}
                </p>
                <p class="text-gray-400 truncate mt-0.5">
                  <span v-if="t.matched && t.db_artists">{{ t.db_artists }} • {{ t.db_album }}</span>
                  <span v-else class="font-mono text-[11px] text-gray-500">{{ t.raw_path }}</span>
                </p>
              </div>
            </div>

            <div class="flex items-center space-x-3 flex-shrink-0">
              <span v-if="t.matched && t.db_duration" class="text-gray-400 font-mono">
                {{ formatDuration(t.db_duration) }}
              </span>
              <span
                class="px-2.5 py-1 rounded-full text-[11px] font-semibold flex items-center space-x-1"
                :class="t.matched ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'"
              >
                <CheckCircle2 v-if="t.matched" class="w-3 h-3" />
                <AlertCircle v-else class="w-3 h-3" />
                <span>{{ t.matched ? 'Identificada' : 'Não localizada' }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-white/10 bg-surface-elevated/40 flex justify-end">
        <button
          @click="emit('close')"
          class="px-5 py-2.5 bg-white/10 hover:bg-white/20 text-white text-sm font-medium rounded-xl transition-all"
        >
          Fechar
        </button>
      </div>
    </div>
  </div>
</template>

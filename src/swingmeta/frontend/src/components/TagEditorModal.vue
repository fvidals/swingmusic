<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { X, Save, Check, Loader2, Music, FileAudio, Disc } from 'lucide-vue-next';
import { api } from '../api/client';
import type { Track, FileTags } from '../types';

const props = defineProps<{
  track: Track;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'updated', updatedTags: any): void;
}>();

const isLoading = ref(true);
const isSaving = ref(false);
const errorMsg = ref('');
const successMsg = ref('');

const formData = ref<{
  title: string;
  artist: string;
  album: string;
  albumartist: string;
  year: string;
  tracknumber: string;
  genre: string;
}>({
  title: props.track.title || '',
  artist: '',
  album: props.track.album || '',
  albumartist: '',
  year: props.track.date ? String(props.track.date) : '',
  tracknumber: props.track.track ? String(props.track.track) : '',
  genre: props.track.genres || '',
});

const fileInfo = ref<{ filename: string; format: string; filepath: string } | null>(null);

onMounted(async () => {
  try {
    const detail = await api.getTrackDetail(props.track.id);
    if (detail.file_tags) {
      fileInfo.value = {
        filename: detail.file_tags.filename,
        format: detail.file_tags.format,
        filepath: detail.file_tags.filepath,
      };
      formData.value = {
        title: detail.file_tags.title || props.track.title || '',
        artist: detail.file_tags.artist || '',
        album: detail.file_tags.album || props.track.album || '',
        albumartist: detail.file_tags.albumartist || '',
        year: detail.file_tags.year || (props.track.date ? String(props.track.date) : ''),
        tracknumber: detail.file_tags.tracknumber || (props.track.track ? String(props.track.track) : ''),
        genre: detail.file_tags.genre || props.track.genres || '',
      };
    }
  } catch (err: any) {
    errorMsg.value = 'Aviso: Não foi possível ler tags diretamente do arquivo de áudio.';
  } finally {
    isLoading.value = false;
  }
});

async function saveTags() {
  isSaving.value = true;
  errorMsg.value = '';
  successMsg.value = '';

  try {
    const result = await api.updateTrackTags(props.track.id, formData.value);
    successMsg.value = 'Tags ID3 salvas no arquivo e sincronizadas com o banco!';
    emit('updated', formData.value);
    setTimeout(() => {
      emit('close');
    }, 1500);
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao gravar tags no arquivo de áudio.';
  } finally {
    isSaving.value = false;
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
    <div class="bg-surface rounded-2xl border border-white/10 w-full max-w-xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="p-5 border-b border-white/10 flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <Music class="w-5 h-5 text-accent" />
          <h2 class="text-lg font-semibold text-white">Editar Tags de Áudio (ID3)</h2>
        </div>
        <button
          @click="emit('close')"
          class="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- File info badge -->
      <div v-if="fileInfo" class="px-5 py-3 bg-surface-elevated/60 border-b border-white/5 flex items-center space-x-3 text-xs text-gray-400">
        <FileAudio class="w-4 h-4 text-emerald-400 flex-shrink-0" />
        <span class="truncate font-mono text-gray-300">{{ fileInfo.filename }}</span>
        <span class="px-1.5 py-0.5 uppercase font-bold text-[10px] bg-white/10 text-gray-300 rounded">
          {{ fileInfo.format }}
        </span>
      </div>

      <!-- Form Body -->
      <div class="p-5 overflow-y-auto flex-1 space-y-4">
        <div v-if="isLoading" class="py-12 flex items-center justify-center space-y-2 text-gray-400">
          <Loader2 class="w-6 h-6 animate-spin text-accent" />
        </div>

        <template v-else>
          <!-- Title -->
          <div>
            <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Título da Faixa</label>
            <input
              v-model="formData.title"
              type="text"
              class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
            />
          </div>

          <!-- Artist & Album Artist -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Artista(s)</label>
              <input
                v-model="formData.artist"
                type="text"
                placeholder="Ex: Queen, David Bowie"
                class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Artista do Álbum</label>
              <input
                v-model="formData.albumartist"
                type="text"
                placeholder="Ex: Queen"
                class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
              />
            </div>
          </div>

          <!-- Album -->
          <div>
            <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Álbum</label>
            <input
              v-model="formData.album"
              type="text"
              class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
            />
          </div>

          <!-- Year, Track Number, Genre -->
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Ano</label>
              <input
                v-model="formData.year"
                type="text"
                placeholder="2024"
                class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Faixa Nº</label>
              <input
                v-model="formData.tracknumber"
                type="text"
                placeholder="1"
                class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1.5">Gênero</label>
              <input
                v-model="formData.genre"
                type="text"
                placeholder="Rock"
                class="w-full bg-surface-elevated border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-accent"
              />
            </div>
          </div>

          <div v-if="errorMsg" class="p-3 bg-red-500/10 border border-red-500/20 text-red-300 rounded-xl text-xs">
            {{ errorMsg }}
          </div>
          <div v-if="successMsg" class="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-xl text-xs">
            {{ successMsg }}
          </div>
        </template>
      </div>

      <!-- Footer -->
      <div class="p-4 border-t border-white/10 bg-surface-elevated/40 flex justify-end space-x-2">
        <button
          @click="emit('close')"
          class="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-sm font-medium rounded-xl transition-all"
        >
          Cancelar
        </button>
        <button
          @click="saveTags"
          :disabled="isSaving || isLoading"
          class="px-5 py-2 bg-accent text-black font-semibold text-sm rounded-xl hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center space-x-1.5 shadow-lg shadow-accent/20"
        >
          <Loader2 v-if="isSaving" class="w-4 h-4 animate-spin" />
          <Save v-else class="w-4 h-4" />
          <span>{{ isSaving ? 'Gravando no arquivo...' : 'Salvar Tags' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

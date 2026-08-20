<script setup lang="ts">
import { ref, watch } from 'vue';
import { FileText, Save, Check, Loader2 } from 'lucide-vue-next';
import { api } from '../api/client';

const props = defineProps<{
  artisthash: string;
  initialBio?: string;
}>();

const emit = defineEmits<{
  (e: 'saved', newBio: string): void;
}>();

const bioText = ref(props.initialBio || '');
const isSaving = ref(false);
const showSuccess = ref(false);
const errorMsg = ref('');

watch(() => props.initialBio, (val) => {
  bioText.value = val || '';
});

async function saveBio() {
  isSaving.value = true;
  errorMsg.value = '';
  showSuccess.value = false;

  try {
    await api.updateArtistMetadata(props.artisthash, { bio: bioText.value });
    showSuccess.value = true;
    emit('saved', bioText.value);
    setTimeout(() => {
      showSuccess.value = false;
    }, 3000);
  } catch (err: any) {
    errorMsg.value = err.message || 'Erro ao salvar biografia';
  } finally {
    isSaving.value = false;
  }
}
</script>

<template>
  <div class="bg-surface rounded-2xl p-5 border border-white/5 space-y-4">
    <div class="flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <FileText class="w-5 h-5 text-accent" />
        <h3 class="font-semibold text-white text-base">Biografia do Artista</h3>
      </div>
      <button
        @click="saveBio"
        :disabled="isSaving"
        class="px-4 py-2 bg-accent text-black font-semibold text-xs rounded-xl hover:bg-accent/90 disabled:opacity-50 transition-all flex items-center space-x-1.5 shadow-md shadow-accent/20"
      >
        <Loader2 v-if="isSaving" class="w-3.5 h-3.5 animate-spin" />
        <Check v-else-if="showSuccess" class="w-3.5 h-3.5" />
        <Save v-else class="w-3.5 h-3.5" />
        <span>{{ isSaving ? 'Salvando...' : showSuccess ? 'Salvo!' : 'Salvar Biografia' }}</span>
      </button>
    </div>

    <p class="text-xs text-gray-400">
      Adicione a história, influências ou notas sobre este artista. O texto será salvo no banco <code>userdata.db</code>.
    </p>

    <textarea
      v-model="bioText"
      rows="6"
      placeholder="Escreva ou cole a biografia do artista aqui..."
      class="w-full bg-surface-elevated border border-white/10 rounded-xl p-4 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent resize-y transition-colors leading-relaxed"
    ></textarea>

    <div v-if="errorMsg" class="p-3 bg-red-500/10 border border-red-500/20 text-red-300 rounded-lg text-xs">
      {{ errorMsg }}
    </div>
  </div>
</template>

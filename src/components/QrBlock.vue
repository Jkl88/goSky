<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import QRCode from 'qrcode';

const props = defineProps<{
  value: string;
  size?: number;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);

async function render() {
  if (!canvasRef.value || !props.value) return;
  await QRCode.toCanvas(canvasRef.value, props.value, {
    width: props.size ?? 220,
    margin: 2,
    color: { dark: '#0f172a', light: '#ffffff' },
  });
}

onMounted(render);
watch(() => props.value, render);
</script>

<template>
  <div class="qr-wrap">
    <canvas ref="canvasRef" />
  </div>
</template>

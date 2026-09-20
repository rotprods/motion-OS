const writeAscii = (view: DataView, offset: number, value: string) => {
  for (let i = 0; i < value.length; i++) {
    view.setUint8(offset + i, value.charCodeAt(i));
  }
};

const bytesToBase64 = (bytes: Uint8Array): string => {
  let binary = '';
  const chunkSize = 0x4000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    const chunk = bytes.subarray(offset, Math.min(bytes.length, offset + chunkSize));
    for (let i = 0; i < chunk.length; i++) binary += String.fromCharCode(chunk[i]);
  }
  return globalThis.btoa(binary);
};

/** Deterministic synthesized impact/sub hit. No binary media is committed to Git. */
export const makeProceduralImpactDataUri = (): string => {
  const sampleRate = 44100;
  const durationSeconds = 0.42;
  const sampleCount = Math.round(sampleRate * durationSeconds);
  const bytesPerSample = 2;
  const dataSize = sampleCount * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataSize);
  const view = new DataView(buffer);

  writeAscii(view, 0, 'RIFF');
  view.setUint32(4, 36 + dataSize, true);
  writeAscii(view, 8, 'WAVE');
  writeAscii(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * bytesPerSample, true);
  view.setUint16(32, bytesPerSample, true);
  view.setUint16(34, 16, true);
  writeAscii(view, 36, 'data');
  view.setUint32(40, dataSize, true);

  let seed = 0x5f04c1e;
  const nextNoise = () => {
    seed = (Math.imul(1664525, seed) + 1013904223) >>> 0;
    return (seed / 0xffffffff) * 2 - 1;
  };

  for (let i = 0; i < sampleCount; i++) {
    const t = i / sampleRate;
    const transient = nextNoise() * Math.exp(-52 * t) * 0.25;
    const sub = Math.sin(2 * Math.PI * 63 * t) * Math.exp(-8.2 * t) * 0.68;
    const body = Math.sin(2 * Math.PI * 126 * t + 0.4) * Math.exp(-13 * t) * 0.16;
    const preWhoosh = t < 0.085 ? nextNoise() * Math.sin(Math.PI * t / 0.085) * 0.055 : 0;
    const sample = Math.max(-1, Math.min(1, transient + sub + body + preWhoosh));
    view.setInt16(44 + i * 2, Math.round(sample * 32767), true);
  }

  return `data:audio/wav;base64,${bytesToBase64(new Uint8Array(buffer))}`;
};

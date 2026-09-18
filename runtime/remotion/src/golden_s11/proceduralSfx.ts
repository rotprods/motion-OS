const writeAscii = (view: DataView, offset: number, value: string) => {
  for (let i = 0; i < value.length; i++) view.setUint8(offset + i, value.charCodeAt(i));
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

/** Deterministic synthetic UI hit. Timing is structural evidence; sound identity is not source authority. */
export const makeUiHitDataUri = (seedInput: number, pitchHz = 620): string => {
  const sampleRate = 44100;
  const durationSeconds = 0.14;
  const sampleCount = Math.round(sampleRate * durationSeconds);
  const dataSize = sampleCount * 2;
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
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeAscii(view, 36, 'data');
  view.setUint32(40, dataSize, true);

  let seed = seedInput >>> 0;
  const noise = () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return (seed / 0xffffffff) * 2 - 1;
  };
  for (let i = 0; i < sampleCount; i++) {
    const t = i / sampleRate;
    const click = noise() * Math.exp(-75 * t) * 0.22;
    const tone = Math.sin(2 * Math.PI * pitchHz * t) * Math.exp(-30 * t) * 0.38;
    const low = Math.sin(2 * Math.PI * 92 * t) * Math.exp(-24 * t) * 0.12;
    const sample = Math.max(-1, Math.min(1, click + tone + low));
    view.setInt16(44 + i * 2, Math.round(sample * 32767), true);
  }
  return `data:audio/wav;base64,${bytesToBase64(new Uint8Array(buffer))}`;
};

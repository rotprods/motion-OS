export type MeasuredBox = {
  x: number;
  y: number;
  width: number;
  height: number;
  opacity: number;
};

type TrackKeyframe = MeasuredBox & {frame: number};

const SETUP_TRACK: TrackKeyframe[] = [
  {frame: 0, x: 96, y: 559, width: 45, height: 21, opacity: 1},
  {frame: 4, x: 96, y: 559, width: 45, height: 21, opacity: 1},
  {frame: 5, x: 96, y: 559, width: 100, height: 21, opacity: 1},
  {frame: 10, x: 94, y: 562, width: 101, height: 21, opacity: 1},
  {frame: 11, x: 92, y: 565, width: 102, height: 21, opacity: 1},
  {frame: 15, x: 79, y: 580, width: 110, height: 23, opacity: 1},
  {frame: 20, x: 69, y: 592, width: 115, height: 24, opacity: 1},
  {frame: 25, x: 64, y: 598, width: 118, height: 24, opacity: 1},
  {frame: 30, x: 60, y: 602, width: 121, height: 25, opacity: 1},
  {frame: 38, x: 58, y: 605, width: 122, height: 25, opacity: 1},
  {frame: 50, x: 57, y: 606, width: 122, height: 25, opacity: 1},
  {frame: 60, x: 56, y: 606, width: 123, height: 25, opacity: 1},
  {frame: 64, x: 62, y: 600, width: 119, height: 25, opacity: 1},
  {frame: 65, x: 67, y: 595, width: 116, height: 24, opacity: 1},
  {frame: 66, x: 75, y: 588, width: 111, height: 23, opacity: 1},
  {frame: 67, x: 86, y: 578, width: 104, height: 22, opacity: 1},
  {frame: 68, x: 86, y: 578, width: 104, height: 22, opacity: 1},
];

const HERO_TRACK: TrackKeyframe[] = [
  {frame: 10, x: 96, y: 580, width: 110, height: 12, opacity: 0.32},
  {frame: 11, x: 92, y: 577, width: 354, height: 51, opacity: 1},
  {frame: 12, x: 89, y: 578, width: 359, height: 56, opacity: 1},
  {frame: 14, x: 82, y: 582, width: 374, height: 62, opacity: 1},
  {frame: 15, x: 79, y: 587, width: 381, height: 63, opacity: 1},
  {frame: 17, x: 73, y: 590, width: 393, height: 68, opacity: 1},
  {frame: 20, x: 69, y: 590, width: 401, height: 74, opacity: 1},
  {frame: 25, x: 64, y: 591, width: 410, height: 81, opacity: 1},
  {frame: 30, x: 60, y: 592, width: 418, height: 86, opacity: 1},
  {frame: 38, x: 58, y: 592, width: 422, height: 88, opacity: 1},
  {frame: 50, x: 57, y: 593, width: 423, height: 89, opacity: 1},
  {frame: 60, x: 56, y: 590, width: 424, height: 92, opacity: 1},
  {frame: 64, x: 62, y: 588, width: 412, height: 88, opacity: 1},
  {frame: 65, x: 68, y: 589, width: 400, height: 79, opacity: 1},
  {frame: 66, x: 75, y: 586, width: 385, height: 72, opacity: 1},
  {frame: 67, x: 86, y: 586, width: 364, height: 60, opacity: 1},
  {frame: 68, x: 86, y: 586, width: 364, height: 60, opacity: 1},
];

const TAIL_TRACK: TrackKeyframe[] = [
  {frame: 38, x: 333, y: 685, width: 146, height: 33, opacity: 1},
  {frame: 43, x: 333, y: 686, width: 147, height: 33, opacity: 1},
  {frame: 50, x: 332, y: 687, width: 148, height: 33, opacity: 1},
  {frame: 60, x: 332, y: 687, width: 147, height: 32, opacity: 1},
  {frame: 64, x: 330, y: 680, width: 144, height: 31, opacity: 1},
  {frame: 65, x: 328, y: 673, width: 140, height: 31, opacity: 1},
  {frame: 66, x: 325, y: 663, width: 135, height: 30, opacity: 1},
  {frame: 67, x: 321, y: 649, width: 128, height: 28, opacity: 1},
  {frame: 68, x: 321, y: 649, width: 128, height: 28, opacity: 1},
];

const lerp = (a: number, b: number, progress: number) => a + (b - a) * progress;

const sample = (frame: number, track: TrackKeyframe[]): MeasuredBox | null => {
  if (frame < track[0].frame || frame > track[track.length - 1].frame) return null;
  const exact = track.find((item) => item.frame === frame);
  if (exact) return exact;
  const rightIndex = track.findIndex((item) => item.frame > frame);
  const left = track[rightIndex - 1];
  const right = track[rightIndex];
  const progress = (frame - left.frame) / (right.frame - left.frame);
  return {
    x: lerp(left.x, right.x, progress),
    y: lerp(left.y, right.y, progress),
    width: lerp(left.width, right.width, progress),
    height: lerp(left.height, right.height, progress),
    opacity: lerp(left.opacity, right.opacity, progress),
  };
};

export const measuredS04Layout = (frame: number) => ({
  setup: sample(frame, SETUP_TRACK),
  hero: sample(frame, HERO_TRACK),
  tail: sample(frame, TAIL_TRACK),
});

export const S04_MEASURED_TRACK_SUMMARY = {
  method: 'REFERENCE_MINUS_INPAINTED_CLEAN_PLATE_COLOR_COMPONENT_BBOX',
  authority: 'MEASURED_HEURISTIC',
  setupFrames: [0, 68],
  heroFrames: [10, 68],
  tailFrames: [38, 68],
  sourceCutToPhoneFrame: 69,
} as const;

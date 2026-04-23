/**
 * 静止画 + zoompanモーション再現。MVPは3種:
 *   - ultra_slow_zoom_in : 1.0 → 1.3 を全長で線形ズーム
 *   - static_no_motion   : 1.0 固定
 *   - flash_cut_zoom     : 1/3 静止 → 1/3 で 1.0→1.4 急加速 → 1/3 で 1.4 ホールド
 *
 * 元実装: video-ai/fv_studio/app.py:1831 _build_motion_filter (ffmpeg zoompan)
 */
import React from "react";
import { AbsoluteFill, Img, interpolate, useCurrentFrame } from "remotion";

export type MotionType =
  | "ultra_slow_zoom_in"
  | "static_no_motion"
  | "flash_cut_zoom";

type Props = {
  src: string;
  motion: MotionType;
  durationFrames: number;
};

const computeScale = (
  motion: MotionType,
  frame: number,
  duration: number,
): number => {
  switch (motion) {
    case "static_no_motion":
      return 1.0;
    case "ultra_slow_zoom_in":
      return interpolate(frame, [0, duration], [1.0, 1.3], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
    case "flash_cut_zoom": {
      const third = duration / 3;
      if (frame < third) return 1.0;
      if (frame < third * 2) {
        return interpolate(frame, [third, third * 2], [1.0, 1.4], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
      }
      return 1.4;
    }
    default:
      return 1.0;
  }
};

export const MotionImage: React.FC<Props> = ({ src, motion, durationFrames }) => {
  const frame = useCurrentFrame();
  const scale = computeScale(motion, frame, durationFrames);

  return (
    <AbsoluteFill style={{ overflow: "hidden", backgroundColor: "#000" }}>
      <Img
        src={src}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${scale})`,
          transformOrigin: "center center",
        }}
      />
    </AbsoluteFill>
  );
};

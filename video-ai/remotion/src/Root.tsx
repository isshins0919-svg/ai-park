/**
 * Remotion Root — こすりちゃんFV動画のルート。
 *
 * CompositionSpec は Python 側 (remotion_bridge.py) が
 * `npx remotion render ... --props=/abs/path/composition.json` で渡す。
 * ルート側では Remotion の inputProps として受け取る。
 */
import React from "react";
import {
  Composition,
  AbsoluteFill,
  Audio,
  Sequence,
  getInputProps,
  staticFile,
} from "remotion";
import { MotionImage, MotionType } from "./MotionImage";
import { CaptionLayer, CaptionLayerSpec } from "./CaptionLayer";

type CaptionWindow = {
  start: number;
  end: number;
  layers: CaptionLayerSpec[];
};

export type CompositionSpec = {
  fps: number;
  width: number;
  height: number;
  image: string;
  audio?: string;
  duration_sec: number;
  motion: MotionType;
  captions: CaptionWindow[];
};

const DEFAULT_SPEC: CompositionSpec = {
  fps: 30,
  width: 1080,
  height: 1920,
  image: "",
  duration_sec: 3.0,
  motion: "static_no_motion",
  captions: [
    {
      start: 0.0,
      end: 3.0,
      layers: [
        {
          text: "サンプル (inputProps未指定)",
          placement: "kick_bottom",
          size: "xl",
          style: "double_stroke",
          emphasis_words: [],
        },
      ],
    },
  ],
};

// 絶対パスやhttp(s) URLはそのまま、それ以外は public/ 配下としてstaticFile化
const resolveAsset = (p: string | undefined): string | undefined => {
  if (!p) return undefined;
  if (/^https?:\/\//i.test(p) || p.startsWith("/") || /^[a-zA-Z]:\\/.test(p)) return p;
  return staticFile(p);
};

// CLI の --props で渡される JSON を吸い上げる。不足フィールドは DEFAULT_SPEC から補完。
const rawInput = getInputProps() as Partial<CompositionSpec>;
const merged: CompositionSpec = { ...DEFAULT_SPEC, ...rawInput };
const spec: CompositionSpec = {
  ...merged,
  image: resolveAsset(merged.image) ?? "",
  audio: resolveAsset(merged.audio),
};
const totalFrames = Math.max(1, Math.round(spec.duration_sec * spec.fps));

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="KosuriFV"
      component={KosuriFVComposition}
      durationInFrames={totalFrames}
      fps={spec.fps}
      width={spec.width}
      height={spec.height}
      defaultProps={{ spec }}
    />
  );
};

type CompProps = { spec: CompositionSpec };

const KosuriFVComposition: React.FC<CompProps> = ({ spec }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* 1) 静止画 + モーション (裏層) */}
      {spec.image && (
        <MotionImage
          src={spec.image}
          motion={spec.motion}
          durationFrames={Math.max(1, Math.round(spec.duration_sec * spec.fps))}
        />
      )}

      {/* 2) テロップは時間窓ごとに独立Sequence */}
      {spec.captions.map((win, i) => {
        const from = Math.max(0, Math.round(win.start * spec.fps));
        const to = Math.round(win.end * spec.fps);
        const dur = Math.max(1, to - from);
        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            <AbsoluteFill style={{ pointerEvents: "none" }}>
              {win.layers.map((layer, j) => (
                <CaptionLayer key={j} {...layer} />
              ))}
            </AbsoluteFill>
          </Sequence>
        );
      })}

      {/* 3) ナレーション音声 */}
      {spec.audio && <Audio src={spec.audio} />}
    </AbsoluteFill>
  );
};

/**
 * テロップ1層を描画。仕様は app.py:2147-2309 と一致させる:
 *   - size:  xl=140 / l=108 / m=80 / s=52  (px)
 *   - placement Y比: hook_top=0.20, mid=0.45, kick_bottom=0.72
 *   - style "double_stroke": 白塗り + 内側黒縁(font/12) + 外側白縁(font/28)
 *   - フェードイン: 最初の8フレーム
 *
 * px単位でtopを指定し AbsoluteFill 直下に置くことで、
 * 裏層MotionImageの transform: scale() の影響を受けない（pixel-fixed）。
 */
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export type CaptionPlacement = "hook_top" | "mid" | "kick_bottom" | "note_top" | "footer";
export type CaptionSize = "xl" | "l" | "m" | "s";
export type CaptionStyle = "double_stroke" | "bold" | "highlight";

export type CaptionLayerSpec = {
  text: string;
  placement: CaptionPlacement;
  size: CaptionSize;
  style: CaptionStyle;
  emphasis_words: string[];
};

const SIZE_MAP: Record<CaptionSize, number> = {
  xl: 140,
  l: 108,
  m: 80,
  s: 52,
};

const Y_RATIO_MAP: Record<CaptionPlacement, number> = {
  note_top: 0.08,
  hook_top: 0.20,
  mid: 0.45,
  kick_bottom: 0.72,
  footer: 0.85,
};

const buildDoubleStrokeShadow = (fontSize: number): string => {
  // 内側黒縁 (font/12) を 8方向 + 外側白縁 (font/28) を 8方向で重ねる
  const inner = Math.max(2, Math.round(fontSize / 12));
  const outer = Math.max(1, Math.round(fontSize / 28));
  const total = inner + outer;
  const dirs = [
    [-1, -1], [1, -1], [-1, 1], [1, 1],
    [0, -1], [0, 1], [-1, 0], [1, 0],
  ];
  // 内側黒
  const blackLayer = dirs
    .map(([dx, dy]) => `${dx * inner}px ${dy * inner}px 0 #000`)
    .join(", ");
  // 外側白（黒の外側）
  const whiteLayer = dirs
    .map(([dx, dy]) => `${dx * total}px ${dy * total}px 0 #fff`)
    .join(", ");
  return `${blackLayer}, ${whiteLayer}`;
};

const renderTextWithEmphasis = (text: string, emphasis: string[]): React.ReactNode => {
  if (!emphasis || emphasis.length === 0) return text;
  // 強調語を黄色塗りに置き換え
  const pattern = new RegExp(`(${emphasis.map(escapeRegex).join("|")})`, "g");
  const parts = text.split(pattern);
  return parts.map((part, i) =>
    emphasis.includes(part) ? (
      <span key={i} style={{ color: "rgb(255,230,0)" }}>{part}</span>
    ) : (
      <React.Fragment key={i}>{part}</React.Fragment>
    ),
  );
};

const escapeRegex = (s: string): string => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export const CaptionLayer: React.FC<CaptionLayerSpec> = ({
  text,
  placement,
  size,
  style,
  emphasis_words,
}) => {
  const frame = useCurrentFrame();
  const { height } = useVideoConfig();
  const opacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });

  const fontSize = SIZE_MAP[size] ?? SIZE_MAP.xl;
  const yPx = Math.round((Y_RATIO_MAP[placement] ?? 0.72) * height);

  const baseStyle: React.CSSProperties = {
    position: "absolute",
    top: yPx,
    left: 0,
    right: 0,
    textAlign: "center",
    fontFamily: '"Noto Sans JP", "Hiragino Sans", "Yu Gothic", sans-serif',
    fontWeight: 900,
    fontSize,
    lineHeight: 1.3,
    padding: "0 6%",
    opacity,
    color: "#fff",
  };

  const styleSpecific: React.CSSProperties =
    style === "highlight"
      ? {
          color: "rgb(30,20,0)",
          backgroundColor: "rgba(255,230,0,0.96)",
          padding: "12px 24px",
        }
      : style === "bold"
      ? {
          color: "#fff",
          textShadow: `0 0 ${Math.round(fontSize / 12)}px #000, ${Math.round(fontSize / 12)}px ${Math.round(fontSize / 12)}px 0 #000`,
        }
      : {
          // double_stroke (default)
          color: "#fff",
          textShadow: buildDoubleStrokeShadow(fontSize),
        };

  return (
    <div style={{ ...baseStyle, ...styleSpecific }}>
      {renderTextWithEmphasis(text, emphasis_words)}
    </div>
  );
};

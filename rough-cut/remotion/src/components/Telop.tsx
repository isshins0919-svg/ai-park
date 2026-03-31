/**
 * テロップコンポーネント (overlay 2層方式)
 *
 * おまかせくん MultiStrokeTelop のシンプル版。
 * overlay 方式: stroke層 (transparent + WebkitTextStroke) + fill層 (白文字)
 * で高品質な縁取りテロップを実現。
 */
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

// =============================================================================
// 型定義
// =============================================================================

type TelopAnimationIn = "stamp" | "popIn" | "fadeIn" | "none";
type TelopAnimationOut = "popOut" | "fadeOut" | "none";

interface VoiceWord {
  text: string;
  start: number;
  end: number;
}

interface TelopSegment {
  text: string;
  word_indices: number[];
}

interface TelopData {
  id: string;
  text: string;
  word_indices: number[];
  segments: TelopSegment[];
}

interface TelopProps {
  telops: TelopData[];
  words: VoiceWord[];
  cutStartFrame: number;
  fps: number;
  animationIn: TelopAnimationIn;
  animationOut: TelopAnimationOut;
  telopY?: number;
  fontSize?: number;
}

// =============================================================================
// スタイル定義 (BrandTemplate デフォルト準拠)
// =============================================================================

const TELOP_CONFIG = {
  fontFamily: '"Zen Kaku Gothic Antique", "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Meiryo", sans-serif',
  fontSize: 52,
  fontWeight: 900 as const,
  letterSpacing: "0.02em",
  lineHeight: 1.4,
  textColor: "#FFFFFF",
  // overlay 2層方式
  strokeWidth: 8,
  strokeColor: "#000000",
  // drop-shadow
  dropShadow: "drop-shadow(0px 4px 8px rgba(0,0,0,0.5))",
};

// =============================================================================
// アニメーション (Remotion spring ベース)
// =============================================================================

const OUT_DURATION = 6;

const getInAnim = (
  frame: number,
  startFrame: number,
  type: TelopAnimationIn,
  fps: number,
): { opacity: number; transform: string } => {
  const localFrame = frame - startFrame;
  if (type === "none" || localFrame < 0) return { opacity: 1, transform: "" };

  if (type === "stamp") {
    const progress = spring({ frame: localFrame, fps, config: { damping: 8, stiffness: 300 } });
    const scale = interpolate(progress, [0, 1], [2.5, 1]);
    return { opacity: Math.min(1, progress * 3), transform: `scale(${scale})` };
  }

  if (type === "popIn") {
    const progress = spring({ frame: localFrame, fps, config: { damping: 10, stiffness: 200 } });
    return { opacity: progress, transform: `scale(${interpolate(progress, [0, 1], [0, 1])})` };
  }

  if (type === "fadeIn") {
    const opacity = interpolate(localFrame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
    return { opacity, transform: "" };
  }

  return { opacity: 1, transform: "" };
};

const getOutAnim = (
  framesUntilEnd: number,
  type: TelopAnimationOut,
): { opacity: number; scale: number } => {
  if (type === "none") return { opacity: 1, scale: 1 };
  const progress = Math.min(1, framesUntilEnd / OUT_DURATION);

  if (type === "popOut") {
    const c1 = 1.70158;
    const c3 = c1 + 1;
    const eased = progress < 1 ? 1 + c3 * (progress - 1) ** 3 + c1 * (progress - 1) ** 2 : 1;
    return {
      opacity: interpolate(progress, [0, 0.3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
      scale: eased,
    };
  }

  if (type === "fadeOut") return { opacity: progress, scale: 1 };
  return { opacity: 1, scale: 1 };
};

// =============================================================================
// コンポーネント
// =============================================================================

export const Telop = ({
  telops,
  words,
  cutStartFrame,
  fps,
  animationIn,
  animationOut,
  telopY = 0.5,
  fontSize,
}: TelopProps) => {
  const frame = useCurrentFrame();
  const effectiveFontSize = fontSize ?? TELOP_CONFIG.fontSize;
  const strokeWidth = Math.round(TELOP_CONFIG.strokeWidth * (effectiveFontSize / 52));

  const rawTimings = telops
    .map((telop) => {
      const indices = telop.word_indices;
      if (indices.length === 0) return null;
      const firstIdx = Math.min(...indices);
      const lastIdx = Math.max(...indices);
      const startWord = words[firstIdx];
      const endWord = words[lastIdx];
      if (!startWord || !endWord) return null;
      return {
        telop,
        startFrame: Math.round(startWord.start * fps),
        endFrame: Math.round(endWord.end * fps),
        segments: telop.segments,
      };
    })
    .filter(Boolean) as Array<{
      telop: TelopData;
      startFrame: number;
      endFrame: number;
      segments: TelopSegment[];
    }>;

  // 半開区間 [start, end) で隙間チカチカ防止
  const telopTimings = rawTimings.map((t, i) => {
    const isLast = i === rawTimings.length - 1;
    const displayEnd = isLast ? t.endFrame : rawTimings[i + 1].startFrame;
    return { ...t, displayEnd };
  });

  // 共通テキストスタイル
  const textStyle: React.CSSProperties = {
    fontFamily: TELOP_CONFIG.fontFamily,
    fontSize: effectiveFontSize,
    fontWeight: TELOP_CONFIG.fontWeight,
    letterSpacing: TELOP_CONFIG.letterSpacing,
    lineHeight: TELOP_CONFIG.lineHeight,
    textAlign: "center",
    whiteSpace: "pre-wrap",
    wordBreak: "keep-all",
  };

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          top: `${telopY * 100}%`,
          left: 0,
          right: 0,
          transform: "translateY(-50%)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {telopTimings.map((timing) => {
          const { telop, startFrame, displayEnd, segments } = timing;
          const isLast = timing === telopTimings[telopTimings.length - 1];

          const isVisible = isLast
            ? frame >= startFrame && frame <= displayEnd
            : frame >= startFrame && frame < displayEnd;
          if (!isVisible) return null;

          // アニメーション
          const inAnim = getInAnim(frame, startFrame, animationIn, fps);
          const outAnim = getOutAnim(displayEnd - frame, animationOut);
          const opacity = inAnim.opacity * outAnim.opacity;
          const transform = `${inAnim.transform}${outAnim.scale !== 1 ? ` scale(${outAnim.scale})` : ""}`;

          return (
            <div
              key={telop.id}
              style={{
                opacity,
                transform,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 8,
                filter: TELOP_CONFIG.dropShadow,
              }}
            >
              {segments.map((segment, segIdx) => (
                <div
                  key={segIdx}
                  style={{ position: "relative", display: "inline-block" }}
                >
                  {/* Stroke層: transparent + WebkitTextStroke (縁取りのみ) */}
                  <div
                    style={{
                      ...textStyle,
                      color: "transparent",
                      WebkitTextStroke: `${strokeWidth}px ${TELOP_CONFIG.strokeColor}`,
                    }}
                  >
                    {segment.text}
                  </div>
                  {/* Fill層: 白文字 (最上層) */}
                  <div
                    style={{
                      ...textStyle,
                      color: TELOP_CONFIG.textColor,
                      position: "absolute",
                      inset: 0,
                    }}
                  >
                    {segment.text}
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

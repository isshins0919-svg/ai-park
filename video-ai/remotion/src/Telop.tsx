import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

type TelopProps = {
  text: string;
  emphasis: boolean;
};

export const Telop: React.FC<TelopProps> = ({ text, emphasis }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // フェードイン（最初の8フレーム）
  const opacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });

  // 強調テロップ: 黄色背景×黒文字 / 通常: 白縁取り文字
  const style: React.CSSProperties = emphasis
    ? {
        backgroundColor: "rgba(255, 215, 0, 0.92)",
        color: "#000",
        padding: "12px 28px",
        borderRadius: 8,
        fontSize: 72,
        fontWeight: 900,
        textAlign: "center",
        lineHeight: 1.4,
        maxWidth: "88%",
      }
    : {
        color: "#fff",
        fontSize: 60,
        fontWeight: 800,
        textAlign: "center",
        lineHeight: 1.5,
        maxWidth: "88%",
        textShadow:
          "-3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000, 3px 3px 0 #000, 0 3px 0 #000, 0 -3px 0 #000, 3px 0 0 #000, -3px 0 0 #000",
      };

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: "18%",
        opacity,
      }}
    >
      <div style={style}>{text}</div>
    </AbsoluteFill>
  );
};

import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { Telop } from "./Telop";

type SceneClipProps = {
  videoSrc: string;   // クリップのパス
  text: string;
  emphasis: boolean;
};

export const SceneClip: React.FC<SceneClipProps> = ({ videoSrc, text, emphasis }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* 動画クリップ（音声なし） */}
      <OffthreadVideo
        src={videoSrc}
        muted
        style={{ width: "100%", height: "100%", objectFit: "cover" }}
      />
      {/* テロップ（フェードイン付き） */}
      {text && <Telop text={text} emphasis={emphasis} />}
    </AbsoluteFill>
  );
};

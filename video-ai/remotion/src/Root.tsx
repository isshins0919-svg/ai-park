/**
 * Remotion Root — composition.json を読み込んで動画を構成する
 *
 * composition.json の構造:
 * {
 *   "fps": 30,
 *   "width": 1080,
 *   "height": 1920,
 *   "scenes": [
 *     { "clip": "/path/to/clip.mp4", "text": "テキスト", "emphasis": false, "durationFrames": 90 },
 *     ...
 *   ],
 *   "narration": "/path/to/narration.mp3"
 * }
 */
import { Composition, Series, Audio, AbsoluteFill } from "remotion";
import { SceneClip } from "./SceneClip";

// composition.json を読み込む（Remotionはimportで直接読める）
// 実際の実行時はPythonが生成したJSONをここに渡す
const COMP_PATH = process.env.COMPOSITION_JSON || "./composition.json";

type Scene = {
  clip: string;
  text: string;
  emphasis: boolean;
  durationFrames: number;
};

type CompositionSpec = {
  fps: number;
  width: number;
  height: number;
  scenes: Scene[];
  narration?: string;
};

// JSONを動的にロード（開発時はサンプルを使用）
const loadSpec = (): CompositionSpec => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    return require(COMP_PATH);
  } catch {
    return {
      fps: 30,
      width: 1080,
      height: 1920,
      scenes: [
        { clip: "", text: "サンプルテキスト", emphasis: false, durationFrames: 90 },
      ],
    };
  }
};

const spec = loadSpec();
const totalFrames = spec.scenes.reduce((sum, s) => sum + s.durationFrames, 0);

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="VideoAI"
      component={VideoComposition}
      durationInFrames={totalFrames}
      fps={spec.fps}
      width={spec.width}
      height={spec.height}
    />
  );
};

const VideoComposition: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <Series>
        {spec.scenes.map((scene, i) => (
          <Series.Sequence key={i} durationInFrames={scene.durationFrames}>
            <SceneClip
              videoSrc={scene.clip}
              text={scene.text}
              emphasis={scene.emphasis}
            />
          </Series.Sequence>
        ))}
      </Series>
      {spec.narration && (
        <Audio src={spec.narration} />
      )}
    </AbsoluteFill>
  );
};

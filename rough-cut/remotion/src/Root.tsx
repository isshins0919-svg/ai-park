import React from "react";
import { Composition, getInputProps, staticFile } from "remotion";
import { loadFont as loadZenKaku } from "@remotion/google-fonts/ZenKakuGothicAntique";
import { TalkEdit } from "./compositions/TalkEdit";

// フォントロード (weights を絞る: 全ロードはタイムアウトの原因)
loadZenKaku("normal", { weights: ["900"] });

interface InputProps {
  timeline?: {
    version: string;
    total_duration_ms: number;
    video_fit: string;
    fps: number;
    cuts: unknown[];
    [key: string]: unknown;
  };
  voice_data?: {
    version: string;
    cuts: unknown[];
  };
  meta?: Record<string, unknown>;
  width?: number;
  height?: number;
}

export const RemotionRoot: React.FC = () => {
  const inputProps = getInputProps() as InputProps;

  return (
    <>
      <Composition
        id="TalkEdit"
        component={TalkEdit as unknown as React.FC<Record<string, unknown>>}
        durationInFrames={900} // calculateMetadata で上書きされる
        fps={30}
        width={1280}
        height={720}
        defaultProps={{
          timeline: inputProps.timeline || {
            version: "1.0.0",
            total_duration_ms: 30000,
            video_fit: "cover",
            fps: 30,
            cuts: [],
          },
          voice_data: inputProps.voice_data || { version: "1.0", cuts: [] },
          meta: inputProps.meta || {},
        } as Record<string, unknown>}
        calculateMetadata={async ({ props }) => {
          // CLI render 時は getInputProps() で渡されるのでそのまま使う
          const ip = getInputProps() as InputProps;
          if (ip.timeline && ip.timeline.cuts && (ip.timeline.cuts as unknown[]).length > 0) {
            const meta = (ip.meta || {}) as Record<string, unknown>;
            const fps = ip.timeline.fps || 30;
            return {
              durationInFrames: Math.ceil((ip.timeline.total_duration_ms / 1000) * fps),
              fps,
              width: ip.width || (meta.display_width as number) || 1280,
              height: ip.height || (meta.display_height as number) || 720,
              props: {
                timeline: ip.timeline,
                voice_data: ip.voice_data || { version: "1.0", cuts: [] },
                meta: ip.meta || {},
              },
            };
          }

          // Studio 時: public/composition.json から読み込み
          try {
            const res = await fetch(staticFile("composition.json"));
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const meta = data.meta || {};
            const fps = data.timeline?.fps || 30;
            const totalMs = data.timeline?.total_duration_ms || 30000;
            return {
              durationInFrames: Math.ceil((totalMs / 1000) * fps),
              fps,
              width: (meta.display_width as number) || 1280,
              height: (meta.display_height as number) || 720,
              props: {
                timeline: data.timeline,
                voice_data: data.voice_data || { version: "1.0", cuts: [] },
                meta,
              },
            };
          } catch {
            // composition.json がない場合はデフォルト
            return {
              durationInFrames: 900,
              fps: 30,
              width: 1280,
              height: 720,
            };
          }
        }}
      />
    </>
  );
};

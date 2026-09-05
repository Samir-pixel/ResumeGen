"use client";

import { useEffect, useRef, useState } from "react";

const PAGE_WIDTH = 794;
const PAGE_HEIGHT = 1123;

export function ResumePreview({ src }: { src: string }) {
  const frameRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    const node = frameRef.current;
    if (!node) return;

    const observer = new ResizeObserver(([entry]) => {
      const width = entry.contentRect.width;
      if (width > 0) {
        setScale(width / PAGE_WIDTH);
      }
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={frameRef} className="w-full overflow-x-hidden bg-[#d7d7d3]">
      <div style={{ height: PAGE_HEIGHT * scale * 2, minHeight: PAGE_HEIGHT * scale }}>
        <iframe
          key={src}
          src={src}
          title="Предпросмотр резюме"
          className="border-0 bg-white"
          style={{
            width: PAGE_WIDTH,
            height: PAGE_HEIGHT * 2,
            transform: `scale(${scale})`,
            transformOrigin: "top left",
          }}
        />
      </div>
    </div>
  );
}

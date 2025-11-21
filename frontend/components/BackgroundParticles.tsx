"use client";

import { useEffect, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";

export default function BackgroundParticles() {
  const [init, setInit] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => setInit(true));
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      document.querySelectorAll("canvas").forEach((canvas) => {
        (canvas as HTMLElement).style.pointerEvents = "none";
      });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  if (!init) return null;

  return (
    <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none">
      <Particles
        id="tsparticles"
        className="w-full h-full pointer-events-none"
        options={{
          fullScreen: { enable: false },
          background: { color: { value: "#ffffff" } },
          fpsLimit: 60,
          interactivity: {
            events: {
              onHover: { enable: false },
              onClick: { enable: false },
            },
          },
          particles: {
            color: { value: "#3b82f6" },
            links: {
              color: "#60a5fa",
              distance: 150,
              enable: true,
              opacity: 0.3,
              width: 1,
            },
            move: { enable: true, speed: 1.5, outModes: { default: "bounce" } },
            number: {
              density: { enable: true },
              value: 250,
            },
            opacity: { value: 0.4 },
            shape: { type: "circle" },
            size: { value: { min: 1, max: 3 } },
          },
          detectRetina: true,
        }}
      />
    </div>
  );
}

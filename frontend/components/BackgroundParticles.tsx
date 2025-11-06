"use client";
import { useCallback, useEffect, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";

export default function BackgroundParticles() {
  const [init, setInit] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => setInit(true));
  }, []);

  if (!init) return null;

  return (
    <Particles
      id="tsparticles"
      className="fixed top-0 left-0 w-full h-full -z-10"
      options={{
        fullScreen: { enable: true, zIndex: -1 },
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
            value: 300,
          },
          opacity: { value: 0.4 },
          shape: { type: "circle" },
          size: { value: { min: 1, max: 3 } },
        },
        detectRetina: true,
      }}
    />
  );
}
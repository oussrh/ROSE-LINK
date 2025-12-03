"use client";

import { useEffect, useState } from "react";
import { VERSION, GITHUB_VERSION_URL } from "@/lib/version";

export default function VersionBadge() {
  const [version, setVersion] = useState<string>(VERSION);

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await fetch(GITHUB_VERSION_URL);
        if (response.ok) {
          const text = await response.text();
          setVersion(text.trim());
        }
      } catch {
        // Use fallback VERSION from lib/version.ts
      }
    };

    fetchVersion();
  }, []);

  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-dark-800 text-dark-400">
      v{version}
    </span>
  );
}

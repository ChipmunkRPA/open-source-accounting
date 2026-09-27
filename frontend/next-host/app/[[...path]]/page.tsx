'use client';
import {useEffect, useRef} from 'react';
export default function AppHost() {
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let disposed = false;
    let cleanup: undefined | (() => void);
    import('../../../src/main').then(async ({mount}) => {
      if (disposed || !root.current) return;
      const result = await mount(root.current);
      if (disposed) result?.(); else cleanup = result;
    });
    return () => { disposed = true; cleanup?.(); };
  }, []);
  return <div id="app" ref={root}><p className="boot">Loading Open Source Accounting…</p></div>;
}

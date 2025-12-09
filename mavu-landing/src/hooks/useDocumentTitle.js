import { useEffect } from 'react';

export function useDocumentTitle(title) {
  useEffect(() => {
    const prevTitle = document.title;
    document.title = title ? `${title} | MAVU AI` : 'MAVU AI — Цифровой друг для вашего ребёнка';

    return () => {
      document.title = prevTitle;
    };
  }, [title]);
}

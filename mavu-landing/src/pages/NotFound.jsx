import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

export default function NotFound() {
  const { t } = useTranslation();
  useDocumentTitle('404 — ' + t('notFound.subtitle'));

  return (
    <section className="py-16 md:py-24 min-h-[80vh] flex items-center">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-2xl text-center">
        {/* 404 Animation */}
        <div className="relative mb-6 sm:mb-8">
          <h1 className="text-[100px] sm:text-[150px] md:text-[200px] font-bold text-gradient opacity-20 leading-none select-none">
            {t('notFound.title')}
          </h1>

          {/* Floating MAVU character */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-24 h-24 sm:w-28 md:w-32 sm:h-28 md:h-32 rounded-full bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center animate-float shadow-2xl shadow-violet-500/30">
              <span className="text-4xl sm:text-4xl md:text-5xl font-bold text-white">M</span>
            </div>
          </div>

          {/* Stars around */}
          <div className="absolute top-6 sm:top-10 left-1/4 w-2 sm:w-3 h-2 sm:h-3 bg-violet-400 rounded-full animate-twinkle" />
          <div className="absolute top-1/3 right-1/4 w-1.5 sm:w-2 h-1.5 sm:h-2 bg-pink-400 rounded-full animate-twinkle animation-delay-1000" />
          <div className="absolute bottom-6 sm:bottom-10 left-1/3 w-1.5 sm:w-2 h-1.5 sm:h-2 bg-emerald-400 rounded-full animate-twinkle animation-delay-2000" />
        </div>

        {/* Text */}
        <h2 className="text-xl sm:text-2xl md:text-3xl font-bold text-white mb-3 md:mb-4">
          {t('notFound.subtitle')}
        </h2>
        <p className="text-sm sm:text-base text-gray-400 mb-6 sm:mb-8 max-w-md mx-auto px-2">
          {t('notFound.description')}
        </p>

        {/* CTA */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-gradient-to-r from-violet-600 to-pink-600 text-white text-sm sm:text-base font-semibold hover:opacity-90 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/30 hover:scale-105"
        >
          <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          {t('notFound.backHome')}
        </Link>
      </div>
    </section>
  );
}

import { useState } from 'react';
import { Link, useLocation, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

export default function Success() {
  const { t } = useTranslation();
  const location = useLocation();
  const [copied, setCopied] = useState(false);
  useDocumentTitle(t('success.title'));

  const promoCode = location.state?.promoCode;

  // Redirect if no promo code (user accessed directly)
  if (!promoCode) {
    return <Navigate to="/" replace />;
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(promoCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <section className="py-16 md:py-24 min-h-[80vh] flex items-center">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-lg text-center">
        {/* Success Icon */}
        <div className="w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-6 sm:mb-8 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center animate-bounce-once">
          <svg className="w-10 h-10 sm:w-12 sm:h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        {/* Title */}
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-2">
          {t('success.title')}
        </h1>
        <p className="text-sm sm:text-base text-gray-400 mb-6 sm:mb-8">{t('success.subtitle')}</p>

        {/* Promo Code Card */}
        <div className="glass-strong rounded-xl sm:rounded-2xl p-4 sm:p-6 mb-6 sm:mb-8">
          <p className="text-gray-400 text-xs sm:text-sm mb-2 sm:mb-3">{t('success.promoLabel')}</p>
          <div className="flex items-center justify-center gap-2 sm:gap-3">
            <code className="text-xl sm:text-2xl md:text-3xl font-bold text-gradient tracking-wider">
              {promoCode}
            </code>
            <button
              onClick={handleCopy}
              className="p-2 rounded-lg glass hover:bg-white/10 transition-colors group"
              title={copied ? t('success.copied') : t('success.copy')}
            >
              {copied ? (
                <svg className="w-4 h-4 sm:w-5 sm:h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
              )}
            </button>
          </div>
          {copied && (
            <p className="text-emerald-400 text-xs sm:text-sm mt-2 animate-fade-in">
              {t('success.copied')}
            </p>
          )}
        </div>

        {/* Instructions */}
        <div className="glass rounded-xl sm:rounded-2xl p-4 sm:p-6 mb-6 sm:mb-8 text-left">
          <h3 className="text-sm sm:text-base text-white font-semibold mb-3 sm:mb-4">{t('success.instructions.title')}</h3>
          <ol className="space-y-2 sm:space-y-3">
            <li className="flex items-start gap-2 sm:gap-3">
              <span className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0 text-violet-400 text-xs sm:text-sm font-medium">
                1
              </span>
              <span className="text-xs sm:text-sm text-gray-300">{t('success.instructions.step1')}</span>
            </li>
            <li className="flex items-start gap-2 sm:gap-3">
              <span className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0 text-violet-400 text-xs sm:text-sm font-medium">
                2
              </span>
              <span className="text-xs sm:text-sm text-gray-300">{t('success.instructions.step2')}</span>
            </li>
            <li className="flex items-start gap-2 sm:gap-3">
              <span className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0 text-violet-400 text-xs sm:text-sm font-medium">
                3
              </span>
              <span className="text-xs sm:text-sm text-gray-300">{t('success.instructions.step3')}</span>
            </li>
          </ol>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
          <a
            href="#"
            className="px-6 sm:px-8 py-3 sm:py-4 rounded-full bg-gradient-to-r from-violet-600 to-pink-600 text-white text-sm sm:text-base font-semibold hover:opacity-90 transition-all duration-300 hover:shadow-lg hover:shadow-violet-500/30"
          >
            {t('success.download')}
          </a>
          <Link
            to="/"
            className="px-6 sm:px-8 py-3 sm:py-4 rounded-full glass text-white text-sm sm:text-base font-semibold hover:bg-white/10 transition-all duration-300"
          >
            {t('success.backHome')}
          </Link>
        </div>
      </div>
    </section>
  );
}

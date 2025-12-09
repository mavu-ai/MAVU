import { useTranslation } from 'react-i18next';
import { useDocumentTitle } from '../hooks/useDocumentTitle';

export default function Privacy() {
  const { t } = useTranslation();
  useDocumentTitle(t('privacy.title'));

  const sections = ['collect', 'use', 'protect', 'share', 'rights', 'contact'];

  return (
    <section className="py-16 md:py-24">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8 md:mb-12">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-3 md:mb-4">
            {t('privacy.title')}
          </h1>
          <p className="text-sm sm:text-base text-gray-400">
            {t('privacy.lastUpdate')} 01.12.2024
          </p>
        </div>

        {/* Intro */}
        <div className="glass-strong rounded-xl sm:rounded-2xl p-4 sm:p-6 mb-6 md:mb-8">
          <p className="text-sm sm:text-base text-gray-300">{t('privacy.intro')}</p>
        </div>

        {/* Sections */}
        <div className="space-y-4 md:space-y-6">
          {sections.map((section) => (
            <div key={section} className="glass rounded-xl sm:rounded-2xl p-4 sm:p-6 hover:bg-white/5 transition-colors">
              <h2 className="text-lg sm:text-xl font-semibold text-white mb-3 md:mb-4">
                {t(`privacy.sections.${section}.title`)}
              </h2>
              <div className="text-sm sm:text-base text-gray-400 whitespace-pre-line">
                {t(`privacy.sections.${section}.content`)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
